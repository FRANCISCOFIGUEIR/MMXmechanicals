from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.tenant import get_current_user, check_simulation_limit
from app.models.user import User
from app.models.simulation import Simulation, SimulationStatus
from app.models.project import Project
from app.services.solver.lbm import LBMSolver, SolverConfig
from app.services.solver.boundary import BoundaryCondition
from app.config import settings
import numpy as np, os, uuid, json, logging
from datetime import datetime
router = APIRouter()
logger = logging.getLogger(__name__)
@router.post("/")
async def create_simulation(body, user=Depends(check_simulation_limit), db=Depends(get_db)):
    project_id = body["project_id"]
    name = body.get("name", f"Sim_{uuid.uuid4().hex[:8]}")
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    project = result.scalar_one_or_none()
    if not project: raise HTTPException(404, "Projeto nao encontrado")
    grid_x = body.get("grid_x", 64); grid_y = body.get("grid_y", 64); grid_z = body.get("grid_z", 64)
    max_dim = max(grid_x, grid_y, grid_z)
    if max_dim > user.grid_limit: raise HTTPException(403, f"Grade {max_dim} excede limite {user.grid_limit}")
    sim = Simulation(name=name, project_id=project_id, solver_type=body.get("solver_type","lbm_d3q19"),
        grid_size_x=grid_x, grid_size_y=grid_y, grid_size_z=grid_z,
        viscosity=body.get("viscosity",0.02), density=body.get("density",1.0),
        inlet_velocity=body.get("inlet_velocity",0.1), outlet_pressure=body.get("outlet_pressure",0.0),
        temperature_inlet=body.get("temperature_inlet",20.0), thermal_conductivity=body.get("thermal_conductivity",0.026),
        specific_heat=body.get("specific_heat",1005.0), max_iterations=body.get("max_iterations",10000),
        convergence_criterion=body.get("convergence",1e-6), save_interval=body.get("save_interval",100),
        boundary_conditions=body.get("boundary_conditions",[]), turbulence_model=body.get("turbulence_model","les"),
        status=SimulationStatus.PENDING)
    db.add(sim); user.simulations_used += 1; await db.commit(); await db.refresh(sim)
    if body.get("async", True):
        sim.status = SimulationStatus.QUEUED; await db.commit()
        return {"simulation_id": sim.id, "status": "queued"}
    return await _run_simulation(sim, project, body, db)
@router.get("/{sim_id}")
async def get_simulation(sim_id, user=Depends(get_current_user), db=Depends(get_db)):
    result = await db.execute(select(Simulation).join(Project).where(Simulation.id == sim_id, Project.user_id == user.id))
    sim = result.scalar_one_or_none()
    if not sim: raise HTTPException(404, "Simulacao nao encontrada")
    return {"id": sim.id, "name": sim.name, "status": sim.status.value, "progress": sim.progress,
        "iterations_completed": sim.iterations_completed, "grid_size": f"{sim.grid_size_x}x{sim.grid_size_y}x{sim.grid_size_z}",
        "solver_type": sim.solver_type, "viscosity": sim.viscosity, "density": sim.density,
        "inlet_velocity": sim.inlet_velocity, "turbulence_model": sim.turbulence_model,
        "max_iterations": sim.max_iterations, "error_message": sim.error_message,
        "results_summary": sim.results_summary, "gpu_used": sim.gpu_used,
        "compute_time_seconds": sim.compute_time_seconds}
@router.get("/{sim_id}/results")
async def get_results(sim_id, user=Depends(get_current_user), db=Depends(get_db)):
    result = await db.execute(select(Simulation).join(Project).where(Simulation.id == sim_id, Project.user_id == user.id))
    sim = result.scalar_one_or_none()
    if not sim: raise HTTPException(404, "Simulacao nao encontrada")
    if sim.status != SimulationStatus.COMPLETED: raise HTTPException(400, "Simulacao nao concluida")
    if sim.results_path and os.path.exists(sim.results_path):
        with open(sim.results_path, 'r') as f: return json.load(f)
    return sim.results_summary
async def _run_simulation(sim, project, config, db):
    sim.status = SimulationStatus.RUNNING; sim.started_at = datetime.utcnow()
    solid_mask = None
    grid_path = config.get("grid_path")
    if grid_path and os.path.exists(grid_path): solid_mask = np.load(grid_path)
    solver_config = SolverConfig(nx=sim.grid_size_x, ny=sim.grid_size_y, nz=sim.grid_size_z,
        nu=sim.viscosity, rho0=sim.density, ux_inlet=sim.inlet_velocity, rho_outlet=1.0,
        enable_thermal=config.get("enable_thermal", False), thermal_diffusivity=config.get("thermal_diffusivity",0.05),
        T_inlet=config.get("T_inlet",1.0), T_wall=config.get("T_wall",0.0),
        max_iters=sim.max_iterations, convergence=sim.convergence_criterion,
        save_interval=sim.save_interval, turbulence_model=sim.turbulence_model, solid_mask=solid_mask)
    bcs = []
    for bc_def in sim.boundary_conditions:
        bcs.append(BoundaryCondition(face=bc_def["face"], bc_type=bc_def["type"], **bc_def.get("params", {})))
    solver_config.boundary_conditions = bcs
    solver = LBMSolver(solver_config)
    results = solver.run()
    vtk_path = os.path.join(settings.RESULTS_DIR, f"sim_{sim.id}.vtk")
    solver.export_vtk(vtk_path)
    results_path = os.path.join(settings.RESULTS_DIR, f"sim_{sim.id}.json")
    with open(results_path, 'w') as f: json.dump(results, f, indent=2, default=str)
    sim.status = SimulationStatus.COMPLETED; sim.progress = 1.0
    sim.iterations_completed = results["total_iterations"]
    sim.results_path = results_path
    sim.results_summary = {"converged": results["converged"], "total_iterations": results["total_iterations"],
        "compute_time": results["compute_time"], "grid_size": results["grid_size"], "gpu_used": results["gpu_used"]}
    sim.gpu_used = results["gpu_used"]; sim.compute_time_seconds = results["compute_time"]
    sim.completed_at = datetime.utcnow(); await db.commit()
    return {"simulation_id": sim.id, "status": "completed", "results": sim.results_summary}
