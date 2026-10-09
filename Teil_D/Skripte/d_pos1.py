"""Einzelteilzeichnung Antriebsnabe (Pos. 1) nach Vorlage 14.2.5.2: gleiche Ansichten, gleiche Lage der Maße.
Lage aus dem Scan (300 dpi, Rahmen 390 x 277 mm) umgerechnet; Geometrie aus dem Kontrollmodell mit Freistichen."""
import pickle, math
from dimlib import *
from shapely.geometry import LineString as _LS
from shapely.ops import unary_union as _uu
import dxfout
ZB = (11.0, 4.0, 2.8, 8.0)               # Zellenbreiten der Toleranzrahmen wie in der Vorlage

d = pickle.load(open("p1_buch.pkl", "rb"))
K = 11.811                                   # Pixel je mm im Scan
def L(px, py=None):                          # linke Bildhaelfte (halbe Aufloesung) -> Blatt-mm
    return (20 + (2*px - 27.5)/K, None if py is None else 287 - (2*py - 7)/K)
def R(px, py=None):                          # rechte Bildhaelfte (ab Pixel 2300)
    return (20 + (2300 + 2*px - 27.5)/K, None if py is None else 287 - (2*py - 7)/K)
X_ = lambda p: p[0]
Y_ = lambda p: p[1]

sh = Sheet("A3")
cx, cy = 156.53, 183.28                      # Mitte Vorderansicht
ox, oy = 267.78, 183.28                      # Schnitt A-A: x = 0 (linke Stirnflaeche), Achse
F = lambda u, v: (cx + u, cy + v)
S = lambda x, r: (ox + x, oy + r)

# ---------------- Geometrie ----------------
sp = _uu(d["sec_p"]).buffer(-0.05)
def weg(pl):
    Ls = _LS(pl)
    if sum(sp.contains(Ls.interpolate(t, normalized=True)) for t in (0.25, 0.5, 0.75)) >= 2: return True
    ys = [p[1] for p in pl]
    return max(ys) - min(ys) < 0.01 and abs(ys[0] - 52) < 0.01        # Naht Auge oben (nur Mittellinie zeigen)
sh.polylines([pl for pl in d["sec_l"] if not weg(pl)], S)
for p in d["sec_p"]: sh.hatch(p, S, 135, 2.5)
sh.polylines(d["fv_l"], F)

# Mittellinien
sh.cl(S(-2.6, 0), S(83.2, 0))
for r in (52, -52): sh.cl(S(34.4, r), S(59.8, r))
sh.cl(F(-43, 0), F(43, 0)); sh.cl(F(0, 64), F(0, -60.8))
for v in (52, -52): sh.cl(F(-12, v), F(12, v))

# Schnittverlauf A-A (Halbschnitt: links waagrecht, unten senkrecht)
TH2 = 2*TH
xa = X_(L(557))
sh.line([(xa, Y_(L(0, 170))), (xa, Y_(L(0, 215)))], lw=TH2)
sh.line([(X_(L(495)), Y_(L(0, 192))), (xa, Y_(L(0, 192)))]); sh.arrow((xa, Y_(L(0, 192))), (X_(L(495)), Y_(L(0, 192))))
sh.text(xa, Y_(L(0, 150)), "A", 5, ha="center")
sh.line([(xa, cy + 7.3), (xa, cy), (X_(L(598)), cy)], lw=TH2)
sh.line([(X_(L(785)), cy), (cx, cy), (cx, cy - 6.6)], lw=TH2)
yb1, yb2, ya = Y_(L(0, 985)), Y_(L(0, 1025)), Y_(L(0, 1003))
sh.line([(cx, yb1), (cx, yb2)], lw=TH2)
sh.line([(X_(L(757)), ya), (cx, ya)]); sh.arrow((cx, ya), (X_(L(757)), ya))
sh.text(cx, Y_(L(0, 1068)), "A", 5, ha="center")
sh.text(*R(122, 213), "A–A", 6, ha="center")

