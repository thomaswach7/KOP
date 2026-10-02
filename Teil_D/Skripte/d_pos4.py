import pickle, math
from shapely.geometry import Point, LineString
from dimlib import *
d = pickle.load(open("p4.pkl", "rb"))
sh = Sheet("A3")
SX, SY = 262.0, 166.0
FX, FY = 112.0, 166.0
S = lambda x, r: (SX + x, SY + r)
TS = lambda u, v: (SX + u, SY + v)
TF = lambda a, b: (FX + a, FY + b)

sh.polylines(d["sec_l"], TS)
for p in d["sec_p"]: sh.hatch(p, TS, 45, 2.5)
sh.polylines(d["fv_l"], TF)
sh.cl((SX-6, SY), (SX+35, SY))
for r in (75, -75): sh.cl(S(-4, r), S(16, r))
sh.cl((FX-92, FY), (FX+92, FY)); sh.cl((FX, FY-92), (FX, FY+92))
th = np.linspace(0, 2*np.pi, 400)
sh.ax.plot(FX+75*np.cos(th), FY+75*np.sin(th), color="k", lw=TN, dashes=(14, 3, 1.5, 3))
for k in range(6):
    a = math.radians(90+60*k); c = (FX+75*math.cos(a), FY+75*math.sin(a))
    sh.cl((c[0]-9*math.cos(a), c[1]-9*math.sin(a)), (c[0]+9*math.cos(a), c[1]+9*math.sin(a)))
    sh.cl((c[0]-7*math.sin(a), c[1]+7*math.cos(a)), (c[0]+7*math.sin(a), c[1]-7*math.cos(a)))
for sg in (1, -1):
    y1 = FY+sg*97
    sh.line([(FX, FY+sg*90), (FX, y1)], lw=2*TH)
    sh.line([(FX, y1-sg*2), (FX+8, y1-sg*2)]); sh.arrow((FX+8, y1-sg*2), (FX, y1-sg*2))
    sh.text(FX+10, y1-sg*2-1.75, "A", 5)
sh.text(SX-22, SY+100, "A–A", 5, ha="center")

# ---- Durchmesser ----
sh.dim(S(2, 85), S(2, -85), SX-12, "Ø170", "v")
# Halbmasse in der Bohrung (Halbschnitt): Masslinie ueber die Achse hinaus, ein Pfeil
def halfdim(x, r, txt, top, ty):
    p = S(x, -r); q = S(x, top)
    sh.line([p, q]); sh.arrow(p, q)
    sh.text(S(x, 0)[0]-1.0, SY+ty, txt, H, rot=90, ha="left")
halfdim(1.0, 23, "Ø46H12", 5, -21)
halfdim(5.5, 29, "Ø58H12", 30, 8)
sh.dim(S(29, 42.01), S(29, -42.01), SX+38, "Ø84", "v")
sh.dim(S(19, 62.5), S(19, -62.5), SX+47, "Ø125", "v")
sh.dim(S(17.5, 68), S(17.5, -68), SX+56, "Ø136h6", "v")
# ---- Laengen ----
yb = SY-85
sh.dim(S(29, -42), S(19, -62.5), yb-8, "10", "h")
sh.dim(S(29, -42), S(12, -85), yb-15, "17", "h")
sh.dim(S(29, -42), S(0, -83), yb-22, "29", "h")
sh.dim(S(29, -37.5), S(13, -37.5), SY-6, "16+0,1", "h", ext1=False, ext2=False, tpos=0.5)
sh.dim(S(29, -37.5), S(11, -33), SY-12, "18", "h", ext1=False, tpos=0.5)
sh.line([S(13, -35.6), S(13, -4)]); sh.line([S(11, -32), S(11, -10)])
sh.line([S(29.3, -37.5), S(29.3, -16)]) if False else None
# Senkung
sh.leader(S(4.5, -82.4), (SX-14, SY-102), "Ø15H13 ↧8,6", end_len=26)
# Fase, Radien, Schraege
sh.leader(S(18.3, 67.2), (SX+24, SY+80), "1,5×45°", end_len=19)
sh.leader(S(0.6, 84.4), (SX-8, SY+92), "R2", end_len=8)
c = S(13, 33); tip = S(13-1.414, 33-(-1.414)) if False else S(11.59, 34.41)
sh.leader(S(11.6, -34.4), S(16, -21), "R2", end_len=8)
p0 = S(29, -42.01); R = 8.0
arc = [(p0[0]+R*math.cos(math.radians(t)), p0[1]+R*math.sin(math.radians(t))) for t in np.linspace(0, 4.96, 8)]
sh.line([p0, (p0[0]+R+3, p0[1])]); sh.line([p0, (p0[0]+(R+3)*math.cos(math.radians(4.96)), p0[1]+(R+3)*math.sin(math.radians(4.96)))])
sh.line(arc); sh.arrow(arc[0], (arc[0][0]+0.3, arc[0][1]-3)); sh.arrow(arc[-1], (arc[-1][0]-0.3, arc[-1][1]+3))
sh.line([(arc[0][0]+0.5, arc[0][1]-1), (SX+36, SY-53)]); sh.text(SX+36.5, SY-55.5, "5°", H)

