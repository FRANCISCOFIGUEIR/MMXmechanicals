import os, numpy as np
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
