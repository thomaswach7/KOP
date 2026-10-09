import cadquery as cq
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder

def compound(shapes):
    c = TopoDS_Compound(); b = BRep_Builder(); b.MakeCompound(c)
    for s in shapes: b.Add(c, s.wrapped)
    return c

from OCP.BRepLib import BRepLib
def project(shapes, normal, xdir, regularity=False):
    """Liefert Listen von Polylinien (sichtbare Kanten + Umrisse) in Bildkoordinaten."""
    algo = HLRBRep_Algo()
    c = compound(shapes)
    if regularity: BRepLib.EncodeRegularity_s(c, 1e-3)   # tangentiale Kanten nicht zeichnen
    algo.Add(c)
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0,0,0), gp_Dir(*normal), gp_Dir(*xdir))))
    algo.Update(); algo.Hide()
    h = HLRBRep_HLRToShape(algo)
    out = []
    for comp in (h.VCompound(), h.OutLineVCompound()):
        if comp is None or comp.IsNull(): continue
        for e in cq.Shape.cast(comp).Edges():
            n = 2 if e.geomType()=='LINE' else max(8, int(e.Length()/0.3))
            pts = [e.positionAt(i/n) for i in range(n+1)]
            out.append([(p.x, p.y) for p in pts])
    return out
