import numpy as np, time, logging
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
            f.write("# vtk DataFile Version 3.0\nMMX Mechanics CFD\nASCII\nDATASET STRUCTURED_POINTS\n")
            f.write(f"DIMENSIONS {nx} {ny} {nz}\nORIGIN 0 0 0\nSPACING 1 1 1\nPOINT_DATA {nx*ny*nz}\n")
            f.write("SCALARS density float 1\nLOOKUP_TABLE default\n")
            f.write(' '.join(map(str, rho.flatten()))+'\n')
            f.write("SCALARS velocity_magnitude float 1\nLOOKUP_TABLE default\n")
            f.write(' '.join(map(str, vel_mag.flatten()))+'\n')
            if self.thermal is not None:
                T = to_cpu(self.thermal.temperature())
                f.write("SCALARS temperature float 1\nLOOKUP_TABLE default\n")
                f.write(' '.join(map(str, T.flatten()))+'\n')
