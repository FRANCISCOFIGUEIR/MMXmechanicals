import asyncio, numpy as np, os, json, logging
from celery import Celery
from datetime import datetime
from sqlalchemy import select
from app.config import settings
from app.database import AsyncSessionLocal
from app.models.simulation import Simulation, SimulationStatus
from app.models.project import Project
from app.services.solver.lbm import LBMSolver, SolverConfig
from app.services.solver.boundary import BoundaryCondition
logger = logging.getLogger(__name__)
celery_app = Celery("mmx", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.update(task_serializer="json", accept_content=["json"], result_serializer="json",
    timezone="America/Sao_Paulo", enable_utc=True, task_track_started=True, task_time_limit=3600,
    worker_prefetch_multiplier=1, worker_concurrency=1)
@celery_app.task(name="run_simulation", bind=True)
def run_simulation_task(self, simulation_id, config):
    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Simulation).where(Simulation.id == simulation_id))
            sim = result.scalar_one_or_none()
            if not sim: return {"error": "not found"}
            sim.status = SimulationStatus.RUNNING; sim.started_at = datetime.utcnow(); await db.commit()
            try:
                solid_mask = None
                grid_path = config.get("grid_path")
                if grid_path and os.path.exists(grid_path): solid_mask = np.load(grid_path)
                solver_config = SolverConfig(nx=sim.grid_size_x, ny=sim.grid_size_y, nz=sim.grid_size_z,
                    nu=sim.viscosity, rho0=sim.density, ux_inlet=sim.inlet_velocity,
                    enable_thermal=config.get("enable_thermal", False), max_iters=sim.max_iterations,
                    convergence=sim.convergence_criterion, save_interval=sim.save_interval,
                    turbulence_model=sim.turbulence_model, solid_mask=solid_mask)
                bcs = []
                for bc_def in sim.boundary_conditions:
                    bcs.append(BoundaryCondition(face=bc_def["face"], bc_type=bc_def["type"], **bc_def.get("params", {})))
                solver_config.boundary_conditions = bcs
                solver = LBMSolver(solver_config); results = solver.run()
                vtk_path = os.path.join(settings.RESULTS_DIR, f"sim_{simulation_id}.vtk")
                solver.export_vtk(vtk_path)
                results_path = os.path.join(settings.RESULTS_DIR, f"sim_{simulation_id}.json")
                with open(results_path, 'w') as f: json.dump(results, f, indent=2, default=str)
                sim.status = SimulationStatus.COMPLETED; sim.progress = 1.0
                sim.iterations_completed = results["total_iterations"]; sim.results_path = results_path
                sim.results_summary = {"converged": results["converged"], "total_iterations": results["total_iterations"],
                    "compute_time": results["compute_time"], "grid_size": results["grid_size"], "gpu_used": results["gpu_used"]}
                sim.gpu_used = results["gpu_used"]; sim.compute_time_seconds = results["compute_time"]
                sim.completed_at = datetime.utcnow(); await db.commit()
                return {"simulation_id": simulation_id, "status": "completed"}
            except Exception as e:
                sim.status = SimulationStatus.FAILED; sim.error_message = str(e); await db.commit()
                return {"error": str(e)}
    return asyncio.run(_run())
