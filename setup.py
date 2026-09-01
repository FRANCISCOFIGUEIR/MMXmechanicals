#!/usr/bin/env python3
"""MMX Mechanics - Auto-criador de todos os arquivos do projeto"""
import os

files = {}

# ==================== BACKEND ====================

files["backend/app/__init__.py"] = "# MMX Mechanics"
files["backend/app/config.py"] = '''import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
load_dotenv()
class Settings(BaseSettings):
    APP_NAME: str = "MMX Mechanics"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://mmx:mmx@localhost:5432/mmx")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    USE_GPU: bool = os.getenv("USE_GPU", "True") == "True"
    GPU_DEVICE_ID: int = int(os.getenv("GPU_DEVICE_ID", "0"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/app/uploads")
    RESULTS_DIR: str = os.getenv("RESULTS_DIR", "/app/results")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "200"))
    DEFAULT_LANG: str = os.getenv("DEFAULT_LANG", "pt-BR")
    FREE_SIMULATION_LIMIT: int = int(os.getenv("FREE_SIMULATION_LIMIT", "5"))
    PRO_SIMULATION_LIMIT: int = int(os.getenv("PRO_SIMULATION_LIMIT", "100"))
    MAX_GRID_FREE: int = 128
    MAX_GRID_PRO: int = 512
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173", "https://mmx.figsmor.com.br"]
    class Config:
        env_file = ".env"
settings = Settings()
'''

files["backend/app/database.py"] = '''from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, pool_size=20, max_overflow=10, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
class Base(DeclarativeBase):
    pass
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
'''

files["backend/app/main.py"] = '''from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn, os
from app.config import settings
from app.database import engine, Base
from app.routers import auth, projects, simulations, files, geometries
from app.services.i18n.translator import TranslationService
@asynccontextmanager
async def lifespan(app):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.RESULTS_DIR, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.i18n = TranslationService(settings.DEFAULT_LANG)
    yield
    await engine.dispose()
app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan, docs_url="/api/docs", redoc_url="/api/redoc")
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/results", StaticFiles(directory=settings.RESULTS_DIR), name="results")
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(simulations.router, prefix="/api/simulations", tags=["simulations"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(geometries.router, prefix="/api/geometries", tags=["geometries"])
@app.get("/api/health")
async def health():
    return {"status": "online", "app": settings.APP_NAME, "version": settings.APP_VERSION, "gpu": settings.USE_GPU}
@app.get("/api/i18n/{lang}")
async def get_translations(lang, request):
    return request.app.state.i18n.get_all_translations(lang)
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
'''

files["backend/app/models/__init__.py"] = "# MMX"
files["backend/app/models/user.py"] = '''from sqlalchemy import Column, String, Boolean, DateTime, Enum, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid, enum
class PlanType(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    plan = Column(Enum(PlanType), default=PlanType.FREE, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    simulations_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    @property
    def grid_limit(self):
        return {"free": 128, "pro": 512, "enterprise": 1024}.get(self.plan.value, 128)
    @property
    def sim_limit(self):
        return {"free": 5, "pro": 100, "enterprise": 999999}.get(self.plan.value, 5)
'''

files["backend/app/models/project.py"] = '''from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid
class Project(Base):
    __tablename__ = "projects"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    geometry_file = Column(String(500), nullable=True)
    geometry_type = Column(String(50), nullable=True)
    mesh_config = Column(JSON, default=dict)
    physics_config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="projects")
    simulations = relationship("Simulation", back_populates="project", cascade="all, delete-orphan")
'''

files["backend/app/models/simulation.py"] = '''from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON, Enum, Integer, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum, uuid
class SimulationStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
class Simulation(Base):
    __tablename__ = "simulations"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    solver_type = Column(String(50), default="lbm_d3q19")
    grid_size_x = Column(Integer, nullable=False)
    grid_size_y = Column(Integer, nullable=False)
    grid_size_z = Column(Integer, nullable=False)
    viscosity = Column(Float, default=0.01)
    density = Column(Float, default=1.0)
    inlet_velocity = Column(Float, default=1.0)
    outlet_pressure = Column(Float, default=0.0)
    temperature_inlet = Column(Float, default=20.0)
    thermal_conductivity = Column(Float, default=0.026)
    specific_heat = Column(Float, default=1005.0)
    max_iterations = Column(Integer, default=10000)
    convergence_criterion = Column(Float, default=1e-6)
    save_interval = Column(Integer, default=100)
    boundary_conditions = Column(JSON, default=list)
    turbulence_model = Column(String(50), default="les")
    status = Column(Enum(SimulationStatus), default=SimulationStatus.PENDING)
    progress = Column(Float, default=0.0)
    iterations_completed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    results_path = Column(String(500), nullable=True)
    results_summary = Column(JSON, default=dict)
    gpu_used = Column(Boolean, default=False)
    compute_time_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    project = relationship("Project", back_populates="simulations")
'''

files["backend/app/core/__init__.py"] = "# MMX"
files["backend/app/core/security.py"] = '''from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(password): return pwd_context.hash(password)
def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)
def create_access_token(subject, extra=None):
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire, "type": "access"}
    if extra: payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
def create_refresh_token(subject):
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
def decode_token(token):
    try: return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError: return {}
'''

files["backend/app/core/tenant.py"] = '''from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.core.security import decode_token
security = HTTPBearer()
async def get_current_user(credentials=Depends(security), db=Depends(get_db)):
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido ou expirado")
    result = await db.execute(select(User).where(User.id == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario inativo ou nao encontrado")
    return user
async def check_simulation_limit(user=Depends(get_current_user)):
    if user.simulations_used >= user.sim_limit:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Limite de simulacoes do plano atingido")
    return user
'''

files["backend/app/routers/__init__.py"] = "# MMX"
files["backend/app/routers/auth.py"] = '''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.models.user import User, PlanType
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.tenant import get_current_user
router = APIRouter()
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company: str | None = None
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req, db=Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none(): raise HTTPException(400, "Email ja cadastrado")
    user = User(email=req.email, full_name=req.full_name, company=req.company, hashed_password=hash_password(req.password), plan=PlanType.FREE)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id, {"email": user.email, "plan": user.plan.value}), refresh_token=create_refresh_token(user.id))
@router.post("/login", response_model=TokenResponse)
async def login(req, db=Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password): raise HTTPException(401, "Email ou senha invalidos")
    if not user.is_active: raise HTTPException(403, "Conta desativada")
    return TokenResponse(access_token=create_access_token(user.id, {"email": user.email, "plan": user.plan.value}), refresh_token=create_refresh_token(user.id))
@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "company": user.company, "plan": user.plan.value, "simulations_used": user.simulations_used, "sim_limit": user.sim_limit, "grid_limit": user.grid_limit}
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body, db=Depends(get_db)):
    refresh = body.get("token") or body.get("refresh_token")
    if not refresh: raise HTTPException(400, "Refresh token ausente")
    payload = decode_token(refresh)
    if not payload or payload.get("type") != "refresh": raise HTTPException(401, "Refresh token invalido")
    result = await db.execute(select(User).where(User.id == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user or not user.is_active: raise HTTPException(401, "Usuario nao encontrado")
    return TokenResponse(access_token=create_access_token(user.id, {"email": user.email, "plan": user.plan.value}), refresh_token=create_refresh_token(user.id))
'''

files["backend/app/routers/projects.py"] = '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database import get_db
from app.core.tenant import get_current_user
from app.models.user import User
from app.models.project import Project
import uuid
router = APIRouter()
class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
@router.get("/")
async def list_projects(user=Depends(get_current_user), db=Depends(get_db)):
    result = await db.execute(select(Project).where(Project.user_id == user.id))
    return [{"id": p.id, "name": p.name, "description": p.description} for p in result.scalars().all()]
@router.post("/")
async def create_project(req, user=Depends(get_current_user), db=Depends(get_db)):
    project = Project(id=str(uuid.uuid4()), name=req.name, description=req.description, user_id=user.id)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return {"id": project.id, "name": project.name}
