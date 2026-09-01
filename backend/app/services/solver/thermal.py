import numpy as np
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
