from fastapi import APIRouter, Depends, HTTPException
from app.core.tenant import get_current_user
from app.models.user import User
from app.config import settings
import numpy as np, os, uuid
router = APIRouter()
def make_cylinder_2d(nx, ny, radius=0.15, cx=0.3, cy=0.5):
    grid = np.zeros((nx, ny), dtype=bool)
    for i in range(nx):
        for j in range(ny):
            x, y = i/nx, j/ny
            if (x-cx)**2 + (y-cy)**2 < radius**2: grid[i, j] = True
    return grid
def make_channel_2d(nx, ny):
    grid = np.zeros((nx, ny), dtype=bool); grid[:, 0:3] = True; grid[:, -3:] = True; return grid
def make_lid_cavity_2d(nx, ny):
    grid = np.zeros((nx, ny), dtype=bool); grid[0, :] = True; grid[-1, :] = True; grid[:, 0] = True; return grid
def make_backward_step_2d(nx, ny, step_ratio=0.4):
    grid = np.zeros((nx, ny), dtype=bool); step_y = int(ny * step_ratio)
    grid[0:int(nx*0.3), 0:step_y] = True; grid[:, 0] = True; return grid
def make_sphere_3d(nx, ny, nz, radius=0.2, cx=0.3, cy=0.5, cz=0.5):
    grid = np.zeros((nx, ny, nz), dtype=bool)
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                x, y, z = i/nx, j/ny, k/nz
                if (x-cx)**2 + (y-cy)**2 + (z-cz)**2 < radius**2: grid[i, j, k] = True
    return grid
def make_duct_3d(nx, ny, nz):
    grid = np.zeros((nx, ny, nz), dtype=bool)
    grid[:, 0, :] = True; grid[:, -1, :] = True; grid[:, :, 0] = True; grid[:, :, -1] = True; return grid
def make_tube_3d(nx, ny, nz, radius=0.35):
    grid = np.zeros((nx, ny, nz), dtype=bool); cy, cz = ny/2, nz/2
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                if (j-cy)**2 + (k-cz)**2 > (radius*min(ny,nz))**2: grid[i, j, k] = True
    return grid
PRESETS = {
    "cylinder-flow": {"name": "Escoamento sobre Cilindro", "dimension": "2D", "generator": make_cylinder_2d,
        "config": {"viscosity": 0.02, "inlet_velocity": 0.1, "turbulence_model": "none",
            "boundary_conditions": [{"face": "west", "type": "velocity", "params": {"ux": 0.1, "uy": 0}},
                {"face": "east", "type": "outflow"}, {"face": "south", "type": "wall"}, {"face": "north", "type": "wall"}]}},
    "channel-flow": {"name": "Canal Plano 2D", "dimension": "2D", "generator": make_channel_2d,
        "config": {"viscosity": 0.05, "inlet_velocity": 0.08, "turbulence_model": "none"}},
    "lid-cavity": {"name": "Cavidade com Tampa", "dimension": "2D", "generator": make_lid_cavity_2d,
        "config": {"viscosity": 0.02, "inlet_velocity": 0.0, "turbulence_model": "none",
            "boundary_conditions": [{"face": "west", "type": "wall"}, {"face": "east", "type": "wall"},
                {"face": "south", "type": "wall"}, {"face": "north", "type": "velocity", "params": {"ux": 0.1, "uy": 0}}]}},
    "backward-step": {"name": "Degrau Atras", "dimension": "2D", "generator": make_backward_step_2d,
        "config": {"viscosity": 0.01, "inlet_velocity": 0.15, "turbulence_model": "les"}},
    "sphere-3d": {"name": "Esfera em 3D", "dimension": "3D", "generator": make_sphere_3d,
        "config": {"viscosity": 0.02, "inlet_velocity": 0.1, "turbulence_model": "les"}},
    "3d-duct": {"name": "Duto Retangular 3D", "dimension": "3D", "generator": make_duct_3d,
        "config": {"viscosity": 0.03, "inlet_velocity": 0.08, "turbulence_model": "les"}},
    "heat-tube": {"name": "Tubo com Troca Termica", "dimension": "3D", "generator": make_tube_3d,
        "config": {"viscosity": 0.02, "inlet_velocity": 0.1, "turbulence_model": "les",
            "enable_thermal": True, "thermal_diffusivity": 0.05, "T_inlet": 1.0, "T_wall": 0.0}},
}
@router.get("/")
async def list_geometries(user=Depends(get_current_user)):
    return [{"id": gid, "name": g["name"], "dimension": g["dimension"]} for gid, g in PRESETS.items()]
@router.post("/{geo_id}/generate")
async def generate_geometry(geo_id, body, user=Depends(get_current_user)):
    if geo_id not in PRESETS: raise HTTPException(404, "Geometria nao encontrada")
    preset = PRESETS[geo_id]; grid_size = body.get("grid_size", 64)
    if grid_size > user.grid_limit: raise HTTPException(403, f"Grade {grid_size} excede limite {user.grid_limit}")
    if preset["dimension"] == "2D": grid = preset["generator"](grid_size, grid_size)
    else: grid = preset["generator"](grid_size, grid_size, grid_size)
    grid_id = str(uuid.uuid4()); grid_path = os.path.join(settings.UPLOAD_DIR, f"preset_{grid_id}.npy")
    np.save(grid_path, grid)
    return {"grid_id": grid_id, "grid_path": grid_path, "grid_shape": list(grid.shape),
        "solid_cells": int(grid.sum()), "fluid_cells": grid.size - int(grid.sum()),
        "dimension": preset["dimension"], "preset_config": preset["config"]}
