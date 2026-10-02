import pickle, math
from dimlib import *
d = pickle.load(open("p5.pkl", "rb"))
sh = Sheet("A3")
FX, FY = 125.0, 190.0          # Kupplungsachse (Bogenmittelpunkt) in der Vorderansicht
SX, SY = 315.0, 190.0          # Symmetrieebene / Achse in Schnitt A-A
F = lambda x, y: (FX + x, FY + y)
S = lambda z, y: (SX + z, SY + y)
pol = lambda r, a_from_down: (r*math.sin(math.radians(a_from_down)), -r*math.cos(math.radians(a_from_down)))

sh.polylines(d["fv_l"], F)
sh.polylines(d["sec_l"], S)
for p in d["gewicht"]: sh.hatch(p, S, 45, 2.0)
for p in d["belag"]: sh.hatch(p, S, "x", 1.2)

# Mittellinien
sh.cl(F(-12, 0), F(12, 0)); sh.cl(F(0, 10), F(0, -72))
th = np.radians(np.linspace(-90-75, -90+75, 200))
sh.ax.plot(FX+51.5*np.cos(th), FY+51.5*np.sin(th), color="k", lw=TN, dashes=(14, 3, 1.5, 3))
for sg in (1, -1):
    hx, hy = 47.89*sg, -19.24
    sh.cl(F(hx-12, hy), F(hx+12, hy)); sh.cl(F(hx, hy-12), F(hx, hy+12))
    bx, by = pol(51.5, 67.5*sg)
    sh.cl(F(0, 0), F(bx*1.25, by*1.25))
sh.cl(S(-32, 0), S(32, 0)); sh.cl(S(0, 8), S(0, -70))
# Schnittverlauf A-A (Symmetrieebene)
for yy in (-4, -72):
    sh.line([F(0, yy), F(0, yy-7 if yy < -10 else yy+7)], lw=2*TH)
for yy, sg in ((3, 1), (-79, -1)):
    sh.line([F(0, yy), F(8, yy)]); sh.arrow(F(8, yy), F(0, yy)); sh.text(*F(9.5, yy-1.75), "A", 5)
sh.text(*S(0, 24), "A–A", 5, ha="center")

# ---------------- Vorderansicht ----------------
sh.dim(F(-47.89, -19.24), F(47.89, -19.24), FY+16, "95,77", "h")
sh.dim(F(0, 0), F(-47.89, -19.24), FX-66, "19,24", "v", ext1=True, ext2=True) if False else None
sh.leader(F(47.89+4*math.cos(math.radians(40)), -19.24+4*math.sin(math.radians(40))), F(64, 12), "2× Ø8H9", end_len=17)
sh.gdt((F(64, 12)[0], F(64, 12)[1]-8.5), "perp", "Ø0,05", "A")
# Radien
b = pol(51.5, 67.5); c = (FX+b[0], FY+b[1])
sh.leader((c[0]+9*math.cos(math.radians(-20)), c[1]+9*math.sin(math.radians(-20))), F(72, -40), "R9", end_len=8)
sh.leader((c[0]+8.5*math.cos(math.radians(60)), c[1]+8.5*math.sin(math.radians(60))), F(70, -2), "R8,5", end_len=10)
r4 = (44.01, -34.22)
sh.leader(F(-r4[0]-4.25*0.6, r4[1]-4.25*0.8), F(-72, -48), "R4,25", end_len=12)
sh.leader(F(*pol(60, -60)), F(-74, -36), "R60", end_len=9)
# Winkel (von unten gemessen, symmetrisch)
def angdim(half, R, txt, ext_r):
    for sg in (1, -1):
        p = pol(ext_r, half*sg); sh.line([F(*pol(R-3, half*sg)), F(*p)]) if False else None
    a1, a2 = -90-half, -90+half
    pts = [F(R*math.cos(math.radians(t)), R*math.sin(math.radians(t))) for t in np.linspace(a1, a2, 80)]
    sh.line(pts); sh.arrow(pts[0], pts[4]); sh.arrow(pts[-1], pts[-5])
    sh.text(FX, FY-R+1.0, txt, H, ha="center")
for sg in (1, -1):
    for half, rr in ((67.5, 43), (56.25, 60), (51.0, 62), (46.0, 62)):
        sh.line([F(*pol(4, half*sg)), F(*pol(rr, half*sg))])
