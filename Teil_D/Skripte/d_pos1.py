import pickle, math
from dimlib import *
d = pickle.load(open("p1.pkl", "rb"))
sh = Sheet("A3")
SX, SY = 228.0, 168.0
FX, FY = 108.0, 168.0
S = lambda x, r: (SX + x, SY + r)
TS = lambda u, v: (SX + u, SY + v)
TF = lambda a, b: (FX + a, FY + b)

from shapely.geometry import LineString as _LS
from shapely.ops import unary_union as _uu
_sp = _uu(d["sec_p"]).buffer(-0.05)
from shapely.geometry import Point as _Pt
def _naht(pl):
    L = _LS(pl); pts = [L.interpolate(t, normalized=True) for t in (0.25, 0.5, 0.75)]
    return sum(_sp.contains(p) for p in pts) >= 2
sh.polylines([pl for pl in d["sec_l"] if not _naht(pl)], TS)
for p in d["sec_p"]: sh.hatch(p, TS, 45, 2.5)
sh.polylines(d["fv_l"], TF)
sh.cl((SX-6, SY), (SX+87, SY))
for r in (52, -52): sh.cl(S(34, r), S(60, r))
sh.cl((FX-48, FY), (FX+48, FY)); sh.cl((FX, FY-70), (FX, FY+70))
for b in (52, -52): sh.cl(TF(-13, b), TF(13, b))
# Schnittverlauf A-A (Ebene durch die Arme = senkrecht)
for sg in (1, -1):
    y1 = FY+sg*86
    sh.line([(FX, FY+sg*79), (FX, y1)], lw=2*TH)
    sh.line([(FX, y1-sg*2), (FX+8, y1-sg*2)]); sh.arrow((FX+8, y1-sg*2), (FX, y1-sg*2))
    sh.text(FX+10, y1-sg*2-1.75, "A", 5)
sh.text(SX+40, SY+97, "A–A", 5, ha="center")

# ---------------- Schnitt A-A ----------------
sh.dim(S(0, 22.5), S(0, -22.5), SX-10, "Ø45k6", "v")
sh.datum((SX-10, SY-22.5), (0, -1), "B", length=6)
sh.dim(S(81, 22.5), S(81, -22.5), SX+91, "Ø45k6", "v")
lt = (SX+91, SY+22.5); le = (SX+91, SY+52)
sh.line([lt, le]); sh.arrow(lt, le)
sh.gdt((SX+91-3.5, SY+52), "coax", "Ø0,05", "B", leader_to=None)
# Laengen oben (Bezug rechtes Ende)
sh.dim(S(81, 22.5), S(65, 25.5), SY+70, "16", "h")
sh.dim(S(81, 22.5), S(57, 39.5), SY+77, "24", "h")
sh.dim(S(81, 22.5), S(55.5, 61), SY+84, "25,5", "h")
# Laengen unten
sh.dim(S(38.5, -61), S(55.5, -61), SY-69, "17|−0,1|−0,2", "h")
sh.dim(S(37, -39.5), S(57, -39.5), SY-76, "20", "h")
sh.dim(S(29, -25.5), S(65, -25.5), SY-83, "36 −0,1", "h")
sh.dim(S(0, -22.5), S(81, -22.5), SY-90, "81", "h")
# Gesamtrundlauf linker Lagersitz, Gesamtplanlauf Arm links
sh.gdt((SX-32, SY+64), "trunout", "0,05", "A", leader_to=S(13, 22.6), leader_via=(S(13, 0)[0], SY+67.5), side="right")