# ---- Einzelheit Z (Filzringnut) 2:1 ----
zc = (5.5, -26.0); zr = 7.5
sh.ax.add_patch(Circle(S(*zc), zr, fill=False, lw=TN, color="k"))
sh.leader((S(*zc)[0]-zr*0.7, S(*zc)[1]-zr*0.7), (SX-14, SY-46), "Z", arrow=False, end_len=5, size=5)
DX, DY, M = 368.0, 118.0, 2.0
TD = lambda u, v: (DX + M*(u - zc[0]), DY + M*(v - zc[1]))
circ = Point(*zc).buffer(zr, 128)
for pl in d["sec_l"]:
    g = LineString([(p[0], p[1]) for p in pl]).intersection(circ) if len(pl) > 1 else None
    if g is None or g.is_empty: continue
    for gg in getattr(g, "geoms", [g]):
        if gg.geom_type == "LineString": sh.line([TD(*p) for p in gg.coords], lw=TH)
for p in d["sec_p"]:
    sh.hatch(p.intersection(circ), lambda u, v: TD(u, v), 45, 1.25)
th = np.linspace(0, 2*np.pi, 200)
sh.ax.plot(DX + M*zr*np.cos(th), DY + M*zr*np.sin(th), color="k", lw=TN)
sh.text(DX, DY+M*zr+24, "Z (2:1)", 5, ha="center") if False else sh.text(DX, DY+M*zr+34, "Z (2:1)", 5, ha="center")
# Masse in der Einzelheit (Nut: x 2,76..8,24 bei r=-23 ; 3,5..7,5 bei r=-29)
sh.dim(TD(3.5, -29), TD(7.5, -29), TD(0, -29-5.5)[1], "4H13", "h", tpos=2.1)
sh.dim(TD(0, -23), TD(7.5, -29), TD(0, -9.5)[1], "7,5", "h")
apex = (5.5, -45.2); Ra = 31.0
fl = [((2.76, -23), (3.5, -29)), ((8.24, -23), (7.5, -29))]
for (p0, p1) in fl:
    dx, dy = p0[0]-p1[0], p0[1]-p1[1]; n = math.hypot(dx, dy)
    sh.line([TD(*p0), TD(p0[0]+dx/n*5.5, p0[1]+dy/n*10.5)])
