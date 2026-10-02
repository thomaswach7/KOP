import pickle, math
from dimlib import *
d = pickle.load(open("p3.pkl", "rb"))
sh = Sheet("A4")
SX, SY = 72.0, 170.0
S = lambda x, r: (SX + x, SY + r)
TS = lambda u, v: (SX + u, SY + v)
sh.polylines(d["sec_l"], TS)
for p in d["sec_p"]: sh.hatch(p, TS, 45, 2.5)
# Gewinde im Schnitt: Nenn-Ø schmal, Gewindeende breit
for x0, x1 in ((0, 20), (70, 50)):
    for dz in (4, -4): sh.line([S(x0, -75+dz), S(x1, -75+dz)], lw=TN)
    sh.line([S(x1, -79), S(x1, -71)], lw=TH)
sh.cl((SX-6, SY), (SX+76, SY))
sh.cl(S(-4, -75), S(31, -75)); sh.cl(S(39, -75), S(74, -75))

# Durchmesser
sh.dim(S(0, 68), S(0, -68), SX-9, "Ø136H7", "v")
sh.datum((SX-9, SY-68), (0, -1), "A", length=5)
sh.dim(S(10, 85), S(10, -85), SX-18, "Ø170", "v")
sh.line([(SX+71, SY-75), (SX+82, SY-75)])
sh.line([(SX+80, SY-75), (SX+80, SY+12)]); sh.arrow((SX+80, SY-75), (SX+80, SY+12))
sh.text(SX+79, SY-10, "Ø150", H, rot=90, ha="left")
# Laengen
sh.dim(S(0, 85), S(70, 85), SY+93, "70|+0,2|+0,1", "h")
sh.dim(S(70, -79), S(50, -79), SY-93, "20", "h")
sh.dim(S(70, -79), S(44, -78.4), SY-100, "26", "h", ext1=False)
sh.leader(S(10, -79.2), (SX+30, SY-110), "6× M8 ↧20 beidseitig", end_len=36)
sh.leader(S(0.5, -68.5), (SX+14, SY-56), "1×45°", end_len=12)
# Lagetoleranzen
sh.gdt((SX+72.5, SY+100), "trunout", "0,05", "A")
sh.line([(SX+76, SY+100), (SX+76, SY+81), (SX+70.1, SY+81)]); sh.arrow((SX+70.1, SY+81), (SX+76, SY+81))
sh.gdt((SX-8.5, SY+100), "parallel", "0,05", "B")
sh.line([(SX-5, SY+100), (SX-5, SY+78), (SX-0.1, SY+78)]); sh.arrow((SX-0.1, SY+78), (SX-5, SY+78))
sh.datum((SX+70, SY+72), (1, 0), "B", length=3)
# Oberflaechen
sh.surf_leader(S(35, -67.9), S(30, -40), "z")
sh.surf_leader(S(-0.1, -82.5), (SX-6, SY-100), "y")
sh.surf_leader(S(70.1, 60), (SX+86, SY+50), "y")
# Sammelangabe (rechts)
gx, gy = 160, 192
sh.surf_symbol((gx, gy), "x"); sh.text(gx+12, gy+0.5, "(", 7); sh.surf_symbol((gx+18, gy), removal=True); sh.text(gx+27, gy+0.5, ")", 7)
for i, (l, rz) in enumerate((("x", "Rz 63"), ("y", "Rz 16"), ("z", "Rz 4"))):
    yy = gy-18-i*15
    sh.surf_symbol((gx, yy), l); sh.text(gx+12, yy+2, "=", 3.5); sh.surf_symbol((gx+21, yy), text=rz)
sh.edge_symbols(162, 112)
sh.text(23, 55.2, "Oberflächen DIN EN ISO 1302, Werkstückkanten DIN ISO 13715", 3.0)
sh.text(23, 50, "Allgemeintoleranzen ISO 2768-mK, Passungssystem Einheitsbohrung", 3.0)
sh.titleblock("Gehäuse (Pos. 3)", "14.2.5.4", "E295", "1:1")
sh.save("Pos03_Gehaeuse.pdf", "prev_p3.png")
print("ok")