# ---------------- Vorderansicht: Maße ----------------
sh.dim(F(-9, 54), F(9, 54), Y_(L(0, 157)), "18", "h")
# Ø8H8 (Pfeile aussen, Text oberhalb)
x8 = X_(L(943))
sh.dim(F(4.5, 56), F(4.5, 48), x8, "", "v", arrows_out=True)
sh.text(x8 - 1.0, cy + 63.5, "Ø8H8", H, rot=90, ha="center")
tipz = (X_(L(1000)), cy + 48)
sh.line([(x8 + 2, cy + 48), (X_(L(1020)), cy + 48)])
sh.surf_symbol(tipz, "z")
# 104
sh.dim(F(-12, 52), F(-12, -52), X_(L(260)), "104", "v")
# 8JS9 mit Symmetrie
xj = X_(L(363))
sh.dim(F(-18.3, 4), F(-18.3, -4), xj, "", "v", arrows_out=True)
sh.text(xj - 1.0, cy + 12.4, "8JS9", H, rot=90, ha="center")
sh.line([(xj, cy + 11), (xj, cy + 25.6)])
sh.surf_symbol((xj, cy + 25.6), "y", rot=90)
yg = Y_(L(0, 825))
sh.line([(xj, cy - 11), (xj, yg + 3.5), (X_(L(388)), yg + 3.5)])
sh.gdt((X_(L(388)), yg), "sym", "0,02", "A", zellen=ZB)
# 79 (Abstand der Fussflaechen)
sh.dim(F(9.5, 39.5), F(9.5, -39.5), X_(L(1122)), "79", "v")
# R9 (Rundung Arm/Koerper)
cR = (-18.0, -43.96); dR = (math.cos(math.radians(33.9)), math.sin(math.radians(33.9)))
tip = F(cR[0] + 9*dR[0], cR[1] + 9*dR[1]); st = (tip[0] - 19*dR[0], tip[1] - 19*dR[1])
sh.line([st, tip]); sh.arrow(tip, st)
sh.text(st[0] + 3*dR[0] - 0.9*dR[1], st[1] + 3*dR[1] + 0.9*dR[0], "R9", H, rot=33.9)
# Ø30H7 mit Bezug A, Oberflaeche z an der Bohrung
y30 = Y_(L(0, 1216))
sh.dim(F(-15, 0), F(15, 0), y30, "Ø30H7", "h")
sh.datum(F(15, 0)[:1] + (y30,), (1, 0), "A", length=10.7)
sh.surf_symbol((cx + 15, Y_(L(0, 1148))), "z", rot=90)
# 33,3 +0,2 und Oberflaeche x am Nutgrund
y33 = Y_(L(0, 1289))
sh.dim(F(-18.3, -4), F(15, 0), y33, "33,3 +0,2", "h")
yx = Y_(L(0, 1380))
sh.line([(cx - 18.3, y33 - 2), (cx - 18.3, yx - 1.5)])
sh.line([(cx - 18.3, yx), (X_(L(870)), yx)])
sh.surf_symbol((X_(L(770)), yx), "x")

# ---------------- Schnitt A-A: Maße ----------------
sh.dim(S(0, 22.5), S(81, 22.5), Y_(R(0, 92)), "81", "h")
y20 = Y_(R(0, 185))
sh.dim(S(37, 39.5), S(57, 39.5), y20, "20", "h")
sh.dim(S(57, 39.5), S(81, 22.5), y20, "24", "h")
# Gesamtrundlauf linker Lagersitz + Oberflaeche z
xr = X_(R(357))
sh.gdt((X_(R(48)), Y_(R(0, 417))), "trunout", "0,05", "A", leader_to=(xr, oy + 22.5),
       leader_via=(xr, Y_(R(0, 417)) + 3.5), side="right", zellen=ZB)