@router.get("/{project_id}")
async def get_project(project_id, user=Depends(get_current_user), db=Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    project = result.scalar_one_or_none()
    if not project: raise HTTPException(404, "Projeto nao encontrado")
    return {"id": project.id, "name": project.name, "description": project.description}
'''

files["backend/app/routers/files.py"] = '''from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
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
'''

# ==================== BACKEND ROUTERS REST ====================

files["backend/app/routers/simulations.py"] = '''from fastapi import APIRouter, Depends, HTTPException
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
'''

files["backend/app/routers/geometries.py"] = '''from fastapi import APIRouter, Depends, HTTPException
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
'''

# ==================== SOLVER ====================

files["backend/app/services/__init__.py"] = "# MMX"
files["backend/app/services/solver/__init__.py"] = "# MMX"

files["backend/app/services/solver/lattice.py"] = '''import numpy as np
CX = np.array([0,1,-1,0,0,0,0,1,-1,1,-1,1,-1,1,-1,0,0,0,0])
CY = np.array([0,0,0,1,-1,0,0,1,1,-1,-1,0,0,0,0,1,-1,1,-1])
CZ = np.array([0,0,0,0,0,1,-1,0,0,0,0,1,1,-1,-1,1,-1,1,-1])
W = np.array([1/3,1/18,1/18,1/18,1/18,1/18,1/18,1/36,1/36,1/36,1/36,1/36,1/36,1/36,1/36,1/36,1/36,1/36,1/36])
OPPOSITE = np.array([0,2,1,4,3,6,5,8,7,10,9,12,11,14,13,16,15,18,17])
NX = 19
'''

files["backend/app/services/solver/boundary.py"] = '''import numpy as np
from app.services.solver.lattice import OPPOSITE, CX, CY, CZ, W, NX
class BoundaryCondition:
    def __init__(self, face, bc_type, **kwargs):
        self.face = face; self.bc_type = bc_type; self.params = kwargs
class BoundaryHandler:
    @staticmethod
    def apply_velocity_bc(f, face, ux, uy, uz, rho, cx, cy, cz, w):
        if face == 'west':
            rho_face = (f[0,0,:,:]+f[2,0,:,:]+f[4,0,:,:]+f[6,0,:,:]+2*(f[2,0,:,:]+f[4,0,:,:]+f[6,0,:,:]))/(1+ux)
            for i in range(NX):
                if cx[i] > 0: f[i,0,:,:] = w[i]*rho_face*(1+3*(cx[i]*ux+cy[i]*uy+cz[i]*uz)+4.5*(cx[i]*ux+cy[i]*uy+cz[i]*uz)**2-1.5*(ux*ux+uy*uy+uz*uz))
        elif face == 'east':
            rho_face = (f[0,-1,:,:]+f[1,-1,:,:]+f[4,-1,:,:]+f[6,-1,:,:]+2*(f[1,-1,:,:]+f[4,-1,:,:]+f[6,-1,:,:]))/(1-ux)
            for i in range(NX):
                if cx[i] < 0: f[i,-1,:,:] = w[i]*rho_face*(1+3*(cx[i]*ux+cy[i]*uy+cz[i]*uz)+4.5*(cx[i]*ux+cy[i]*uy+cz[i]*uz)**2-1.5*(ux*ux+uy*uy+uz*uz))
        return f
    @staticmethod
    def apply_pressure_bc(f, face, rho_target, cx, cy, cz, w):
        if face == 'west':
            for i in range(NX):
                if cx[i] > 0: f[i,0,:,:] = w[i]*rho_target
        elif face == 'east':
            for i in range(NX):
                if cx[i] < 0: f[i,-1,:,:] = w[i]*rho_target
        return f
    @staticmethod
    def apply_bounce_back(f, solid_mask):
        for i in range(NX):
            opp = OPPOSITE[i]; f_i_solid = f[i][solid_mask].copy()
            f[i][solid_mask] = f[opp][solid_mask]; f[opp][solid_mask] = f_i_solid
        return f
    @staticmethod
    def apply_outflow_bc(f, face):
        if face == 'east': f[:,-1,:,:] = f[:,-2,:,:]
        elif face == 'west': f[:,0,:,:] = f[:,1,:,:]
        elif face == 'north': f[:,:,-1,:] = f[:,:,-2,:]
        elif face == 'south': f[:,:,0,:] = f[:,:,1,:]
        elif face == 'top': f[:,:,:,-1] = f[:,:,:,-2]
        elif face == 'bottom': f[:,:,:,0] = f[:,:,:,1]
        return f
'''

files["backend/app/services/solver/thermal.py"] = '''import numpy as np
class ThermalSolver:
    T_CX = np.array([0,1,-1,0,0,0,0]); T_CY = np.array([0,0,0,1,-1,0,0])
    T_CZ = np.array([0,0,0,0,0,1,-1]); T_W = np.array([1/7,1/14,1/14,1/14,1/14,1/14,1/14]); T_N = 7
    def __init__(self, nx, ny, nz, thermal_diffusivity=0.05):
        self.nx, self.ny, self.nz = nx, ny, nz; self.alpha = thermal_diffusivity
        self.tau_t = 3.0*self.alpha+0.5; self.omega_t = 1.0/self.tau_t
        self.g = np.zeros((self.T_N, nx, ny, nz), dtype=np.float32)
        for i in range(self.T_N): self.g[i] = self.T_W[i]
    def equilibrium(self, T, ux, uy, uz):
        g_eq = np.zeros_like(self.g)
        for i in range(self.T_N):
            ci_dot_u = self.T_CX[i]*ux+self.T_CY[i]*uy+self.T_CZ[i]*uz
            g_eq[i] = self.T_W[i]*T*(1.0+3.0*ci_dot_u+4.5*ci_dot_u**2-1.5*(ux**2+uy**2+uz**2))
        return g_eq
    def collide(self, T, ux, uy, uz):
        g_eq = self.equilibrium(T, ux, uy, uz); self.g += self.omega_t*(g_eq-self.g)
    def stream(self):
        for i in range(1, self.T_N):
            self.g[i] = np.roll(self.g[i], shift=(int(self.T_CX[i]),int(self.T_CY[i]),int(self.T_CZ[i])), axis=(0,1,2))
    def temperature(self): return np.sum(self.g, axis=0)
    def apply_thermal_bc(self, face, T_value):
        if face == 'west':
            for i in range(self.T_N): self.g[i,0,:,:] = self.T_W[i]*T_value
        elif face == 'east':
            for i in range(self.T_N): self.g[i,-1,:,:] = self.T_W[i]*T_value
        elif face == 'south':
            for i in range(self.T_N): self.g[i,:,0,:] = self.T_W[i]*T_value
        elif face == 'north':
            for i in range(self.T_N): self.g[i,:,-1,:] = self.T_W[i]*T_value
        elif face == 'bottom':
            for i in range(self.T_N): self.g[i,:,:,0] = self.T_W[i]*T_value
        elif face == 'top':
            for i in range(self.T_N): self.g[i,:,:,-1] = self.T_W[i]*T_value
    def apply_thermal_bounce_back(self, solid_mask, T_wall=1.0):
        for i in range(1, self.T_N): self.g[i][solid_mask] = self.T_W[i]*T_wall
'''

files["backend/app/services/solver/lbm.py"] = '''import numpy as np, time, logging
from typing import Optional, Callable
from dataclasses import dataclass, field
from app.services.solver.lattice import CX, CY, CZ, W, OPPOSITE, NX
from app.services.solver.boundary import BoundaryHandler, BoundaryCondition
from app.services.solver.thermal import ThermalSolver
logger = logging.getLogger(__name__)
try:
    import cupy as cp; GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False; cp = None
@dataclass
class SolverConfig:
    nx: int = 64; ny: int = 64; nz: int = 64; nu: float = 0.02; rho0: float = 1.0
    ux_inlet: float = 0.1; uy_inlet: float = 0.0; uz_inlet: float = 0.0; rho_outlet: float = 1.0
    enable_thermal: bool = False; thermal_diffusivity: float = 0.05; T_inlet: float = 1.0; T_wall: float = 0.0
    max_iters: int = 10000; convergence: float = 1e-6; save_interval: int = 100
    turbulence_model: str = "les"; les_cs: float = 0.17; use_trt: bool = True
    omega_magic: float = 1.0/(0.5+(1.0/(0.5+3.0*0.02))-0.5)
    solid_mask: Optional[np.ndarray] = None
    boundary_conditions: list = field(default_factory=list)
    on_iteration: Optional[Callable] = None; on_save: Optional[Callable] = None
class LBMSolver:
    def __init__(self, config):
        self.cfg = config; self.use_gpu = GPU_AVAILABLE; self.xp = cp if self.use_gpu else np
        nx, ny, nz = config.nx, config.ny, config.nz
        self.tau = 0.5+3.0*config.nu; self.omega = 1.0/self.tau
        if config.use_trt:
            self.omega_odd = self.omega; self.omega_even = 1.0/(0.5+config.omega_magic*(1.0/self.omega-0.5))
        else: self.omega_odd = self.omega; self.omega_even = self.omega
        self.cx = self.xp.asarray(CX, dtype=self.xp.float32); self.cy = self.xp.asarray(CY, dtype=self.xp.float32)
        self.cz = self.xp.asarray(CZ, dtype=self.xp.float32); self.w = self.xp.asarray(W, dtype=self.xp.float32)
        self.opposite = self.xp.asarray(OPPOSITE)
        self.f = self.xp.zeros((NX, nx, ny, nz), dtype=self.xp.float32)
        for i in range(NX): self.f[i] = self.w[i]*config.rho0
        if config.solid_mask is not None: self.solid = self.xp.asarray(config.solid_mask)
        else: self.solid = self.xp.zeros((nx, ny, nz), dtype=bool)
        self.rho = self.xp.ones((nx, ny, nz), dtype=self.xp.float32)*config.rho0
        self.ux = self.xp.zeros((nx, ny, nz), dtype=self.xp.float32)
        self.uy = self.xp.zeros((nx, ny, nz), dtype=self.xp.float32)
        self.uz = self.xp.zeros((nx, ny, nz), dtype=self.xp.float32)
        if config.enable_thermal:
            self.thermal = ThermalSolver(nx, ny, nz, config.thermal_diffusivity)
            if self.use_gpu: self.thermal.g = cp.asarray(self.thermal.g)
        else: self.thermal = None
        self.nu_turb = self.xp.zeros((nx, ny, nz), dtype=self.xp.float32)
        self.prev_rho = self.rho.copy(); self.iteration = 0; self.residual = 1.0
    def equilibrium(self, rho, ux, uy, uz):
        f_eq = self.xp.zeros_like(self.f); u_sq = ux*ux+uy*uy+uz*uz
        for i in range(NX):
            ci_dot_u = self.cx[i]*ux+self.cy[i]*uy+self.cz[i]*uz
            f_eq[i] = self.w[i]*rho*(1.0+3.0*ci_dot_u+4.5*ci_dot_u**2-1.5*u_sq)
        return f_eq
    def compute_macroscopic(self):
        self.rho = self.xp.sum(self.f, axis=0)
        rho_safe = self.xp.where(self.rho > 1e-10, self.rho, 1.0)
        self.ux = self.xp.sum(self.f*self.cx[:,None,None,None], axis=0)/rho_safe
        self.uy = self.xp.sum(self.f*self.cy[:,None,None,None], axis=0)/rho_safe
        self.uz = self.xp.sum(self.f*self.cz[:,None,None,None], axis=0)/rho_safe
        self.ux[self.solid] = 0; self.uy[self.solid] = 0; self.uz[self.solid] = 0
    def compute_les_viscosity(self):
        if self.cfg.turbulence_model == "none": return
        cs = self.cfg.les_cs; dx = 1.0
        duxdx = self._central_diff(self.ux, 0); duxdy = self._central_diff(self.ux, 1); duxdz = self._central_diff(self.ux, 2)
        duydx = self._central_diff(self.uy, 0); duydy = self._central_diff(self.uy, 1); duydz = self._central_diff(self.uy, 2)
        duzdx = self._central_diff(self.uz, 0); duzdy = self._central_diff(self.uz, 1); duzdz = self._central_diff(self.uz, 2)
        S = self.xp.sqrt(2*(duxdx**2+duydy**2+duzdz**2)+(duxdy+duydx)**2+(duxdz+duzdx)**2+(duydz+duzdy)**2)
        self.nu_turb = (cs*dx)**2*S
    def _central_diff(self, field, axis):
        return (self.xp.roll(field, -1, axis=axis)-self.xp.roll(field, 1, axis=axis))/2.0
    def collide(self):
        self.compute_macroscopic(); self.compute_les_viscosity()
        f_eq = self.equilibrium(self.rho, self.ux, self.uy, self.uz)
        if self.cfg.use_trt:
            f_sym = 0.5*(self.f+self.f[self.opposite]); f_eq_sym = 0.5*(f_eq+f_eq[self.opposite])
            f_anti = 0.5*(self.f-self.f[self.opposite]); f_eq_anti = 0.5*(f_eq-f_eq[self.opposite])
            self.f = f_sym+self.omega_even*(f_eq_sym-f_sym)+f_anti+self.omega_odd*(f_eq_anti-f_anti)
        else: self.f += self.omega*(f_eq-self.f)
        if self.thermal is not None: self.thermal.collide(self.thermal.temperature(), self.ux, self.uy, self.uz)
    def stream(self):
        for i in range(1, NX):
            self.f[i] = self.xp.roll(self.f[i], shift=(int(self.cx[i]),int(self.cy[i]),int(self.cz[i])), axis=(0,1,2))
        if self.thermal is not None: self.thermal.stream()
    def apply_boundary_conditions(self):
        for bc in self.cfg.boundary_conditions:
            if bc.bc_type == 'velocity':
                self.f = BoundaryHandler.apply_velocity_bc(self.f, bc.face, bc.params.get('ux',0), bc.params.get('uy',0), bc.params.get('uz',0), self.rho, self.cx, self.cy, self.cz, self.w)
            elif bc.bc_type == 'pressure':
                self.f = BoundaryHandler.apply_pressure_bc(self.f, bc.face, bc.params.get('rho',1.0), self.cx, self.cy, self.cz, self.w)
            elif bc.bc_type == 'outflow':
                self.f = BoundaryHandler.apply_outflow_bc(self.f, bc.face)
            elif bc.bc_type == 'thermal':
                if self.thermal: self.thermal.apply_thermal_bc(bc.face, bc.params.get('T', 1.0))
        if self.solid.any():
            self.f = BoundaryHandler.apply_bounce_back(self.f, self.solid)
            if self.thermal is not None: self.thermal.apply_thermal_bounce_back(self.solid, self.cfg.T_wall)
    def check_convergence(self):
        diff = self.xp.linalg.norm(self.rho-self.prev_rho)/max(self.xp.linalg.norm(self.prev_rho), 1e-10)
        self.prev_rho = self.rho.copy(); self.residual = float(diff)
        return self.residual < self.cfg.convergence
    def run(self):
        start_time = time.time(); results = {"iterations": [], "residuals": [], "field_snapshots": []}
        for it in range(self.cfg.max_iters):
            self.iteration = it; self.collide(); self.stream()
            self.apply_boundary_conditions(); self.compute_macroscopic()
            converged = self.check_convergence()
            if it % self.cfg.save_interval == 0 or converged:
                snapshot = self._save_snapshot(it)
                results["iterations"].append(it); results["residuals"].append(self.residual)
                results["field_snapshots"].append(snapshot)
                if self.cfg.on_iteration: self.cfg.on_iteration(it/self.cfg.max_iters, self.residual)
            if converged: break
        elapsed = time.time()-start_time
        results["final"] = self._save_snapshot(self.iteration)
        results["total_iterations"] = self.iteration; results["converged"] = converged
        results["compute_time"] = elapsed; results["grid_size"] = f"{self.cfg.nx}x{self.cfg.ny}x{self.cfg.nz}"
        results["gpu_used"] = self.use_gpu; return results
    def _save_snapshot(self, iteration):
        def to_cpu(arr):
            if self.use_gpu: return cp.asnumpy(arr)
            return np.array(arr)
        snapshot = {"iteration": iteration,
            "rho_stats": {"min": float(to_cpu(self.rho.min())), "max": float(to_cpu(self.rho.max())), "mean": float(to_cpu(self.rho.mean()))},
            "velocity_stats": {"max": float(to_cpu(self.xp.sqrt(self.ux**2+self.uy**2+self.uz**2).max())), "mean": float(to_cpu(self.xp.sqrt(self.ux**2+self.uy**2+self.uz**2).mean()))}}
        if self.thermal is not None:
            T = self.thermal.temperature()
            if self.use_gpu: T = cp.asnumpy(T)
            snapshot["temperature_stats"] = {"min": float(np.min(T)), "max": float(np.max(T)), "mean": float(np.mean(T))}
        return snapshot
    def export_vtk(self, filepath):
        def to_cpu(arr):
            if self.use_gpu: return cp.asnumpy(arr)
            return np.array(arr)
        rho = to_cpu(self.rho); ux = to_cpu(self.ux); uy = to_cpu(self.uy); uz = to_cpu(self.uz)
        vel_mag = np.sqrt(ux**2+uy**2+uz**2)
        nx, ny, nz = self.cfg.nx, self.cfg.ny, self.cfg.nz
        with open(filepath, 'w') as f:
            f.write("# vtk DataFile Version 3.0\\nMMX Mechanics CFD\\nASCII\\nDATASET STRUCTURED_POINTS\\n")
            f.write(f"DIMENSIONS {nx} {ny} {nz}\\nORIGIN 0 0 0\\nSPACING 1 1 1\\nPOINT_DATA {nx*ny*nz}\\n")
            f.write("SCALARS density float 1\\nLOOKUP_TABLE default\\n")
            f.write(' '.join(map(str, rho.flatten()))+'\\n')
            f.write("SCALARS velocity_magnitude float 1\\nLOOKUP_TABLE default\\n")
            f.write(' '.join(map(str, vel_mag.flatten()))+'\\n')
            if self.thermal is not None:
                T = to_cpu(self.thermal.temperature())
                f.write("SCALARS temperature float 1\\nLOOKUP_TABLE default\\n")
                f.write(' '.join(map(str, T.flatten()))+'\\n')
'''

# ==================== IMPORTERS ====================

files["backend/app/services/importer/stl_importer.py"] = '''import numpy as np
from struct import unpack
import os
class STLImporter:
    @staticmethod
    def read_stl(filepath):
        with open(filepath, 'rb') as f:
            f.read(80)
            try:
                num_tri = unpack('<I', f.read(4))[0]
                if os.path.getsize(filepath) == 84+num_tri*50:
                    return STLImporter._read_binary(filepath, num_tri)
            except: pass
        return STLImporter._read_ascii(filepath)
    @staticmethod
    def _read_binary(filepath, num_tri):
        vertices, normals = [], []
        with open(filepath, 'rb') as f:
            f.read(84)
            for _ in range(num_tri):
                nx,ny,nz = unpack('<3f', f.read(12))
                v1 = unpack('<3f', f.read(12)); v2 = unpack('<3f', f.read(12)); v3 = unpack('<3f', f.read(12))
                f.read(2); normals.append([nx,ny,nz]); vertices.extend([v1,v2,v3])
        vertices = np.array(vertices, dtype=np.float32); normals = np.array(normals, dtype=np.float32)
        unique, inverse = np.unique(vertices, axis=0, return_inverse=True)
        return {"vertices": unique, "triangles": inverse.reshape(-1,3), "normals": normals, "format": "binary", "num_triangles": num_tri}
    @staticmethod
    def _read_ascii(filepath):
        vertices, normals = [], []
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('facet normal'):
                    parts = line.split(); normals.append([float(parts[2]),float(parts[3]),float(parts[4])])
                elif line.startswith('vertex'):
                    parts = line.split(); vertices.append([float(parts[1]),float(parts[2]),float(parts[3])])
        vertices = np.array(vertices, dtype=np.float32); normals = np.array(normals, dtype=np.float32)
        unique, inverse = np.unique(vertices, axis=0, return_inverse=True)
        return {"vertices": unique, "triangles": inverse.reshape(-1,3), "normals": normals, "format": "ascii", "num_triangles": len(inverse.reshape(-1,3))}
    @staticmethod
    def voxelize(filepath, gx, gy, gz, fill_interior=True):
        mesh = STLImporter.read_stl(filepath); verts = mesh["vertices"]; tris = mesh["triangles"]
        bbox_min = verts.min(axis=0); bbox_max = verts.max(axis=0); extent = bbox_max-bbox_min
        extent[extent < 1e-10] = 1.0; scale = np.array([gx,gy,gz], dtype=np.float32)/extent
        scaled = (verts-bbox_min)*scale; grid = np.zeros((gx,gy,gz), dtype=bool)
        for tri in tris:
            v0,v1,v2 = scaled[tri[0]],scaled[tri[1]],scaled[tri[2]]
            min_x = max(0,int(np.floor(min(v0[0],v1[0],v2[0])))); max_x = min(gx-1,int(np.ceil(max(v0[0],v1[0],v2[0]))))
            min_y = max(0,int(np.floor(min(v0[1],v1[1],v2[1])))); max_y = min(gy-1,int(np.ceil(max(v0[1],v1[1],v2[1]))))
            min_z = max(0,int(np.floor(min(v0[2],v1[2],v2[2])))); max_z = min(gz-1,int(np.ceil(max(v0[2],v1[2],v2[2]))))
            for ix in range(min_x,max_x+1):
                for iy in range(min_y,max_y+1):
                    for iz in range(min_z,max_z+1):
                        if not grid[ix,iy,iz]:
                            p = np.array([ix+0.5,iy+0.5,iz+0.5])
                            if STLImporter._point_near_triangle(p,v0,v1,v2,1.0): grid[ix,iy,iz] = True
        if fill_interior:
            from scipy.ndimage import binary_fill_holes; grid = binary_fill_holes(grid)
        return grid
    @staticmethod
    def _point_near_triangle(p, v0, v1, v2, threshold=1.0):
        normal = np.cross(v1-v0, v2-v0); norm_len = np.linalg.norm(normal)
        if norm_len < 1e-10: return False
        normal = normal/norm_len; d = np.dot(normal, p-v0)
        if abs(d) > threshold: return False
        proj = p-d*normal
        w1 = np.cross(v2-v1, proj-v1); w2 = np.cross(v0-v2, proj-v2); w3 = np.cross(v1-v0, proj-v0)
        if np.dot(normal,w1) >= 0 and np.dot(normal,w2) >= 0 and np.dot(normal,w3) >= 0: return True
        for a,b in [(v0,v1),(v1,v2),(v2,v0)]:
            ab = b-a; ap = p-a; t = np.dot(ap,ab)/max(np.dot(ab,ab),1e-10); t = max(0,min(1,t))
            closest = a+t*ab
            if np.linalg.norm(p-closest) <= threshold: return True
        return False
    @staticmethod
    def get_stats(filepath):
        mesh = STLImporter.read_stl(filepath); verts = mesh["vertices"]
        return {"num_vertices": len(verts), "num_triangles": mesh["num_triangles"],
            "bounding_box": {"min": verts.min(axis=0).tolist(), "max": verts.max(axis=0).tolist(), "size": (verts.max(axis=0)-verts.min(axis=0)).tolist()}, "format": mesh["format"]}
'''

files["backend/app/services/importer/dxf_importer.py"] = '''import numpy as np
class DXFImporter:
    @staticmethod
    def read_dxf(filepath):
        entities, current, section = [], None, None
        with open(filepath, 'r', errors='ignore') as f: lines = [l.strip() for l in f.readlines()]
        i = 0
        while i < len(lines):
            line = lines[i]
            if line == 'ENTITIES': section = 'ENTITIES'
            elif line == 'ENDSEC':
                if current: entities.append(current); current = None
                section = None
            elif section == 'ENTITIES':
                if line in ('LINE','CIRCLE','ARC','LWPOLYLINE','POLYLINE'):
                    if current: entities.append(current)
                    current = {"type": line, "points": []}
                elif current:
                    if line == '10': current["points"].append({"x": float(lines[i+1]) if i+1 < len(lines) else 0})
                    elif line == '20':
                        if current["points"]: current["points"][-1]["y"] = float(lines[i+1]) if i+1 < len(lines) else 0
                    elif line == '40': current["radius"] = float(lines[i+1]) if i+1 < len(lines) else 0
            i += 1
        if current: entities.append(current)
        return DXFImporter._normalize(entities)
    @staticmethod
    def _normalize(entities):
        segments = []
        for ent in entities:
            if ent["type"] == "LINE":
                p = ent["points"]
                if len(p) >= 2: segments.append({"type": "line", "start": [p[0]["x"],p[0].get("y",0)], "end": [p[1]["x"],p[1].get("y",0)]})
            elif ent["type"] == "CIRCLE":
                c = ent["points"][0] if ent["points"] else {"x":0,"y":0}
                segments.append({"type": "circle", "center": [c["x"],c.get("y",0)], "radius": ent.get("radius",0)})
            elif ent["type"] in ("LWPOLYLINE","POLYLINE"):
                pts = [[p["x"],p.get("y",0)] for p in ent["points"]]
                segments.append({"type": "polyline", "points": pts, "closed": True})
        return {"entities": segments, "num_entities": len(segments), "bounding_box": DXFImporter._bbox(segments)}
    @staticmethod
    def _bbox(segments):
        all_x, all_y = [], []
        for seg in segments:
            if seg["type"] in ("line","polyline"):
                pts = [seg["start"],seg["end"]] if seg["type"] == "line" else seg["points"]
                for p in pts: all_x.append(p[0]); all_y.append(p[1])
            elif seg["type"] in ("circle","arc"):
                cx,cy = seg["center"]; r = seg["radius"]; all_x.extend([cx-r,cx+r]); all_y.extend([cy-r,cy+r])
        if not all_x: return {"min": [0,0], "max": [0,0], "size": [0,0]}
        return {"min": [min(all_x),min(all_y)], "max": [max(all_x),max(all_y)], "size": [max(all_x)-min(all_x),max(all_y)-min(all_y)]}
    @staticmethod
    def voxelize_2d(filepath, gx, gy):
        data = DXFImporter.read_dxf(filepath); segments = data["entities"]; bbox = data["bounding_box"]
        grid = np.zeros((gx,gy), dtype=bool)
        sx = gx/max(bbox["size"][0],1e-6); sy = gy/max(bbox["size"][1],1e-6); ox,oy = bbox["min"][0],bbox["min"][1]
        for seg in segments:
            if seg["type"] == "line":
                DXFImporter._line(grid, int((seg["start"][0]-ox)*sx), int((seg["start"][1]-oy)*sy), int((seg["end"][0]-ox)*sx), int((seg["end"][1]-oy)*sy))
            elif seg["type"] == "circle":
                DXFImporter._circle(grid, int((seg["center"][0]-ox)*sx), int((seg["center"][1]-oy)*sy), int(seg["radius"]*min(sx,sy)))
            elif seg["type"] == "polyline":
                pts = seg["points"]
                for i in range(len(pts)-1):
                    DXFImporter._line(grid, int((pts[i][0]-ox)*sx), int((pts[i][1]-oy)*sy), int((pts[i+1][0]-ox)*sx), int((pts[i+1][1]-oy)*sy))
        from scipy.ndimage import binary_fill_holes; return binary_fill_holes(grid)
    @staticmethod
    def _line(grid, x0, y0, x1, y1):
        dx,dy = abs(x1-x0),abs(y1-y0); sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1; err = dx-dy
        gx,gy = grid.shape
        while True:
            if 0 <= x0 < gx and 0 <= y0 < gy: grid[x0,y0] = True
            if x0 == x1 and y0 == y1: break
            e2 = 2*err
            if e2 > -dy: err -= dy; x0 += sx
            if e2 < dx: err += dx; y0 += sy
    @staticmethod
    def _circle(grid, cx, cy, r):
        if r < 1:
            if 0 <= cx < grid.shape[0] and 0 <= cy < grid.shape[1]: grid[cx,cy] = True
            return
        x,y,err = r,0,0; gx,gy = grid.shape
        while x >= y:
            for px,py in [(cx+x,cy+y),(cx+y,cy+x),(cx-y,cy+x),(cx-x,cy+y),(cx-x,cy-y),(cx-y,cy-x),(cx+y,cy-x),(cx+x,cy-y)]:
                if 0 <= px < gx and 0 <= py < gy: grid[px,py] = True
            y += 1; err += 1+2*y
            if 2*(err-x)+1 > 0: x -= 1; err += 1-2*x
'''

files["backend/app/services/importer/step_importer.py"] = '''import numpy as np
class STEPImporter:
    @staticmethod
    def read_step(filepath):
        import trimesh; mesh = trimesh.load(filepath)
        return {"vertices": mesh.vertices.astype(np.float32), "triangles": mesh.faces.astype(np.int32),
            "format": "step", "num_triangles": len(mesh.faces),
            "bounding_box": {"min": mesh.vertices.min(axis=0).tolist(), "max": mesh.vertices.max(axis=0).tolist(),
            "size": (mesh.vertices.max(axis=0)-mesh.vertices.min(axis=0)).tolist()}}
    @staticmethod
    def voxelize(filepath, gx, gy, gz):
        import trimesh; mesh = trimesh.load(filepath)
        voxel = mesh.voxelized(pitch=1.0).fill(); grid = np.array(voxel.matrix, dtype=bool)
        if grid.shape != (gx,gy,gz):
            from scipy.ndimage import zoom
            factors = (gx/grid.shape[0], gy/grid.shape[1], gz/grid.shape[2])
            grid = zoom(grid.astype(np.float32), factors, order=1) > 0.5
        return grid
'''

files["backend/app/services/importer/__init__.py"] = '''import os, numpy as np
from app.services.importer.stl_importer import STLImporter
from app.services.importer.dxf_importer import DXFImporter
from app.services.importer.step_importer import STEPImporter
class GeometryImporter:
    SUPPORTED_3D = ['.stl','.obj','.step','.stp','.iges','.igs']; SUPPORTED_2D = ['.dxf','.svg']
    @staticmethod
    def get_file_info(filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ['.stl']: return {"format": "stl", "dimension": "3D", "info": STLImporter.get_stats(filepath)}
        elif ext in ['.obj']: return {"format": "obj", "dimension": "3D", "info": GeometryImporter._obj_stats(filepath)}
        elif ext in ['.step','.stp','.iges','.igs']: return {"format": "step", "dimension": "3D", "info": {"format": "step"}}
        elif ext in ['.dxf']:
            data = DXFImporter.read_dxf(filepath)
            return {"format": "dxf", "dimension": "2D", "info": {"num_entities": data["num_entities"], "bounding_box": data["bounding_box"]}}
        return {"format": "unknown", "dimension": "unknown", "info": {}}
    @staticmethod
    def voxelize(filepath, gx, gy, gz=1, dimension="3D"):
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ['.stl']: return STLImporter.voxelize(filepath, gx, gy, gz)
        elif ext in ['.obj','.step','.stp','.iges','.igs']: return STEPImporter.voxelize(filepath, gx, gy, gz)
        elif ext in ['.dxf']: return DXFImporter.voxelize_2d(filepath, gx, gy)
        raise ValueError(f"Unsupported: {ext}")
    @staticmethod
    def _obj_stats(filepath):
        vertices, num_faces = [], 0
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('v '):
                    parts = line.split(); vertices.append([float(parts[1]),float(parts[2]),float(parts[3])])
                elif line.startswith('f '): num_faces += 1
        verts = np.array(vertices, dtype=np.float32)
        return {"num_vertices": len(verts), "num_triangles": num_faces,
            "bounding_box": {"min": verts.min(axis=0).tolist(), "max": verts.max(axis=0).tolist(), "size": (verts.max(axis=0)-verts.min(axis=0)).tolist()}, "format": "obj"}
'''

# ==================== I18N + TASKS ====================

files["backend/app/services/i18n/__init__.py"] = "# MMX"

files["backend/app/services/i18n/translator.py"] = '''import json
from pathlib import Path
class TranslationService:
    def __init__(self, default_lang="pt-BR"):
        self.default_lang = default_lang; self.translations = {}; self._load()
    def _load(self):
        d = Path(__file__).parent.parent.parent / "i18n"
        for f in ["en.json", "pt-BR.json"]:
            fp = d / f; lang = f.replace(".json", "")
            if fp.exists():
                with open(fp, 'r', encoding='utf-8') as fh: self.translations[lang] = json.load(fh)
    def translate(self, key, lang=None, **kw):
        lang = lang or self.default_lang
        for l in [lang, self.default_lang, "en"]:
            if l in self.translations:
                val = self.translations[l]
                for part in key.split("."):
                    if isinstance(val, dict) and part in val: val = val[part]
                    else: val = None; break
                if val is not None: return val.format(**kw) if kw else val
        return key
    def get_all_translations(self, lang):
        return self.translations.get(lang, self.translations.get(self.default_lang, {}))
    def translate_solver_output(self, text, target_lang="pt-BR"):
        if target_lang == "en": return text
        term_map = {"Converged": "Convergiu", "Simulation complete": "Simulacao concluida", "density": "densidade",
            "velocity": "velocidade", "pressure": "pressao", "temperature": "temperatura", "viscosity": "viscosidade"}
        result = text
        for en, pt in term_map.items(): result = result.replace(en, pt)
        return result
'''

files["backend/app/services/tasks.py"] = '''import asyncio, numpy as np, os, json, logging
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
'''

# ==================== I18N JSON ====================

files["backend/app/i18n/pt-BR.json"] = '''{
  "brand": "MMX Mechanics", "tagline": "Engenharia de Fluidos Computacional",
  "nav": {"dashboard": "Painel", "projects": "Projetos", "simulations": "Simulacoes", "library": "Biblioteca", "settings": "Configuracoes", "docs": "Documentacao", "profile": "Perfil", "logout": "Sair", "upgrade": "Upgrade"},
  "dashboard": {"welcome": "Bem-vindo de volta", "subtitle": "Visao geral das suas simulacoes", "newSimulation": "Nova Simulacao", "newProject": "Novo Projeto", "activeSimulations": "Simulacoes Ativas", "totalRuns": "Total de Execucoes", "gpuHours": "Horas de GPU", "avgComputeTime": "Tempo Medio", "recentSimulations": "Simulacoes Recentes", "quickActions": "Acoes Rapidas", "importGeometry": "Importar Geometria", "openProject": "Abrir Projeto", "viewResults": "Ver Resultados", "noSimulations": "Nenhuma simulacao ainda"},
  "simulation": {"new": "Nova Simulacao", "run": "Executar", "cancel": "Cancelar", "results": "Resultados", "converged": "Convergiu", "failed": "Falhou", "running": "Em Execucao", "queued": "Na Fila", "pending": "Pendente", "completed": "Concluida", "iterations": "Iteracoes", "residual": "Residuo", "progress": "Progresso", "computeTime": "Tempo de Calculo", "gridSize": "Tamanho da Grade", "gpuUsed": "GPU Utilizada", "step1": "Geometria", "step2": "Fisica", "step3": "Condicoes de Contorno", "step4": "Revisao", "next": "Proximo", "back": "Voltar"},
  "physics": {"title": "Parametros Fisicos", "density": "Densidade", "viscosity": "Viscosidade", "inletVelocity": "Velocidade de Entrada", "thermalAnalysis": "Analise Termica", "turbulenceModel": "Modelo de Turbulencia", "laminar": "Laminar", "les": "LES", "maxIterations": "Iteracoes Maximas"},
  "boundary": {"title": "Condicoes de Contorno", "west": "Oeste", "east": "Leste", "south": "Sul", "north": "Norte", "velocity": "Velocidade", "pressure": "Pressao", "wall": "Parede", "outflow": "Escoamento Livre"},
  "geometry": {"title": "Importar Geometria", "dragDrop": "Arraste e solte o arquivo aqui", "browse": "Procurar Arquivo", "voxelize": "Voxelizar Geometria", "uploading": "Enviando...", "uploadSuccess": "Arquivo importado"},
  "results": {"title": "Resultados", "velocityField": "Campo de Velocidade", "pressureField": "Campo de Pressao", "temperatureField": "Campo de Temperatura", "statistics": "Estatisticas", "maxVelocity": "Velocidade Maxima", "convergenceHistory": "Historico de Convergencia"},
  "billing": {"plan": "Plano", "free": "Gratuito", "pro": "Profissional", "enterprise": "Empresarial", "upgradeNow": "Fazer Upgrade"},
  "errors": {"fileTooLarge": "Arquivo muito grande", "unsupportedFormat": "Formato nao suportado", "simulationFailed": "A simulacao falhou"}
}'''

files["backend/app/i18n/en.json"] = '''{
  "brand": "MMX Mechanics", "tagline": "Computational Fluid Dynamics Engineering",
  "nav": {"dashboard": "Dashboard", "projects": "Projects", "simulations": "Simulations", "library": "Library", "settings": "Settings", "docs": "Documentation", "profile": "Profile", "logout": "Logout", "upgrade": "Upgrade"},
  "dashboard": {"welcome": "Welcome back", "subtitle": "Overview of your simulations", "newSimulation": "New Simulation", "newProject": "New Project", "activeSimulations": "Active Simulations", "totalRuns": "Total Runs", "gpuHours": "GPU Hours", "avgComputeTime": "Avg Compute Time", "recentSimulations": "Recent Simulations", "quickActions": "Quick Actions", "importGeometry": "Import Geometry", "openProject": "Open Project", "viewResults": "View Results", "noSimulations": "No simulations yet"},
  "simulation": {"new": "New Simulation", "run": "Run", "cancel": "Cancel", "results": "Results", "converged": "Converged", "failed": "Failed", "running": "Running", "queued": "Queued", "pending": "Pending", "completed": "Completed", "iterations": "Iterations", "residual": "Residual", "progress": "Progress", "computeTime": "Compute Time", "gridSize": "Grid Size", "gpuUsed": "GPU Used", "step1": "Geometry", "step2": "Physics", "step3": "Boundary Conditions", "step4": "Review", "next": "Next", "back": "Back"},
  "physics": {"title": "Physical Parameters", "density": "Density", "viscosity": "Viscosity", "inletVelocity": "Inlet Velocity", "thermalAnalysis": "Thermal Analysis", "turbulenceModel": "Turbulence Model", "laminar": "Laminar", "les": "LES", "maxIterations": "Max Iterations"},
  "boundary": {"title": "Boundary Conditions", "west": "West", "east": "East", "south": "South", "north": "North", "velocity": "Velocity", "pressure": "Pressure", "wall": "Wall", "outflow": "Outflow"},
  "geometry": {"title": "Import Geometry", "dragDrop": "Drag and drop file here", "browse": "Browse File", "voxelize": "Voxelize Geometry", "uploading": "Uploading...", "uploadSuccess": "File uploaded"},
  "results": {"title": "Results", "velocityField": "Velocity Field", "pressureField": "Pressure Field", "temperatureField": "Temperature Field", "statistics": "Statistics", "maxVelocity": "Max Velocity", "convergenceHistory": "Convergence History"},
  "billing": {"plan": "Plan", "free": "Free", "pro": "Pro", "enterprise": "Enterprise", "upgradeNow": "Upgrade Now"},
  "errors": {"fileTooLarge": "File too large", "unsupportedFormat": "Unsupported format", "simulationFailed": "Simulation failed"}
}'''

# ==================== BACKEND CONFIG FILES ====================

files["backend/requirements.txt"] = '''fastapi>=0.110.0
uvicorn[standard]>=0.27.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
celery>=5.3.0
redis>=5.0.0
numpy>=1.24.0
scipy>=1.12.0
trimesh>=4.0.0
ezdxf>=0.19.0
python-dotenv>=1.0.0
'''

files["backend/Dockerfile"] = '''FROM python:3.11-slim
RUN apt-get update && apt-get install -y build-essential git libgl1-mesa-glx libglib2.0-0 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install cupy-cuda12x || echo "GPU not available"
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

files["docker-compose.yml"] = '''version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: mmx
      POSTGRES_USER: mmx
      POSTGRES_PASSWORD: mmx
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [postgres, redis]
    environment:
      DATABASE_URL: postgresql+asyncpg://mmx:mmx@postgres:5432/mmx
      REDIS_URL: redis://redis:6379/0
      USE_GPU: "False"
      DEFAULT_LANG: "pt-BR"
    volumes: [uploads:/app/uploads, results:/app/results]
  celery-worker:
    build: ./backend
    command: celery -A app.services.tasks.celery_app worker --loglevel=info -Q gpu --concurrency=1
    depends_on: [redis, postgres]
    environment:
      DATABASE_URL: postgresql+asyncpg://mmx:mmx@postgres:5432/mmx
      REDIS_URL: redis://redis:6379/0
      USE_GPU: "True"
  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on: [backend]
volumes:
  pgdata:
  uploads:
  results:
'''

# Continua na Parte 3 (frontend)...
# ==================== FRONTEND ====================

files["frontend/package.json"] = '''{
  "name": "mmx-mechanics-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.22.0",
    "three": "^0.162.0",
    "@react-three/fiber": "^8.15.0",
    "@react-three/drei": "^9.92.0",
    "axios": "^1.6.0",
    "i18next": "^23.10.0",
    "react-i18next": "^14.0.0",
    "lucide-react": "^0.344.0",
    "recharts": "^2.12.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/three": "^0.162.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.3.0",
    "vite": "^5.1.0"
  }
}'''

files["frontend/vite.config.ts"] = '''import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': 'http://localhost:8000' } },
  build: { outDir: 'dist', chunkSizeWarningLimit: 1000 },
});'''

files["frontend/postcss.config.js"] = '''export default { plugins: { tailwindcss: {}, autoprefixer: {} } };'''

files["frontend/tailwind.config.ts"] = '''import type { Config } from 'tailwindcss';
const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        mmx: {
          bg: '#07080d', surface: '#0d1018', elevated: '#141823',
          border: '#1e2330', accent: '#00e5a0', 'accent-2': '#00b8ff',
          'accent-3': '#7c5cff', danger: '#ff4d6d', warn: '#ffb84d',
          text: '#e8ecf4', muted: '#7a8194', dim: '#4a5060',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        display: ['Space Grotesk', 'Inter', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn .4s ease-out',
        'slide-up': 'slideUp .5s cubic-bezier(.16,1,.3,1)',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { opacity: '0', transform: 'translateY(20px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        glowPulse: { '0%,100%': { boxShadow: '0 0 20px rgba(0,229,160,.15)' }, '50%': { boxShadow: '0 0 40px rgba(0,229,160,.35)' } },
      },
    },
  },
  plugins: [],
};
export default config;'''

files["frontend/Dockerfile"] = '''FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]'''

files["frontend/src/styles/globals.css"] = '''@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
@tailwind base;
@tailwind components;
@tailwind utilities;
* { scrollbar-width: thin; scrollbar-color: #1e2330 transparent; }
*::-webkit-scrollbar { width: 6px; height: 6px; }
*::-webkit-scrollbar-track { background: transparent; }
*::-webkit-scrollbar-thumb { background: #1e2330; border-radius: 3px; }
@layer components {
  .glass { @apply bg-mmx-surface/70 backdrop-blur-xl border border-mmx-border/60; }
  .glass-strong { @apply bg-mmx-elevated/80 backdrop-blur-xl border border-mmx-border; }
  .card { @apply glass rounded-2xl p-6; }
  .btn-primary { @apply bg-mmx-accent text-mmx-bg font-semibold px-5 py-2.5 rounded-xl hover:shadow-[0_0_30px_rgba(0,229,160,.3)] transition-all duration-300 active:scale-[.97] disabled:opacity-40; }
  .btn-ghost { @apply border border-mmx-border text-mmx-text font-medium px-5 py-2.5 rounded-xl hover:bg-mmx-elevated hover:border-mmx-accent/40 transition-all duration-300; }
  .input-mmx { @apply w-full bg-mmx-surface border border-mmx-border rounded-xl px-4 py-2.5 text-mmx-text placeholder-mmx-muted focus:border-mmx-accent/50 focus:ring-2 focus:ring-mmx-accent/15 outline-none transition-all duration-200; }
  .badge { @apply inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold; }
  .badge-success { @apply badge bg-mmx-accent/15 text-mmx-accent; }
  .badge-running { @apply badge bg-mmx-accent-2/15 text-mmx-accent-2; }
  .badge-pending { @apply badge bg-mmx-warn/15 text-mmx-warn; }
  .badge-failed { @apply badge bg-mmx-danger/15 text-mmx-danger; }
  .badge-queued { @apply badge bg-mmx-accent-3/15 text-mmx-accent-3; }
  .section-title { @apply font-display text-sm font-semibold text-mmx-muted uppercase tracking-wider; }
}
@layer utilities {
  .gradient-text { background: linear-gradient(135deg, #00e5a0 0%, #00b8ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  .grid-bg { background-image: linear-gradient(rgba(30,35,48,.4) 1px, transparent 1px), linear-gradient(90deg, rgba(30,35,48,.4) 1px, transparent 1px); background-size: 40px 40px; }
}'''

files["frontend/src/i18n/config.ts"] = '''import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import ptBR from './pt-BR.json';
import en from './en.json';
const savedLang = localStorage.getItem('mmx_lang') || 'pt-BR';
i18n.use(initReactI18next).init({
  resources: { 'pt-BR': { translation: ptBR }, en: { translation: en } },
  lng: savedLang, fallbackLng: 'en', interpolation: { escapeValue: false },
});
export default i18n;'''

files["frontend/src/i18n/pt-BR.json"] = files["backend/app/i18n/pt-BR.json"]
files["frontend/src/i18n/en.json"] = files["backend/app/i18n/en.json"]

files["frontend/src/services/api.ts"] = '''import axios from 'axios';
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const api = axios.create({ baseURL: API_BASE, headers: { 'Content-Type': 'application/json' } });
api.interceptors.request.use(config => {
  const token = localStorage.getItem('mmx_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use((res) => res, async (err) => {
  if (err.response?.status === 401 && !err.config._retry) {
    err.config._retry = true;
    const refreshToken = localStorage.getItem('mmx_refresh');
    if (refreshToken) {
      try {
        const { data } = await axios.post(`${API_BASE}/auth/refresh`, { token: refreshToken });
        localStorage.setItem('mmx_token', data.access_token);
        err.config.headers.Authorization = `Bearer ${data.access_token}`;
        return api(err.config);
      } catch { window.location.href = '/login'; }
    }
  }
  return Promise.reject(err);
});
export default api;
export const AuthAPI = {
  register: (email, password, fullName, company) => api.post('/auth/register', { email, password, full_name: fullName, company }),
  login: (email, password) => api.post('/auth/login', { email, password }),
  me: () => api.get('/auth/me'),
};
export const FileAPI = {
  upload: (file) => { const fd = new FormData(); fd.append('file', file); return api.post('/files/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } }); },
  voxelize: (fp, gx, gy, gz, dim) => api.post('/files/voxelize', { filepath: fp, grid_x: gx, grid_y: gy, grid_z: gz, dimension: dim }),
};
export const SimulationAPI = {
  create: (cfg) => api.post('/simulations/', cfg),
  get: (id) => api.get(`/simulations/${id}`),
  getResults: (id) => api.get(`/simulations/${id}/results`),
  list: () => api.get('/simulations/'),
};
export const GeometryAPI = {
  list: () => api.get('/geometries/'),
  generate: (id, gridSize) => api.post(`/geometries/${id}/generate`, { grid_size: gridSize }),
};'''

files["frontend/src/App.tsx"] = '''import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import './i18n/config';
import './styles/globals.css';
import AppLayout from './components/layout/AppLayout';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import GeometryLibrary from './pages/GeometryLibrary';
import SimulationNew from './pages/SimulationNew';
import SimulationResults from './pages/SimulationResults';
import { useEffect, useState } from 'react';
function AuthGuard({ children }) {
  const location = useLocation();
  const [checking, setChecking] = useState(true);
  const [authed, setAuthed] = useState(false);
  useEffect(() => { setAuthed(!!localStorage.getItem('mmx_token')); setChecking(false); }, []);
  if (checking) return <div className="min-h-screen bg-mmx-bg flex items-center justify-center"><div className="w-12 h-12 rounded-full border-4 border-mmx-border border-t-mmx-accent animate-spin" /></div>;
  if (!authed && location.pathname !== '/login') return <Navigate to="/login" replace />;
  if (authed && location.pathname === '/login') return <Navigate to="/" replace />;
  return children;
}
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<AuthGuard><Login /></AuthGuard>} />
        <Route path="/*" element={<AuthGuard><AppLayout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/library" element={<GeometryLibrary />} />
            <Route path="/simulation/new" element={<SimulationNew />} />
            <Route path="/simulation/:id" element={<SimulationResults />} />
            <Route path="/projects" element={<Dashboard />} />
            <Route path="/simulations" element={<Dashboard />} />
            <Route path="/settings" element={<Dashboard />} />
          </Routes>
        </AppLayout></AuthGuard>} />
      </Routes>
    </BrowserRouter>
  );
}'''

files["frontend/src/components/layout/AppLayout.tsx"] = '''import { ReactNode } from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
export default function AppLayout({ children }) {
  return (
    <div className="min-h-screen bg-mmx-bg text-mmx-text">
      <div className="fixed inset-0 grid-bg opacity-30 pointer-events-none" />
      <div className="fixed top-0 right-0 w-[600px] h-[600px] bg-mmx-accent/5 rounded-full blur-[120px] pointer-events-none" />
      <Sidebar />
      <div className="ml-[240px] min-h-screen flex flex-col relative z-10">
        <TopBar />
        <main className="flex-1 p-6 animate-fade-in">{children}</main>
      </div>
    </div>
  );
}'''

files["frontend/src/components/layout/Sidebar.tsx"] = '''import { NavLink, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { LayoutDashboard, FolderKanban, FlaskConical, Library, Settings, LogOut, Zap, ChevronRight } from 'lucide-react';
const navItems = [
  { key: 'dashboard', icon: LayoutDashboard, path: '/' },
  { key: 'projects', icon: FolderKanban, path: '/projects' },
  { key: 'simulations', icon: FlaskConical, path: '/simulations' },
  { key: 'library', icon: Library, path: '/library' },
  { key: 'settings', icon: Settings, path: '/settings' },
];
export default function Sidebar() {
  const { t } = useTranslation();
  const location = useLocation();
  return (
    <aside className="fixed left-0 top-0 h-screen w-[240px] glass-strong z-50 flex flex-col">
      <div className="px-6 py-6 border-b border-mmx-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-mmx-accent to-mmx-accent-2 flex items-center justify-center font-display font-bold text-mmx-bg text-lg">MX</div>
          <div><h1 className="font-display font-bold text-base">MMX <span className="gradient-text">Mechanics</span></h1>
          <p className="text-[10px] text-mmx-muted tracking-wider uppercase">CFD Engine</p></div>
        </div>
      </div>
      <nav className="flex-1 py-4 px-3 space-y-1">
        {navItems.map(item => {
          const active = location.pathname === item.path;
          return (
            <NavLink key={item.key} to={item.path} className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${active ? 'bg-mmx-accent/10 text-mmx-accent border border-mmx-accent/20' : 'text-mmx-muted hover:text-mmx-text hover:bg-mmx-elevated border border-transparent'}`}>
              <item.icon size={18} className={active ? 'text-mmx-accent' : 'text-mmx-muted'} />
              <span>{t(`nav.${item.key}`)}</span>
              {active && <ChevronRight size={14} className="ml-auto text-mmx-accent" />}
            </NavLink>
          );
        })}
      </nav>
      <div className="px-4 py-3 border-t border-mmx-border">
        <div className="glass rounded-xl p-3 flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-mmx-accent animate-pulse" />
          <div className="flex-1"><p className="text-xs font-semibold">GPU Engine</p><p className="text-[10px] text-mmx-muted">CUDA CuPy D3Q19</p></div>
          <Zap size={16} className="text-mmx-accent" />
        </div>
      </div>
      <div className="px-4 py-4 border-t border-mmx-border flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-mmx-accent-3 to-mmx-accent-2 flex items-center justify-center text-mmx-bg font-bold text-sm">FF</div>
        <div className="flex-1 min-w-0"><p className="text-sm font-semibold truncate">Francisco</p><p className="text-[10px] text-mmx-muted truncate">Figsmor Engenharia</p></div>
        <button className="text-mmx-muted hover:text-mmx-danger"><LogOut size={16} /></button>
      </div>
    </aside>
  );
}'''

files["frontend/src/components/layout/TopBar.tsx"] = '''import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Search, Bell, Globe } from 'lucide-react';
export default function TopBar() {
  const { i18n } = useTranslation();
  const [lang, setLang] = useState(i18n.language);
  return (
    <header className="sticky top-0 z-40 glass border-b border-mmx-border">
      <div className="flex items-center justify-between px-6 py-3">
        <div className="relative w-full max-w-xl">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-mmx-muted" />
          <input type="text" placeholder="Buscar..." className="input-mmx pl-10 text-sm" />
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => { const n = lang === 'pt-BR' ? 'en' : 'pt-BR'; i18n.changeLanguage(n); setLang(n); }} className="p-2 rounded-xl hover:bg-mmx-elevated text-mmx-muted hover:text-mmx-text"><Globe size={18} /></button>
          <button className="relative p-2 rounded-xl hover:bg-mmx-elevated text-mmx-muted"><Bell size={18} /><span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-mmx-accent" /></button>
        </div>
      </div>
    </header>
  );
}'''

files["frontend/src/pages/Login.tsx"] = '''import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Lock, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { AuthAPI } from '../services/api';
export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState(''); const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState(''); const [company, setCompany] = useState('');
  const [showPwd, setShowPwd] = useState(false); const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const handleSubmit = async (e) => {
    e.preventDefault(); setLoading(true); setError('');
    try {
      const { data } = mode === 'login' ? await AuthAPI.login(email, password) : await AuthAPI.register(email, password, fullName, company);
      localStorage.setItem('mmx_token', data.access_token); localStorage.setItem('mmx_refresh', data.refresh_token); navigate('/');
    } catch (err) { setError(err.response?.data?.detail || 'Erro'); } finally { setLoading(false); }
  };
  return (
    <div className="min-h-screen bg-mmx-bg flex">
      <div className="fixed inset-0 grid-bg opacity-20 pointer-events-none" />
      <div className="hidden lg:flex flex-col justify-center w-1/2 px-16 relative z-10">
        <div className="flex items-center gap-3 mb-8"><div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-mmx-accent to-mmx-accent-2 flex items-center justify-center font-bold text-mmx-bg text-xl">MX</div><h1 className="font-display font-bold text-2xl">MMX <span className="gradient-text">Mechanics</span></h1></div>
        <h2 className="font-display text-4xl font-bold mb-4">Fluidodinamica Computacional<br /><span className="gradient-text">na velocidade da GPU</span></h2>
        <p className="text-mmx-muted text-lg mb-8 max-w-md">Simulacao de escoamento e transferencia de calor com Lattice Boltzmann Method acelerado por CUDA.</p>
      </div>
      <div className="flex-1 flex items-center justify-center px-6 relative z-10">
        <div className="w-full max-w-md">
          <div className="glass-strong rounded-3xl p-8">
            <div className="flex gap-2 mb-6 p-1 bg-mmx-surface rounded-xl">
              <button onClick={() => setMode('login')} className={`flex-1 py-2.5 rounded-lg text-sm font-semibold ${mode === 'login' ? 'bg-mmx-accent text-mmx-bg' : 'text-mmx-muted'}`}>Entrar</button>
              <button onClick={() => setMode('register')} className={`flex-1 py-2.5 rounded-lg text-sm font-semibold ${mode === 'register' ? 'bg-mmx-accent text-mmx-bg' : 'text-mmx-muted'}`}>Criar Conta</button>
            </div>
            {error && <div className="mb-4 p-3 rounded-xl bg-mmx-danger/10 border border-mmx-danger/20 text-mmx-danger text-sm">{error}</div>}
            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'register' && <input type="text" value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Nome completo" className="input-mmx" required />}
              {mode === 'register' && <input type="text" value={company} onChange={e => setCompany(e.target.value)} placeholder="Empresa" className="input-mmx" />}
              <div className="relative"><Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-mmx-muted" /><input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="seu@email.com" className="input-mmx pl-10" required /></div>
              <div className="relative"><Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-mmx-muted" /><input type={showPwd ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} placeholder="Senha" className="input-mmx pl-10 pr-10" required minLength={6} /><button type="button" onClick={() => setShowPwd(!showPwd)} className="absolute right-3 top-1/2 -translate-y-1/2 text-mmx-muted">{showPwd ? <EyeOff size={16} /> : <Eye size={16} />}</button></div>
              <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">{loading ? <div className="w-5 h-5 rounded-full border-2 border-mmx-bg/30 border-t-mmx-bg animate-spin" /> : <>{mode === 'login' ? 'Entrar' : 'Criar Conta'} <ArrowRight size={18} /></>}</button>
            </form>
          </div>
          <p className="text-center text-xs text-mmx-muted mt-6">MMX Mechanics v1.0.0 - Figsmor Engenharia</p>
        </div>
      </div>
    </div>
  );
}'''

files["frontend/src/pages/Dashboard.tsx"] = '''import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Activity, FlaskConical, Plus, Upload, CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react';
import { SimulationAPI } from '../services/api';
export default function Dashboard() {
  const { t } = useTranslation(); const navigate = useNavigate();
  const [sims, setSims] = useState([]); const [loading, setLoading] = useState(true);
  useEffect(() => { SimulationAPI.list().then(res => setSims(res.data)).catch(() => setSims([])).finally(() => setLoading(false)); }, []);
  const stats = [
    { label: t('dashboard.activeSimulations'), value: sims.filter(s => s.status === 'running').length, icon: Activity },
    { label: t('dashboard.totalRuns'), value: sims.length, icon: FlaskConical },
  ];
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="font-display text-2xl font-bold">{t('dashboard.welcome')}, Francisco</h1><p className="text-mmx-muted text-sm mt-1">{t('dashboard.subtitle')}</p></div>
        <div className="flex gap-2">
          <button onClick={() => navigate('/library')} className="btn-ghost flex items-center gap-2 text-sm"><Upload size={16} /> {t('dashboard.importGeometry')}</button>
          <button onClick={() => navigate('/simulation/new')} className="btn-primary flex items-center gap-2 text-sm"><Plus size={16} /> {t('dashboard.newSimulation')}</button>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {stats.map((s, i) => <div key={i} className="card"><s.icon size={20} className="text-mmx-accent mb-3" /><p className="text-2xl font-bold font-mono">{s.value}</p><p className="text-xs text-mmx-muted mt-1">{s.label}</p></div>)}
      </div>
      <div className="card lg:col-span-2">
        <h2 className="section-title mb-4">{t('dashboard.recentSimulations')}</h2>
        {loading ? <div className="flex justify-center py-12"><div className="w-8 h-8 rounded-full border-2 border-mmx-border border-t-mmx-accent animate-spin" /></div> :
         sims.length === 0 ? <div className="text-center py-12"><FlaskConical size={40} className="text-mmx-dim mx-auto mb-3" /><p className="text-mmx-muted">{t('dashboard.noSimulations')}</p></div> :
         <div className="space-y-2">{sims.map(sim => <div key={sim.id} onClick={() => navigate(`/simulation/${sim.id}`)} className="flex items-center gap-4 p-3 rounded-xl hover:bg-mmx-elevated cursor-pointer">
           <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-mmx-accent/15">{sim.status === 'completed' ? <CheckCircle2 size={18} className="text-mmx-accent" /> : sim.status === 'running' ? <Loader2 size={18} className="text-mmx-accent-2 animate-spin" /> : sim.status === 'failed' ? <XCircle size={18} className="text-mmx-danger" /> : <Clock size={18} className="text-mmx-warn" />}</div>
           <div className="flex-1"><p className="text-sm font-semibold">{sim.name}</p><p className="text-xs text-mmx-muted">{sim.grid_size}</p></div>
           <span className={`badge badge-${sim.status === 'completed' ? 'success' : sim.status === 'running' ? 'running' : sim.status === 'failed' ? 'failed' : 'pending'}`}>{t(`simulation.${sim.status}`)}</span>
         </div>)}</div>}
      </div>
    </div>
  );
}'''

files["frontend/src/pages/GeometryLibrary.tsx"] = '''import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Circle, Square, Box, Layers, Wind, Thermometer, ArrowRight } from 'lucide-react';
const GEOS = [
  { id: 'cylinder-flow', name: 'Escoamento sobre Cilindro', dim: '2D', cat: 'Externos', diff: 'Iniciante', re: 100, icon: Circle },
  { id: 'channel-flow', name: 'Canal Plano 2D', dim: '2D', cat: 'Internos', diff: 'Iniciante', re: 50, icon: Square },
  { id: 'lid-cavity', name: 'Cavidade com Tampa', dim: '2D', cat: 'Validacao', diff: 'Iniciante', re: 400, icon: Box },
  { id: 'backward-step', name: 'Degrau Atras', dim: '2D', cat: 'Internos', diff: 'Intermediario', re: 500, icon: Layers },
  { id: 'sphere-3d', name: 'Esfera em 3D', dim: '3D', cat: 'Externos', diff: 'Intermediario', re: 200, icon: Circle },
  { id: '3d-duct', name: 'Duto Retangular 3D', dim: '3D', cat: 'Industriais', diff: 'Intermediario', re: 300, icon: Square },
  { id: 'heat-tube', name: 'Tubo com Troca Termica', dim: '3D', cat: 'Industriais', diff: 'Avancado', re: 150, icon: Thermometer },
];
export default function GeometryLibrary() {
  const navigate = useNavigate(); const [search, setSearch] = useState(''); const [dim, setDim] = useState('Todos');
  const filtered = GEOS.filter(g => (!search || g.name.toLowerCase().includes(search.toLowerCase())) && (dim === 'Todos' || g.dim === dim));
  return (
    <div className="space-y-6">
      <div><h1 className="font-display text-2xl font-bold">Biblioteca de Geometrias</h1><p className="text-mmx-muted text-sm mt-1">7 geometrias pre-configuradas</p></div>
      <div className="flex gap-3">
        <div className="relative flex-1"><Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-mmx-muted" /><input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar..." className="input-mmx pl-10" /></div>
        <div className="flex gap-2">{['Todos','2D','3D'].map(d => <button key={d} onClick={() => setDim(d)} className={`px-4 py-2.5 rounded-xl text-sm font-medium ${dim === d ? 'bg-mmx-accent text-mmx-bg' : 'glass text-mmx-muted'}`}>{d}</button>)}</div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((g, i) => <div key={g.id} className="card group hover:border-mmx-accent/30 cursor-pointer animate-slide-up" style={{ animationDelay: `${i*30}ms` }} onClick={() => navigate(`/simulation/new?geo=${g.id}`)}>
          <div className="h-32 rounded-xl bg-mmx-bg mb-4 flex items-center justify-center"><g.icon size={40} className="text-mmx-accent group-hover:scale-110 transition-transform" /></div>
          <h3 className="font-semibold text-sm mb-2">{g.name}</h3>
          <div className="flex justify-between text-xs text-mmx-muted"><span>{g.dim} · {g.cat}</span><span className="font-mono">Re={g.re}</span></div>
          <ArrowRight size={14} className="text-mmx-accent mt-3 opacity-0 group-hover:opacity-100" />
        </div>)}
      </div>
    </div>
  );
}'''

files["frontend/src/pages/SimulationNew.tsx"] = '''import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Check, ChevronRight, ChevronLeft, Play, Thermometer, Grid3x3, Gauge } from 'lucide-react';
import { SimulationAPI, GeometryAPI } from '../services/api';
export default function SimulationNew() {
  const { t } = useTranslation(); const navigate = useNavigate(); const [params] = useSearchParams();
  const [step, setStep] = useState(0); const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState({ name: `Sim_${Date.now().toString(36).slice(-6)}`, grid_size: 64, viscosity: 0.02, density: 1.0, inlet_velocity: 0.1, max_iterations: 10000, turbulence_model: 'les', enable_thermal: false, thermal_diffusivity: 0.05, T_inlet: 1.0, T_wall: 0.0, boundary_conditions: [{ face: 'west', type: 'velocity', params: { ux: 0.1, uy: 0, uz: 0 } }, { face: 'east', type: 'outflow' }, { face: 'south', type: 'wall' }, { face: 'north', type: 'wall' }] });
  const reynolds = (config.inlet_velocity * config.grid_size) / config.viscosity;
  const handleRun = async () => {
    setLoading(true);
    try {
      let gridPath = null; const geoId = params.get('geo');
      if (geoId) { const { data } = await GeometryAPI.generate(geoId, config.grid_size); gridPath = data.grid_path; }
      const { data } = await SimulationAPI.create({ project_id: 'default', name: config.name, grid_x: config.grid_size, grid_y: config.grid_size, grid_z: config.grid_size, viscosity: config.viscosity, density: config.density, inlet_velocity: config.inlet_velocity, max_iterations: config.max_iterations, turbulence_model: config.turbulence_model, enable_thermal: config.enable_thermal, thermal_diffusivity: config.thermal_diffusivity, T_inlet: config.T_inlet, T_wall: config.T_wall, boundary_conditions: config.boundary_conditions, grid_path: gridPath, async: false });
      navigate(`/simulation/${data.simulation_id}`);
    } catch (err) { console.error(err); } finally { setLoading(false); }
  };
  const steps = ['Geometria', 'Fisica', 'Condicoes', 'Revisao'];
  return (
    <div className="space-y-6">
      <h1 className="font-display text-2xl font-bold">{t('simulation.new')}</h1>
      <div className="flex items-center gap-2">
        {steps.map((s, i) => <div key={i} className="flex items-center flex-1">
          <div className={`flex items-center gap-2 ${i <= step ? 'text-mmx-accent' : 'text-mmx-muted'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${i < step ? 'bg-mmx-accent text-mmx-bg' : i === step ? 'bg-mmx-accent/20 border-2 border-mmx-accent' : 'bg-mmx-surface border border-mmx-border'}`}>{i < step ? <Check size={14} /> : i + 1}</div>
            <span className="text-sm font-medium hidden sm:block">{s}</span>
          </div>
          {i < steps.length - 1 && <div className={`flex-1 h-px mx-2 ${i < step ? 'bg-mmx-accent' : 'bg-mmx-border'}`} />}
        </div>)}
      </div>
      <div className="card max-w-2xl">
        {step === 0 && <div className="space-y-4">
          <h2 className="section-title">Geometria</h2>
          <input type="text" value={config.name} onChange={e => setConfig({ ...config, name: e.target.value })} className="input-mmx" />
          <div><div className="flex justify-between mb-1.5"><label className="text-xs text-mmx-muted">Grade</label><span className="text-xs font-mono text-mmx-accent">{config.grid_size}^3</span></div><input type="range" min={16} max={128} step={8} value={config.grid_size} onChange={e => setConfig({ ...config, grid_size: parseInt(e.target.value) })} className="w-full accent-mmx-accent" /></div>
          <div className="p-3 rounded-xl bg-mmx-elevated flex items-center gap-3"><Grid3x3 size={18} className="text-mmx-accent-2" /><div><p className="text-xs text-mmx-muted">Celulas</p><p className="text-sm font-mono">{(config.grid_size ** 3).toLocaleString()}</p></div></div>
        </div>}
        {step === 1 && <div className="space-y-4">
          <h2 className="section-title">Fisica</h2>
          <div><div className="flex justify-between mb-1.5"><label className="text-xs text-mmx-muted">Densidade</label><span className="text-xs font-mono text-mmx-accent">{config.density}</span></div><input type="range" min={0.1} max={10} step={0.1} value={config.density} onChange={e => setConfig({ ...config, density: parseFloat(e.target.value) })} className="w-full accent-mmx-accent" /></div>
          <div><div className="flex justify-between mb-1.5"><label className="text-xs text-mmx-muted">Viscosidade</label><span className="text-xs font-mono text-mmx-accent">{config.viscosity}</span></div><input type="range" min={0.001} max={0.1} step={0.001} value={config.viscosity} onChange={e => setConfig({ ...config, viscosity: parseFloat(e.target.value) })} className="w-full accent-mmx-accent" /></div>
          <div><div className="flex justify-between mb-1.5"><label className="text-xs text-mmx-muted">Velocidade</label><span className="text-xs font-mono text-mmx-accent">{config.inlet_velocity}</span></div><input type="range" min={0.01} max={0.5} step={0.01} value={config.inlet_velocity} onChange={e => setConfig({ ...config, inlet_velocity: parseFloat(e.target.value) })} className="w-full accent-mmx-accent" /></div>
          <div className="flex gap-2">{['none','les'].map(m => <button key={m} onClick={() => setConfig({ ...config, turbulence_model: m })} className={`flex-1 py-2 rounded-lg text-xs font-medium ${config.turbulence_model === m ? 'bg-mmx-accent text-mmx-bg' : 'glass text-mmx-muted'}`}>{m === 'none' ? 'Laminar' : 'LES'}</button>)}</div>
          <div className="p-3 rounded-xl bg-mmx-elevated flex items-center gap-3"><Gauge size={18} className="text-mmx-accent-3" /><div><p className="text-xs text-mmx-muted">Reynolds</p><p className="text-sm font-mono text-mmx-accent-3">Re = {reynolds.toFixed(0)}</p></div></div>
          <button onClick={() => setConfig({ ...config, enable_thermal: !config.enable_thermal })} className="w-full flex items-center justify-between p-3 rounded-xl bg-mmx-surface border border-mmx-border"><div className="flex items-center gap-3"><Thermometer size={18} className={config.enable_thermal ? 'text-mmx-danger' : 'text-mmx-muted'} /><span className="text-sm">Analise Termica</span></div><div className={`w-10 h-6 rounded-full ${config.enable_thermal ? 'bg-mmx-accent' : 'bg-mmx-border'}`}><div className={`w-4 h-4 rounded-full bg-mmx-bg transition-transform ${config.enable_thermal ? 'translate-x-5' : 'translate-x-1'}`} /></div></button>
        </div>}
        {step === 2 && <div className="space-y-4"><h2 className="section-title">Condicoes de Contorno</h2>{config.boundary_conditions.map((bc, i) => <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-mmx-elevated"><span className="badge badge-queued">{bc.face}</span><span className="text-sm">{bc.type}</span></div>)}</div>}
        {step === 3 && <div className="space-y-4"><h2 className="section-title">Revisao</h2><div className="grid grid-cols-2 gap-3">{[["Nome", config.name], ["Grade", `${config.grid_size}^3`], ["Reynolds", reynolds.toFixed(0)], ["Iteracoes", config.max_iterations], ["Turbulencia", config.turbulence_model], ["Termico", config.enable_thermal ? 'Sim' : 'Nao']].map((r, i) => <div key={i} className="p-3 rounded-xl bg-mmx-elevated"><p className="text-xs text-mmx-muted">{r[0]}</p><p className="text-sm font-mono">{r[1]}</p></div>)}</div></div>}
      </div>
      <div className="flex justify-between max-w-2xl">
        <button onClick={() => setStep(Math.max(0, step - 1))} disabled={step === 0} className="btn-ghost flex items-center gap-2 text-sm disabled:opacity-30"><ChevronLeft size={16} /> Voltar</button>
        {step < 3 ? <button onClick={() => setStep(step + 1)} className="btn-primary flex items-center gap-2 text-sm">Proximo <ChevronRight size={16} /></button> : <button onClick={handleRun} disabled={loading} className="btn-primary flex items-center gap-2 text-sm">{loading ? <div className="w-4 h-4 rounded-full border-2 border-mmx-bg/30 border-t-mmx-bg animate-spin" /> : <Play size={16} />} Executar</button>}
      </div>
    </div>
  );
}'''

files["frontend/src/pages/SimulationResults.tsx"] = '''import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, CheckCircle2, XCircle, Clock, Cpu, Activity } from 'lucide-react';
import { SimulationAPI } from '../services/api';
import Viewer3D from '../components/Viewer3D';
export default function SimulationResults() {
  const { id } = useParams(); const navigate = useNavigate();
  const [sim, setSim] = useState(null); const [results, setResults] = useState(null); const [loading, setLoading] = useState(true); const [field, setField] = useState('velocity');
  useEffect(() => {
    if (!id) return;
    const poll = async () => {
      try {
        const { data } = await SimulationAPI.get(id); setSim(data);
        if (data.status === 'completed') { const { data: res } = await SimulationAPI.getResults(id); setResults(res); setLoading(false); }
        else if (data.status === 'failed') setLoading(false);
        else setTimeout(poll, 2000);
      } catch { setLoading(false); }
    }; poll();
  }, [id]);
  if (loading && !sim) return <div className="flex items-center justify-center h-96"><div className="w-12 h-12 rounded-full border-4 border-mmx-border border-t-mmx-accent animate-spin" /></div>;
  if (!sim) return <div className="text-mmx-muted">Nao encontrada</div>;
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/')} className="p-2 rounded-xl hover:bg-mmx-elevated"><ArrowLeft size={18} className="text-mmx-muted" /></button>
        <div><h1 className="font-display text-xl font-bold">{sim.name}</h1><p className="text-xs text-mmx-muted">{sim.grid_size} - {sim.gpu_used ? 'GPU' : 'CPU'}</p></div>
      </div>
      {sim.status === 'completed' && results && <>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[{ icon: CheckCircle2, label: 'Convergiu', value: results.converged ? 'Sim' : 'Nao', color: 'text-mmx-accent' },
            { icon: Clock, label: 'Tempo', value: `${results.compute_time?.toFixed(1)}s`, color: 'text-mmx-accent-2' },
            { icon: Cpu, label: 'GPU', value: results.gpu_used ? 'CUDA' : 'CPU', color: 'text-mmx-accent-3' },
            { icon: Activity, label: 'Iteracoes', value: results.total_iterations?.toLocaleString(), color: 'text-mmx-warn' }].map((s, i) => (
            <div key={i} className="card flex items-center gap-3"><s.icon size={20} className={s.color} /><div><p className="text-xs text-mmx-muted">{s.label}</p><p className="text-sm font-mono">{s.value}</p></div></div>))}
        </div>
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title">Resultados</h2>
            <div className="flex gap-2">{['velocity','pressure','temperature'].map(f => <button key={f} onClick={() => setField(f)} className={`px-3 py-1.5 rounded-lg text-xs font-medium ${field === f ? 'bg-mmx-accent text-mmx-bg' : 'glass text-mmx-muted'}`}>{f}</button>)}</div>
          </div>
          <Viewer3D field={field} simId={id} />
        </div>
      </>}
      {sim.status === 'failed' && <div className="card flex items-center gap-4"><XCircle size={24} className="text-mmx-danger" /><div><p className="font-semibold text-mmx-danger">Falhou</p><p className="text-sm text-mmx-muted">{sim.error_message}</p></div></div>}
    </div>
  );
}'''

files["frontend/src/components/Viewer3D.tsx"] = '''import { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
export default function Viewer3D({ field, simId }) {
  const mountRef = useRef(null); const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!mountRef.current) return;
    const mount = mountRef.current; const width = mount.clientWidth; const height = 400;
    const scene = new THREE.Scene(); scene.background = new THREE.Color(0x07080d);
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000); camera.position.set(80, 60, 80);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true }); renderer.setSize(width, height); mount.appendChild(renderer.domElement);
    const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true;
    scene.add(new THREE.AmbientLight(0x404060, 0.5));
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8); dirLight.position.set(50, 80, 50); scene.add(dirLight);
    const boxGeo = new THREE.BoxGeometry(64, 64, 64); const edges = new THREE.EdgesGeometry(boxGeo);
    scene.add(new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x1e2330 })));
    const gridSize = 64; const planeGeo = new THREE.PlaneGeometry(gridSize, gridSize, gridSize - 1, gridSize - 1);
    const colors = new Float32Array(gridSize * gridSize * 3);
    for (let i = 0; i < gridSize; i++) for (let j = 0; j < gridSize; j++) {
      const x = i / gridSize, y = j / gridSize; let val = field === 'velocity' ? Math.sin(x * Math.PI * 2) * Math.cos(y * Math.PI * 2) * 0.5 + 0.5 : field === 'pressure' ? (1 - x) * (1 - y) : x * 0.8 + y * 0.2;
      const idx = (i * gridSize + j) * 3;
      colors[idx] = Math.max(0, Math.min(1, 1.5 - Math.abs(4 * val - 3))); colors[idx + 1] = Math.max(0, Math.min(1, 1.5 - Math.abs(4 * val - 2))); colors[idx + 2] = Math.max(0, Math.min(1, 1.5 - Math.abs(4 * val - 1)));
    }
    planeGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    const plane = new THREE.Mesh(planeGeo, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.DoubleSide, transparent: true, opacity: 0.8 })); plane.rotation.x = -Math.PI / 2; scene.add(plane);
    for (let s = 0; s < 8; s++) { const points = []; let x = 0, y = 32, z = (s - 4) * 8; for (let step = 0; step < 60; step++) { points.push(new THREE.Vector3(x, y + Math.sin(step * 0.1) * 5, z + Math.cos(step * 0.15) * 3)); x += 1.2; } scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), new THREE.LineBasicMaterial({ color: 0x00e5a0, transparent: true, opacity: 0.4 }))); }
    setLoading(false);
    let frameId; const animate = () => { frameId = requestAnimationFrame(animate); controls.update(); renderer.render(scene, camera); }; animate();
    return () => { cancelAnimationFrame(frameId); mount.removeChild(renderer.domElement); renderer.dispose(); };
  }, [field, simId]);
  return <div className="relative">{loading && <div className="absolute inset-0 flex items-center justify-center"><div className="w-8 h-8 rounded-full border-2 border-mmx-border border-t-mmx-accent animate-spin" /></div>}<div ref={mountRef} className="w-full rounded-xl overflow-hidden bg-mmx-bg" style={{ height: 400 }} /></div>;
}'''

files["frontend/src/components/FileUploader.tsx"] = '''import { useState, useRef } from 'react';
import { UploadCloud, FileBox, CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { FileAPI } from '../services/api';
export default function FileUploader({ onVoxelize }) {
  const [dragging, setDragging] = useState(false); const [uploading, setUploading] = useState(false); const [voxelizing, setVoxelizing] = useState(false);
  const [fileInfo, setFileInfo] = useState(null); const [gridSize, setGridSize] = useState(64); const [error, setError] = useState('');
  const inputRef = useRef(null);
  const handleFile = async (file) => { setUploading(true); setError(''); try { const { data } = await FileAPI.upload(file); setFileInfo(data); } catch (err) { setError('Erro ao enviar'); } finally { setUploading(false); } };
  const handleDrop = (e) => { e.preventDefault(); setDragging(false); const file = e.dataTransfer.files[0]; if (file) handleFile(file); };
  const handleVoxelize = async () => { if (!fileInfo) return; setVoxelizing(true); try { const { data } = await FileAPI.voxelize(fileInfo.filepath, gridSize, gridSize, gridSize, fileInfo.dimension); onVoxelize(data.grid_path); } catch (err) { setError('Erro na voxelizacao'); } finally { setVoxelizing(false); } };
  return (
    <div className="space-y-4">
      <div onDragOver={e => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={handleDrop} onClick={() => inputRef.current?.click()} className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer ${dragging ? 'border-mmx-accent bg-mmx-accent/5' : 'border-mmx-border hover:border-mmx-accent/40'}`}>
        <input ref={inputRef} type="file" accept=".stl,.obj,.step,.stp,.iges,.igs,.dxf" onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])} className="hidden" />
        {uploading ? <Loader2 size={32} className="text-mmx-accent animate-spin mx-auto" /> : <UploadCloud size={32} className="text-mmx-accent mx-auto" />}
        <p className="text-sm font-medium mt-3">Arraste e solte o arquivo aqui</p>
      </div>
      {error && <div className="flex items-center gap-2 p-3 rounded-xl bg-mmx-danger/10 text-mmx-danger text-sm"><AlertCircle size={16} /> {error}</div>}
      {fileInfo && <div className="card">
        <div className="flex items-center gap-3 mb-4"><CheckCircle2 size={20} className="text-mmx-accent" /><span className="text-sm font-semibold">Arquivo importado</span></div>
        <div className="grid grid-cols-2 gap-3 mb-4"><div className="p-2 rounded-lg bg-mmx-elevated"><p className="text-xs text-mmx-muted">Arquivo</p><p className="text-sm font-mono truncate">{fileInfo.filename}</p></div><div className="p-2 rounded-lg bg-mmx-elevated"><p className="text-xs text-mmx-muted">Formato</p><p className="text-sm font-mono">{fileInfo.format} - {fileInfo.dimension}</p></div></div>
        <div className="mb-4"><div className="flex justify-between mb-1.5"><label className="text-xs text-mmx-muted">Grade</label><span className="text-xs font-mono text-mmx-accent">{gridSize}^3</span></div><input type="range" min={16} max={128} step={8} value={gridSize} onChange={e => setGridSize(parseInt(e.target.value))} className="w-full accent-mmx-accent" /></div>
        <button onClick={handleVoxelize} disabled={voxelizing} className="btn-primary w-full flex items-center justify-center gap-2">{voxelizing ? <Loader2 size={18} className="animate-spin" /> : <FileBox size={18} />} Voxelizar</button>
      </div>}
    </div>
  );
}'''

files["README.md"] = '''# MMX Mechanics - CFD Engine
## Plataforma SaaS de Fluidodinamica Computacional com GPU CUDA e Lattice Boltzmann Method (LBM D3Q19)
### Powered by Figsmor Engenharia - figsmor.com.br

### Como executar:
docker-compose up -d

### Endpoints:
- Frontend: http://localhost:3000
- API: http://localhost:8000/api/docs
- Health: http://localhost:8000/api/health
'''

# ==================== EXECUTAR ====================

print("MMX Mechanics - Criando arquivos...")
print("=" * 50)

created = 0
for filepath, content in files.items():
    dirname = os.path.dirname(filepath)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    created += 1
    print(f"  OK: {filepath}")

print("=" * 50)
print(f"Total: {created} arquivos criados com sucesso!")
print("Agora rode: git add . && git commit -m 'MMX Mechanics' && git push")