# ---------------- Ansicht von rechts ----------------
sh.dim(TF(9, 52), TF(9, -52), FX-30, "104", "v", ext1=False, ext2=False)
for b in (52, -52): sh.line([TF(-10, b), TF(-31.5, b)])
sh.dim(TF(-9, 52), TF(9, 52), FY+67, "18", "h")
sh.leader(TF(4*math.cos(math.radians(45)), 52+4*math.sin(math.radians(45))), TF(22, 78), "Ø8H8", end_len=14)
sh.leader(TF(9*math.cos(math.radians(150)), -52+9*math.sin(math.radians(150))) if False else TF(-6.36, -58.36), TF(-22, -76), "R9", end_len=8)
sh.dim(TF(-39.5, 0), TF(39.5, 0), FY-93, "Ø79", "h")
# Passfedernut (rechts)
sh.dim(TF(18.3, 4), TF(18.3, -4), FX+27, "8JS9", "v")
sh.dim(TF(-15, 0), TF(18.3, -4), FY-31, "33,3+0,2", "h")
lt = (FX+27, FY+4); le = (FX+27, FY+30)
sh.line([lt, le]); sh.arrow(lt, le)
sh.gdt((FX+27-3.5, FY+30), "sym", "0,02", "A")
# Oe30H7 mit Bezug A, Oe51 diagonal
for angd, rr, txt, tdist in ((225, 15, "Ø30H7", 0), (135, 25.5, "Ø51", 19)):
    a = math.radians(angd); u = (math.cos(a), math.sin(a))
    p1, p2 = TF(rr*u[0], rr*u[1]), TF(-rr*u[0], -rr*u[1])
    sh.line([p1, p2]); sh.arrow(p1, p2); sh.arrow(p2, p1)
    if txt == "Ø51":
        na = (math.sin(math.radians(45)), math.cos(math.radians(45))); tp = TF(tdist*u[0]+1.0*na[0], tdist*u[1]+1.0*na[1])
        sh.text(tp[0], tp[1], txt, H, rot=-45, ha="center")
a = math.radians(225); u = (math.cos(a), math.sin(a))
p1 = TF(15*u[0], 15*u[1]); le = TF(46*u[0], 46*u[1])
sh.line([p1, le])
tp = TF(30*u[0]-0.7, 30*u[1]+0.7); sh.text(tp[0], tp[1], "Ø30H7", H, rot=45, ha="center")
sh.datum(le, u, "A", length=4)
# Gesamtplanlauf rechte Armflaeche (in dieser Ansicht sichtbar): Hinweislinie mit Punkt
dot = TF(-4, 44)
sh.ax.add_patch(Circle(dot, 0.7, color="k"))
sh.line([dot, TF(-26, 62), TF(-30, 62)])
sh.gdt((FX-30-24, FY+58.5), "trunout", "0,05", "A"); sh.text(FX-54, FY+67.5, "beidseitig", 3.0)

# ---------------- Oberflaechen ----------------
sh.surf_leader(S(6, -22.6), S(-2, -40), "z") if False else None
sh.surf_leader(S(20, 22.6), (SX+20, SY+40), "z")
sh.surf_leader(S(74, 22.6), (SX+72, SY+40), "z")
sh.surf_leader(S(10, 15.1), (SX+8, SY+5), "y")
sh.surf_leader(S(38.4, -44), (SX+20, SY-52), "y")
sh.surf_leader(S(29.1, -24), (SX+14, SY-30), "y") if False else None
sh.surf_leader(TF(4*math.cos(math.radians(-40)), -52+4*math.sin(math.radians(-40))), TF(26, -60), "z")

gx, gy = 28, 54
sh.surf_symbol((gx, gy), removal=False, prohibited=True)
sh.text(gx+9, gy+0.5, "(", 7); sh.surf_symbol((gx+15, gy), removal=True); sh.text(gx+24, gy+0.5, ")", 7)
for i, (l, rz) in enumerate((("x", "Rz 63"), ("y", "Rz 16"), ("z", "Rz 4"))):
    xx = gx+36+i*52
    sh.surf_symbol((xx, gy), l); sh.text(xx+12, gy+2, "=", 3.5); sh.surf_symbol((xx+21, gy), text=rz)
sh.edge_symbols(206, 50)
sh.notes(25, 16, guss=True, freistich="E0,6×0,3", radien="R2")
sh.titleblock("Antriebsnabe (Pos. 1)", "14.2.5.2", "EN-GJS-700-2", "1:1")
import dxfout
print(dxfout.export(sh, "Pos01_Antriebsnabe.dxf"))
sh.save("Pos01_Antriebsnabe.pdf", "prev_p1.png", dpi=150)
print("ok")
