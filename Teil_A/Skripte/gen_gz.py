"""HLR-Ansichten der Baugruppe fuer die Gesamtzeichnung im Halbschnitt (wie Vorlage 14.2.3):
unten Schnitt (Y>=0 behalten, Schnittebene Y=0), oben Aussenansicht; Vorderansicht ohne Pos. 2 und 10."""
import time, pickle, numpy as np
import cadquery as cq
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
import build2, hlr

parts = build2.build_all()
CUT = {"1", "2", "3", "4", "5.1", "5.2", "6", "11", "12"}
keep = cq.Solid.makeBox(400, 200, 400, cq.Vector(-100, 0, -200))
sec_shapes, sec_faces, overlay = [], [], []
for pos, name, s in parts:
    subs = list(s) if isinstance(s, cq.Compound) and pos == "11" else [s]
    for sub in subs:
        bb = sub.BoundingBox()
        is_ball = pos == "11" and abs(bb.xlen - 9.0) < 0.2 and abs(bb.ylen - 9.0) < 0.2
        if pos in CUT and not is_ball:
            c = sub.intersect(keep)
            if c.Volume() < 1e-6: continue
            sec_shapes.append(c)
            for f in c.Faces():
                if f.geomType() == "PLANE" and abs(f.normalAt().y) > 0.999 and abs(f.Center().y) < 1e-6:
                    sec_faces.append((pos, f))
        else:
            cy = (bb.ymin + bb.ymax) / 2
            if bb.ymax <= 0.5: continue
            if is_ball and abs(cy) > 1.0: continue      # vereinfacht wie Vorlage: nur die Kugel in der Schnittebene
            if pos == "7" and cy < 0: continue
            sec_shapes.append(sub)
            if bb.ymin < 0.5 and pos in ("9", "10") or is_ball:
                overlay.append(box(bb.xmin, bb.zmin, bb.xmax, bb.zmax) if not is_ball else
                               Polygon([((bb.xmin+bb.xmax)/2 + 4.5*np.cos(t), (bb.zmin+bb.zmax)/2 + 4.5*np.sin(t)) for t in np.linspace(0, 2*np.pi, 60)]))
t = time.time(); sec_lines = hlr.project(sec_shapes, (0, -1, 0), (1, 0, 0), regularity=True); print("HLR Schnitt %.1fs" % (time.time()-t))
# Aussenansicht (obere Haelfte): komplette Baugruppe, gleiche Blickrichtung
ext_shapes = []
for pos, name, s in parts:
    subs = list(s) if isinstance(s, cq.Compound) and pos == "11" else [s]
    ext_shapes += subs
t = time.time(); ext_lines = hlr.project(ext_shapes, (0, -1, 0), (1, 0, 0), regularity=True); print("HLR Aussen %.1fs" % (time.time()-t))
fv_shapes = [s for pos, name, s in parts if pos not in ("2", "10")]
t = time.time(); fv_lines = hlr.project(fv_shapes, (1, 0, 0), (0, 1, 0), regularity=True); print("HLR Vorderansicht %.1fs" % (time.time()-t))

def face_poly(f):
    def ring(w):
        n = max(40, int(w.Length()/0.25))
        return [(p.x, p.z) for p in (w.positionAt(i/n) for i in range(n))]
    return Polygon(ring(f.outerWire()), [ring(w) for w in f.innerWires()]).buffer(0)
cover = unary_union(overlay) if overlay else None
polys = []
for pos, f in sec_faces:
    p = face_poly(f)
    if cover is not None: p = p.difference(cover)
    polys.append((pos, p))
pickle.dump({"sec_lines": sec_lines, "ext_lines": ext_lines, "fv_lines": fv_lines, "polys": polys}, open("gz_buch.pkl", "wb"))
print("ok", len(sec_lines), len(ext_lines), len(fv_lines), len(polys))
