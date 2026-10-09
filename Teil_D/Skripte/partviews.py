import cadquery as cq, numpy as np
from shapely.geometry import Polygon
import hlr

def project(shapes, N, Vx, regularity=False):
    return hlr.project(shapes if isinstance(shapes, list) else [shapes], N, Vx, regularity)

def section_view(shape, N, Vx, keep_box, plane_pt, plane_n):
    """Schnittansicht: Teil mit keep_box schneiden, HLR + Schnittflaechen (Polygone in Ansichtskoordinaten)."""
    c = shape.intersect(keep_box)
    lines = project([c], N, Vx)
    N = np.array(N, float); Vx = np.array(Vx, float); Vy = np.cross(N, Vx)
    pn = np.array(plane_n, float); pp = np.array(plane_pt, float)
    polys = []
    for f in c.Faces():
        if f.geomType() != "PLANE": continue
        n = np.array(f.normalAt().toTuple())
        if abs(abs(n.dot(pn)) - 1) > 1e-6: continue
        if abs((np.array(f.Center().toTuple()) - pp).dot(pn)) > 1e-5: continue
        def ring(w):
            m = max(60, int(w.Length()/0.2))
            pts = [np.array(w.positionAt(i/m).toTuple()) for i in range(m)]
            return [(p.dot(Vx), p.dot(Vy)) for p in pts]
        polys.append(Polygon(ring(f.outerWire()), [ring(w) for w in f.innerWires()]).buffer(0))
    return lines, polys

def half_section_view(shape, N, Vx, remove_box, plane_pt, plane_n, regularity=False):
    """Halbschnitt: remove_box wird abgezogen; Linien auf der Achse (v=0, waagrecht) werden entfernt."""
    c = shape.cut(remove_box)
    lines = project([c], N, Vx, regularity)
    lines = [pl for pl in lines if not all(abs(p[1]) < 1e-6 for p in pl)]
    N = np.array(N, float); Vx = np.array(Vx, float); Vy = np.cross(N, Vx)
    pn = np.array(plane_n, float); pp = np.array(plane_pt, float)
    polys = []
    for f in c.Faces():
        if f.geomType() != "PLANE": continue
        n = np.array(f.normalAt().toTuple())
        if abs(abs(n.dot(pn)) - 1) > 1e-6: continue
        if abs((np.array(f.Center().toTuple()) - pp).dot(pn)) > 1e-5: continue
        def ring(w):
            m = max(60, int(w.Length()/0.2))
            pts = [np.array(w.positionAt(i/m).toTuple()) for i in range(m)]
            return [(p.dot(Vx), p.dot(Vy)) for p in pts]
        polys.append(Polygon(ring(f.outerWire()), [ring(w) for w in f.innerWires()]).buffer(0))
    return lines, polys
