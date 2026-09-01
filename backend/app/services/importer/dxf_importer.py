import numpy as np
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
