import numpy as np
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
