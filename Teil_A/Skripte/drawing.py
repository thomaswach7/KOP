import math, time, pickle
import cadquery as cq
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon as MPoly
from shapely.geometry import Polygon, LineString, MultiLineString
from shapely.ops import unary_union
import build, hlr

TH, TN = 0.5*72/25.4, 0.25*72/25.4          # Linienbreiten in pt (0,5 / 0,25 mm)
FV = (112.0, 180.0)                          # Mitte Vorderansicht (Blatt-mm)
SV = (222.0, 180.0)                          # X=0 / Achse Schnittansicht

parts = build.build()

# ---------------- Schnitt A-A (Ebene Y=0, Blick in +Y, Material Y<0 entfernt) -------------
CUT = {"1","2","3","4","5.1","5.2","6"}       # Normteile (8) und Federn (7) nicht geschnitten
HATCH = {"1":(45,3.0),"2":(135,3.0),"3":(45,2.0),"4":(135,2.5),"5.1":(45,1.6),"5.2":("x",1.2),"6":(135,0.8)}
keep = cq.Solid.makeBox(400,200,400,cq.Vector(-100,0,-200))
sec_shapes, sec_faces = [], []
for pos,name,s in parts:
    bb = s.BoundingBox()
    if pos in CUT:
        c = s.intersect(keep)
        if c.Volume() < 1e-6: continue
        sec_shapes.append(c)
        for f in c.Faces():
            if f.geomType()=="PLANE" and abs(f.normalAt().y)>0.999 and abs(f.Center().y)<1e-6:
                sec_faces.append((pos,f))
    else:
        if bb.ymax <= 0.5:          # liegt ganz vor der Schnittebene -> entfaellt
            continue
        if pos=="7" and (bb.ymin+bb.ymax)/2 < 0:   # Federn 2 liegen vor der Schnittebene
            continue
        sec_shapes.append(s)
t=time.time()
sec_lines = hlr.project(sec_shapes, (0,-1,0), (1,0,0))
print("HLR Schnitt %.1fs, %d Kanten, %d Schnittflaechen"%(time.time()-t,len(sec_lines),len(sec_faces)))

# ---------------- Vorderansicht (Blick aus +X, ohne Pos. 2) -----------------------------------
fv_shapes = [s for pos,name,s in parts if pos!="2"]
t=time.time()
fv_lines = hlr.project(fv_shapes, (1,0,0), (0,1,0))
print("HLR Vorderansicht %.1fs, %d Kanten"%(time.time()-t,len(fv_lines)))

def face_poly(f):
    """Schnittflaeche (Ebene Y=0) -> shapely Polygon in (X,Z)."""
    def ring(w):
        n = max(40, int(w.Length()/0.25))
        return [(p.x,p.z) for p in (w.positionAt(i/n) for i in range(n))]
    return Polygon(ring(f.outerWire()), [ring(w) for w in f.innerWires()]).buffer(0)

polys = [(pos, face_poly(f)) for pos,f in sec_faces]
pickle.dump({"sec_lines":sec_lines,"fv_lines":fv_lines,"polys":polys}, open("views.pkl","wb"))