angdim(67.5, 14, "135°", 0)
angdim(56.25, 22, "113°", 0)
angdim(51.0, 30, "102°", 0)
angdim(46.0, 38, "92°", 0)
# Augenbreite 17 (linkes Auge, quer zur Radialrichtung)
ec = pol(51.5, -67.5); u = (ec[0]/51.5, ec[1]/51.5); n = (u[1], -u[0])
t1 = (ec[0]+8.5*u[0], ec[1]+8.5*u[1]); t2 = (ec[0]-8.5*u[0], ec[1]-8.5*u[1])
off = 16
e1 = (t1[0]+off*n[0], t1[1]+off*n[1]); e2 = (t2[0]+off*n[0], t2[1]+off*n[1])
sh.line([F(*t1), F(t1[0]+(off+2)*n[0], t1[1]+(off+2)*n[1])]); sh.line([F(*t2), F(t2[0]+(off+2)*n[0], t2[1]+(off+2)*n[1])])
sh.line([F(*e1), F(*e2)]); sh.arrow(F(*e1), F(*e2)); sh.arrow(F(*e2), F(*e1))
rot = math.degrees(math.atan2(u[1], u[0])) + 180
tm = ((e1[0]+e2[0])/2 + 1.2*n[0], (e1[1]+e2[1])/2 + 1.2*n[1])
sh.text(*F(*tm), "17", H, rot=rot, ha="center")
# Abwicklung Belag 5.2 (gestreckte Laenge 102, Einlaufschraege 1,5 x 5)
AX, AY = FX-51, FY-92
dd = dict(color="k", lw=TN, dashes=(14, 2.5, 1.5, 2.5, 1.5, 2.5))
sh.ax.plot([AX, AX+102], [AY, AY], **dd)
sh.ax.plot([AX, AX+5, AX+97, AX+102], [AY, AY-1.5, AY-1.5, AY], **dd)
sh.dim((AX, AY), (AX+102, AY), AY-14, "102", "h")
sh.dim((AX+97, AY-1.5), (AX+102, AY), AY-7, "5", "h")
sh.dim((AX+102, AY), (AX+102, AY-1.5), AX+108, "1,5", "v")
sh.text(AX, AY+3, "Abwicklung Belag 5.2", 3.0)

# ---------------- Schnitt A-A ----------------
# Radien von der Achse
for zz, rr, txt in ((-36, 43, "R43"), (-43, 52, "R52"), (-50, 62, "R62")):
    sh.line([S(-9.5 if rr == 43 else -27.5, -rr), S(zz-2, -rr)])
    sh.line([S(zz, 0), S(zz, -rr)]); sh.arrow(S(zz, -rr), S(zz, 0))
    sh.text(*S(zz-1, -rr/2), txt, H, rot=90, ha="center")
sh.line([S(-52, 0), S(-30, 0)])
sh.dim(S(27, -62), S(27, -65), SX+35, "3", "v", ext1=True, ext2=True)
sh.leader(S(-14, -62.2), S(-38, -80), "geklebt", end_len=14)
sh.dim(S(-27, -65), S(27, -65), SY-73, "54", "h")
sh.dim(S(-9, -30), S(9, -30), SY-30, "18", "h", ext1=False, ext2=False)
sh.dim(S(-10, -14), S(10, -14), SY-14, "20|+0,2|+0,1", "h", ext1=False, ext2=False)
sh.dim(S(-17, -11.2), S(17, -11.2), SY+5, "34 −0,1", "h")
sh.dim(S(-18, -21), S(18, -21), SY+12, "36 −0,1", "h")
sh.datum(S(10, -14), (1, 0), "A", length=9)
# Parallelitaet der Nutflaechen (Augen)
sh.datum(S(-10, -24), (-1, 0), "B", length=12)
sh.gdt((SX+34, SY-27.5), "parallel", "0,05", "B")
sh.line([(SX+34, SY-24), S(10.1, -24)]); sh.arrow(S(10.1, -24), S(16, -24))

# ---------------- Oberflaechen ----------------
sh.surf_leader(F(-47.89-2.8, -19.24+2.8), F(-66, 14), "y")
sh.surf_leader(S(-10.1, -15), S(-24, 2), "y") if False else None
sh.surf_leader(S(17.1, -18), S(30, -6), "y")
sh.surf_leader(S(-18.1, -40), S(-30, -55), "y") if False else None
sh.surf_leader(S(-12, -62.1) if False else F(*pol(62.1, -20)), F(-40, -80) if False else F(-50, -74), "x") if False else None

gx, gy = 28, 54
sh.surf_symbol((gx, gy), removal=False, prohibited=True)
sh.text(gx+9, gy+0.5, "(", 7); sh.surf_symbol((gx+15, gy), removal=True); sh.text(gx+24, gy+0.5, ")", 7)
for i, (l, rz) in enumerate((("x", "Rz 63"), ("y", "Rz 16"))):
    xx = gx+36+i*52
    sh.surf_symbol((xx, gy), l); sh.text(xx+12, gy+2, "=", 3.5); sh.surf_symbol((xx+21, gy), text=rz)
sh.edge_symbols(206, 50)
sh.notes(25, 16, guss=True, extra=("5.2 Belag: aufgeklebt",))
sh.titleblock("Fliehgewicht (Pos. 5)", "14.2.5.6", "EN-GJS-700-2 / Belag", "1:1")
sh.save("Pos05_Fliehgewicht.pdf", "prev_p5.png")
print("ok")
