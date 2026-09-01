import numpy as np
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
