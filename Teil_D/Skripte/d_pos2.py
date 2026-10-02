import pickle, math
from dimlib import *
d = pickle.load(open("p2.pkl", "rb"))
sh = Sheet("A3")
SX, SY = 242.0, 166.0          # x_lok = 0 (Nabenende) / Achse der Schnittansicht
FX, FY = 112.0, 166.0          # Mitte Ansicht von der Lagerseite
S = lambda x, r: (SX + x, SY + r)
TS = lambda u, v: (SX + u, SY + v)
TF = lambda a, b: (FX + a, FY + b)

# ---------------- Ansichten ----------------
sh.polylines(d["sec_l"], TS)
for p in d["sec_p"]: sh.hatch(p, TS, 45, 2.5)
sh.polylines(d["fv_l"], TF)
sh.cl((SX-6, SY), (SX+78, SY))
for r in (75, -75): sh.cl(S(40, r), S(58, r))
sh.cl((FX-92, FY), (FX+92, FY)); sh.cl((FX, FY-92), (FX, FY+92))
th = np.linspace(0, 2*np.pi, 400)
sh.ax.plot(FX+75*np.cos(th), FY+75*np.sin(th), color="k", lw=TN, dashes=(14, 3, 1.5, 3))
for k in range(6):
    a = math.radians(90+60*k); c = (FX+75*math.cos(a), FY+75*math.sin(a))
    sh.cl((c[0]-9*math.cos(a), c[1]-9*math.sin(a)), (c[0]+9*math.cos(a), c[1]+9*math.sin(a)))
    sh.cl((c[0]-7*math.sin(a), c[1]+7*math.cos(a)), (c[0]+7*math.sin(a), c[1]-7*math.cos(a)))
# Schnittverlauf A-A
for sg in (1, -1):
    y1 = FY+sg*97
    sh.line([(FX, FY+sg*90), (FX, y1)], lw=2*TH)
    sh.line([(FX, y1-sg*2), (FX+8, y1-sg*2)]); sh.arrow((FX+8, y1-sg*2), (FX, y1-sg*2))
    sh.text(FX+10, y1-sg*2-1.75, "A", 5)
sh.text(SX-22, SY+100, "A–A", 5, ha="center")

# ---------------- Schnitt: Durchmesser ----------------
sh.dim(S(0, 15), S(0, -15), SX-9, "Ø30H7", "v")
sh.dim(S(20, 25), S(20, -25), SX-18, "Ø50", "v")
sh.dim(S(45, 85), S(45, -85), SX-27, "Ø170", "v")
sh.dim(S(72, 42.63), S(72, -42.63), SX+81, "Ø85,3", "v")
sh.dim(S(62, 62.5), S(62, -62.5), SX+90, "Ø125", "v")
sh.dim(S(60.5, 68), S(60.5, -68), SX+99, "Ø136h6", "v")
# ---------------- Schnitt: Laengen ----------------
yb = SY-85
sh.dim(S(72, -42.6), S(62, -62.5), yb-8, "10", "h")
sh.dim(S(72, -42.6), S(55, -85), yb-15, "17", "h")
sh.dim(S(72, -42.6), S(43, -83), yb-22, "29", "h")
sh.dim(S(72, -42.6), S(0, -23), yb-29, "72", "h")
sh.dim(S(72, 15), S(56, 35), SY+9.5, "16+0,1", "h", ext1=False, tpos=0.42)
sh.dim(S(72, 15), S(54, 15), SY+3.5, "18", "h", ext1=False)
# Senkung (obere Bohrung)
sh.leader(S(47, 82.4), (SX+20, SY+96), "Ø15H13 ↧8,6", end_len=26)
# Fasen / Radien / Schraege
sh.leader(S(61.3, 67.2), (S(66, 0)[0]+4, SY+76), "1,5×45°", end_len=19)
sh.leader(S(43.6, -84.4), (S(36, 0)[0], SY-94) if False else (SX+30, SY-92), "R2", end_len=8)
sh.leader(S(0.6, -24.4), (SX-4, SY-40), "R2", end_len=8)
c = S(33, -35); tip = S(33+7.07, -35+7.07)
sh.line([tip, (c[0]-4, c[1]-4)]); sh.arrow(tip, c)
sh.line([(c[0]-4, c[1]-4), (c[0]-14, c[1]-4)]); sh.text(c[0]-13, c[1]-3.1, "R10", H)
p0 = S(72, -42.63)
R = 8.0
arc = [(p0[0]+R*math.cos(math.radians(t)), p0[1]+R*math.sin(math.radians(t))) for t in np.linspace(0, 4.96, 8)]
sh.line([p0, (p0[0]+R+3, p0[1])]); sh.line([p0, (p0[0]+(R+3)*math.cos(math.radians(4.96)), p0[1]+(R+3)*math.sin(math.radians(4.96)))])
sh.line(arc)
sh.arrow(arc[0], (arc[0][0]+0.3, arc[0][1]-3)); sh.arrow(arc[-1], (arc[-1][0]-0.3, arc[-1][1]+3))
sh.line([(arc[0][0]+0.5, arc[0][1]-1), (SX+79, SY-53)]); sh.text(SX+79.5, SY-55.5, "5°", H)
# ---------------- Ansicht von der Lagerseite ----------------
# Passfedernut (liegt links, a = -z)
sh.dim(TF(-15.2, 4), TF(-15.2, -4), FX-27, "8JS9", "v")
sh.dim(TF(15, 0), TF(-18.3, 4), FY+24, "33,3+0,2", "h")
# Lochkreis + Bohrungen
a = math.radians(30)
sh.leader((FX+75*math.cos(a), FY+75*math.sin(a)), (FX+64, FY+96), "Ø150", arrow=True, end_len=12)
b = math.radians(-30); hp = (FX+75*math.cos(b)-4.5*math.cos(b), FY+75*math.sin(b)-4.5*math.sin(b))
sh.leader((FX+75*math.cos(b)+4.5*math.cos(b+math.pi*0), FY+75*math.sin(b)+4.5*math.sin(b)), (FX+84, FY-92), "6× Ø9H13", end_len=22)
# Ø75H7 schraeg (135 Grad) mit Koaxialitaet, Ø70 schraeg (45 Grad)
for angd, rr, txt, tdist in ((135, 37.5, "Ø75H7", -25.0), (45, 35, "Ø70", 25)):
    ang = math.radians(angd); u = (math.cos(ang), math.sin(ang)); n = (-u[1], u[0])
    p1 = TF(rr*u[0], rr*u[1]); p2 = TF(-rr*u[0], -rr*u[1])
    sh.line([p1, p2]); sh.arrow(p1, p2); sh.arrow(p2, p1)
    rot = angd if angd < 90 else angd-180
    na = (-math.sin(math.radians(rot)), math.cos(math.radians(rot)))
    tp = TF(tdist*u[0] + 1.0*na[0], tdist*u[1] + 1.0*na[1])
    sh.text(tp[0], tp[1], txt, H, rot=rot, ha="center")
