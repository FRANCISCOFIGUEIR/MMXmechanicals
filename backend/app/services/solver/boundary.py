import numpy as np
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
