from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.core.tenant import get_current_user
from app.models.user import User
from app.services.importer import GeometryImporter
from app.config import settings
import os, uuid, numpy as np
router = APIRouter()
ALLOWED_EXTENSIONS = ['.stl', '.obj', '.step', '.stp', '.iges', '.igs', '.dxf']
@router.post("/upload")
async def upload_geometry(file=File(...), user=Depends(get_current_user)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS: raise HTTPException(400, f"Formato nao suportado: {ext}")
    file_id = str(uuid.uuid4())
    filepath = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")
    with open(filepath, 'wb') as f:
        while chunk := await file.read(1024*1024): f.write(chunk)
    info = GeometryImporter.get_file_info(filepath)
    return {"file_id": file_id, "filename": file.filename, "filepath": filepath, "format": info["format"], "dimension": info["dimension"], "info": info.get("info", {})}
@router.post("/voxelize")
async def voxelize_geometry(body, user=Depends(get_current_user)):
    filepath = body["filepath"]
    grid_x = body.get("grid_x", 64)
    grid_y = body.get("grid_y", 64)
    grid_z = body.get("grid_z", 64)
    dimension = body.get("dimension", "3D")
    max_dim = max(grid_x, grid_y, grid_z)
    if max_dim > user.grid_limit: raise HTTPException(403, f"Grade excede limite {user.grid_limit}")
    grid = GeometryImporter.voxelize(filepath, grid_x, grid_y, grid_z, dimension=dimension)
    grid_id = str(uuid.uuid4())
    grid_path = os.path.join(settings.UPLOAD_DIR, f"grid_{grid_id}.npy")
    np.save(grid_path, grid)
    return {"grid_id": grid_id, "grid_path": grid_path, "grid_shape": list(grid.shape), "solid_cells": int(grid.sum()), "fluid_cells": grid.size - int(grid.sum())}