arc = [TD(apex[0]+Ra*math.cos(math.radians(t)), apex[1]+Ra*math.sin(math.radians(t))) for t in np.linspace(83, 97, 20)]
sh.line(arc); sh.arrow(arc[0], arc[3]); sh.arrow(arc[-1], arc[-4])
sh.text(arc[10][0], arc[10][1]+1.2, "14°", H, ha="center")
# ---- Seitenansicht (Lagerseite) ----
a = math.radians(30)
sh.leader((FX+75*math.cos(a), FY+75*math.sin(a)), (FX+64, FY+96), "Ø150", end_len=12)
b = math.radians(-30)
sh.leader((FX+75*math.cos(b)+4.5*math.cos(b), FY+75*math.sin(b)+4.5*math.sin(b)), (FX+84, FY-92), "6× Ø9H13", end_len=22)
arc = [(FX+80*math.cos(t), FY+80*math.sin(t)) for t in np.radians(np.linspace(210, 270, 60))]
sh.line(arc); sh.arrow(arc[0], arc[4]); sh.arrow(arc[-1], arc[-5])
sh.text(FX+89*math.cos(math.radians(240)), FY+89*math.sin(math.radians(240)), "60°", H, rot=-30, ha="center")
sh.text(FX-86, FY-88, "6× 60° (=360°)", 3.5)
ang = math.radians(45); u = (math.cos(ang), math.sin(ang))
p1, p2 = TF(35*u[0], 35*u[1]), TF(-35*u[0], -35*u[1])
sh.line([p1, p2]); sh.arrow(p1, p2); sh.arrow(p2, p1)
na = (-math.sin(ang), math.cos(ang)); tp = TF(25*u[0]+na[0], 25*u[1]+na[1])
sh.text(tp[0], tp[1], "Ø70", H, rot=45, ha="center")
ang = math.radians(135); u = (math.cos(ang), math.sin(ang))
p1, p2 = TF(37.5*u[0], 37.5*u[1]), TF(-37.5*u[0], -37.5*u[1])
sh.line([p1, p2]); sh.arrow(p1, p2); sh.arrow(p2, p1)
rot = -45; na = (-math.sin(math.radians(rot)), math.cos(math.radians(rot)))
tp = TF(-25*u[0]+na[0], -25*u[1]+na[1]); sh.text(tp[0], tp[1], "Ø75H7", H, rot=rot, ha="center")
le = TF(88*u[0], 88*u[1]); sh.line([p1, le])
sh.datum(le, (u[0], u[1]), "A", length=5)

# ---- Bezug A + Lagetoleranzen ----
sh.gdt((SX+80, SY+92), "trunout", "0,05", "A", leader_to=S(16, 68.1), leader_via=(S(16, 0)[0], SY+95.5), side="left")
sh.gdt((SX+80, SY+78.5), "trunout", "0,05", "A", leader_to=S(12.1, 77), leader_via=(S(12.1, 0)[0]+6, SY+82), side="left")

# ---- Oberflaechen ----
sh.surf_leader(S(25, -37.4), S(20, -33), "z")
sh.surf_leader(S(15.5, 68.1), (SX+28, SY+104), "z")
sh.surf_leader(S(12.1, 81), (SX+40, SY+64), "y")
sh.surf_leader(S(-0.1, 50), (SX-24, SY+62), "x")
sh.surf_leader(S(13.1, -36), S(16, -30), "y") if False else None
sh.surf_leader(S(7, 85.1), (SX+6, SY+104), "x")

# ---- Sammelangaben ----
gx, gy = 28, 54
sh.surf_symbol((gx, gy), removal=False, prohibited=True)
sh.text(gx+9, gy+0.5, "(", 7); sh.surf_symbol((gx+15, gy), removal=True); sh.text(gx+24, gy+0.5, ")", 7)
for i, (l, rz) in enumerate((("x", "Rz 63"), ("y", "Rz 16"), ("z", "Rz 4"))):
    xx = gx+36+i*52
    sh.surf_symbol((xx, gy), l); sh.text(xx+12, gy+2, "=", 3.5); sh.surf_symbol((xx+21, gy), text=rz)
sh.edge_symbols(206, 50)
sh.notes(25, 16, guss=True, freistich="E0,6×0,3", radien="R5")
sh.titleblock("Deckel (Pos. 4)", "14.2.5.5", "EN-GJS-700-2", "1:1")
sh.save("Pos04_Deckel.pdf", "prev_p4.png")
print("ok")