ang = math.radians(135); u = (math.cos(ang), math.sin(ang))
p1 = TF(37.5*u[0], 37.5*u[1]); le = TF(96*u[0], 96*u[1])
sh.line([p1, le]); sh.arrow(p1, le)
sh.gdt((le[0]-6, le[1]), "coax", "Ø0,05", "A", leader_to=None)
sh.line([le, (le[0]-0.1, le[1]+0.01)])
# ---------------- Bezug A + Lagetoleranzen ----------------
sh.datum((SX-9, SY-15), (0, -1), "A", length=9)
sh.gdt((SX+112, SY+92), "trunout", "0,05", "A", leader_to=S(59, 68.1), leader_via=(S(59, 0)[0], SY+95.5), side="left")
sh.gdt((SX+112, SY+78.5), "trunout", "0,05", "A", leader_to=S(55.1, 82), leader_via=None, side="left")

# ---------------- Oberflaechen ----------------
sh.surf_leader(S(30, 15.1), (S(28, 0)[0], SY+31), "y")
sh.surf_leader(S(66, 37.4), S(62.5, 22), "z")
sh.surf_leader(S(57.6, 68.1), (SX+60, SY+100), "z")
sh.surf_leader(S(55.1, 72), (S(70, 0)[0]+18, SY+66), "y")
sh.surf_leader(S(-0.1, 20), (SX-14, SY+40), "x")
sh.surf_leader(S(44.5, 85.1), (SX+33, SY+103), "x")

# ---------------- Sammelangaben ----------------
gx, gy = 28, 54
sh.surf_symbol((gx, gy), removal=False, prohibited=True)
sh.text(gx+9, gy+0.5, "(", 7); sh.surf_symbol((gx+15, gy), removal=True); sh.text(gx+24, gy+0.5, ")", 7)
for i, (l, rz) in enumerate((("x", "Rz 63"), ("y", "Rz 16"), ("z", "Rz 4"))):
    xx = gx+36+i*52
    sh.surf_symbol((xx, gy), l); sh.text(xx+12, gy+2, "=", 3.5); sh.surf_symbol((xx+21, gy), text=rz)
sh.edge_symbols(206, 50)
sh.notes(25, 16, guss=True, freistich="E0,6×0,3", radien="R5")
sh.titleblock("Abtriebsnabe (Pos. 2)", "14.2.5.3", "EN-GJS-700-2", "1:1")
sh.save("Pos02_Abtriebsnabe.pdf", "prev_p2.png")
print("ok")