sh.surf_symbol((X_(R(395)), oy + 22.5), "z")
# Ø51, Ø45k6 links mit Bezug B
sh.dim(S(29, 25.5), S(29, -25.5), X_(R(212)), "Ø51", "v")
x45 = X_(R(285))
sh.dim(S(0, 22.5), S(0, -22.5), x45, "Ø45k6", "v")
sh.datum((x45, oy - 22.5), (0, -1), "B", length=(oy - 22.5) - Y_(R(0, 836)) - 3.5)
# Ø45k6 rechts mit Koaxialitaet
x45r = X_(R(889))
sh.dim(S(81, 22.5), S(81, -22.5), x45r, "Ø45k6", "v")
yk = Y_(R(0, 380))
sh.gdt((X_(R(925)), yk), "coax", "Ø0,05", "B", leader_to=(x45r, oy + 22.5), leader_via=(x45r, yk + 3.5), zellen=ZB)
# Oberflaeche z rechte Stirnflaeche (an der Masshilfslinie)
tz = (ox + 81, Y_(R(0, 315))); kn = R(855, 267)
sh.line([tz, kn, (X_(R(958)), kn[1])]); sh.arrow(tz, kn)
sh.surf_symbol((X_(R(895)), kn[1]), "z")
# Gesamtplanlauf beide Armflaechen
yp = Y_(R(0, 962)); wfr = ZB[0] + ZB[1] + 4*ZB[2] + ZB[3]
sh.gdt((X_(R(295)) - wfr, yp - 3.5), "trunout", "0,05", "A", leader_to=(ox + 38.5, yp), side="right", zellen=ZB)
sh.gdt((X_(R(843)), yp - 3.5), "trunout", "0,05", "A", leader_to=(ox + 55.5, yp), side="left", zellen=ZB)
# Laengen unten
y1 = Y_(R(0, 1157))
sh.dim(S(38.5, -61), S(55.5, -61), y1, "17|−0,1|−0,2", "h")
sh.dim(S(55.5, -61), S(81, -22.5), y1, "25,5", "h")
sh.line([(X_(R(260)), y1), (ox + 38.5, y1)])
sh.surf_symbol((X_(R(282)), y1), "y")
y2 = Y_(R(0, 1268))
sh.dim(S(29, -25.5), S(65, -25.5), y2, "36 −0,1", "h")
sh.dim(S(65, -25.5), S(81, -22.5), y2, "16", "h")
sh.line([(X_(R(345)), y2), (ox + 29, y2)])
sh.surf_symbol((X_(R(368)), y2), "y")

# ---------------- Oberflaechen allgemein, Kanten, Hinweise ----------------
gx, gy = X_(L(65)), Y_(L(0, 1365))
sh.surf_symbol((gx, gy), removal=False, prohibited=True)
sh.text(gx + 9, gy + 0.5, "(", 7); sh.surf_symbol((gx + 15, gy), removal=True); sh.text(gx + 24, gy + 0.5, ")", 7)
for row, (l, rz) in enumerate((("x", "Rz 63"), ("y", "Rz 16"), ("z", "Rz 4"))):
    yy = Y_(L(0, 1470 + 70*row)); xx = X_(L(62))
    sh.surf_symbol((xx, yy), l); sh.text(xx + 18, yy + 2, "=", 3.5); sh.surf_symbol((xx + 28, yy), text=rz)
sh.edge_symbols(X_(R(135)), Y_(R(0, 1330)))
for i, s in enumerate(["Nicht bemaßte Freistiche DIN 509 – E0,6×0,3", "Nicht bemaßte Radien R2",
                       "Oberflächen nach DIN EN ISO 1302", "Werkstückkanten nach DIN ISO 13715",
                       "Allgemeintoleranzen ISO 2768-mK", "Gusstoleranzen DIN 1686 – GTB 18"]):
    sh.text(108, 41.2 - i*5.66, s, 3.2)
sh.titleblock("Antriebsnabe (Pos. 1)", "14.2.5.2", "EN-GJS-700-2", "1:1")
print(dxfout.export(sh, "Pos01_Antriebsnabe.dxf"))
sh.save("Pos01_Antriebsnabe.pdf", "prev_p1.png", dpi=150)
print("ok")
