"""Einzelteilzeichnung Abtriebsnabe (Pos. 2), A3 1:1, im Stil der Vorlagen 14.2.5.x (Schriftfeld wie 14.2.5.2).
Im Datensatz gibt es keine Zeichnung 14.2.5.3 -> Geometrie aus dem Kontrollmodell (replay.pos2, wie Modellbaum-Anleitung,
Masse aus Teil_A/CAD/Einzelteile_alle/Pos02_Abtriebsnabe.stp geprueft). Toleranzen, Oberflaechen und Form-/Lagetoleranzen nach Angabe Teil D.
Ansichten aus gen_p2.py (p2.pkl): Vorderansicht von der Flanschseite, Schnitt A-A durch zwei Bohrungen, Nabe links."""
import pickle, math
from dimlib import *
from shapely.geometry import LineString as LS
import dxfout_geo as dxfout, dimlib
dimlib.FONT = dict(family="Liberation Sans")       # metrisch gleich Arial (Schrift der Vorlagen)
def _rahmen(self):                                   # Vorlage: nur Rahmenlinie, keine Mittenmarken
    self.ax.add_patch(plt.Rectangle((20, 10), self.W-30, self.Hh-20, fill=False, lw=TH, color="k"))
Sheet.frame = _rahmen
ZB = (11.0, 4.0, 2.8, 8.0)                           # Zellenbreiten der Toleranzrahmen wie in der Vorlage
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
def tw(t, h=H):                                      # Textbreite in mm (gleiche Schrift wie sh.text)
    return TextPath((0, 0), t, size=h*MM/0.72, prop=FontProperties(**dimlib.FONT)).get_extents().x1*25.4/72

d = pickle.load(open("p2.pkl", "rb"))
sh = Sheet("A3")
cx, cy = 128.0, 180.0                                # Mitte Vorderansicht
o = 262.0                                            # Schnitt: x = 0 (Nabenstirnflaeche), Achse bei cy
F = lambda u, v: (cx + u, cy + v)
S = lambda x, z: (o + x, cy + z)

# ---------------- Ansichten ----------------
innen = [p.buffer(-0.05) for p in d["sec_p"]]       # Linienstuecke im Inneren einer Schnittflaeche weglassen
def sichtbar(pls):
    out = []
    for pl in pls:
        g = LS(pl)
        for q in innen:
            if not q.is_empty and g.intersects(q): g = g.difference(q)
            if g.is_empty: break
        for t in getattr(g, "geoms", [g]):
            if t.geom_type == "LineString" and t.length > 0.05: out.append(list(t.coords))
    return out
sh.polylines(sichtbar(d["sec_l"]), S)
for p in d["sec_p"]: sh.hatch(p, S, 45, 2.5)
sh.polylines(d["fv_l"], F)

# Mittellinien
sh.cl(S(-4, 0), S(76, 0))
for z in (75, -75): sh.cl(S(39, z), S(59, z))
sh.cl(F(-92, 0), F(92, 0)); sh.cl(F(0, -92), F(0, 92))
th = np.linspace(0, 2*math.pi, 400)
sh.ax.plot(cx + 75*np.cos(th), cy + 75*np.sin(th), color="k", lw=TN, dashes=(14, 3, 1.5, 3))
for k in range(6):                                   # Bohrungen bei 30 + 60 k Grad
    a = math.radians(30 + 60*k); c = F(75*math.cos(a), 75*math.sin(a))
    sh.cl((c[0] - 8*math.cos(a), c[1] - 8*math.sin(a)), (c[0] + 8*math.cos(a), c[1] + 8*math.sin(a)))

# Schnittverlauf A-A: senkrecht durch die Bohrungen oben/unten, Blick nach +Y (Pfeile nach rechts)
for sg in (1, -1):
    y0, y1 = cy + sg*91, cy + sg*97
    sh.line([(cx, y0), (cx, y1)], lw=2*TH)
    ya = y1 - sg*1.5
    sh.line([(cx - 0.3, ya), (cx + 8, ya)]); sh.arrow((cx + 8, ya), (cx - 0.3, ya))
    sh.text(cx + 9.5, ya - 2.5 if sg > 0 else ya - 2.5, "A", 5)
sh.text(*S(36, 99), "A-A", 5, ha="center")

def tiefe(x, y, h=3.5):
    """Tiefensymbol (ISO 129): senkrechter Strich mit Pfeil nach unten auf kurzer Grundlinie."""
    sh.line([(x, y + 0.72*h), (x, y + 0.15*h)], lw=TN)
    sh.ax.add_patch(MPoly([(x, y), (x - 0.55, y + 0.35*h), (x + 0.55, y + 0.35*h)], closed=True, color="k", lw=0))
    sh.line([(x - 0.9, y), (x + 0.9, y)], lw=TN)

# ---------------- Schnitt A-A: Durchmesser ----------------
# links (Nabe): 8JS9 (Passfedernut, sichtbare Nutflanken), O50
x8 = o - 8
sh.dim(S(0, 4), S(0, -4), x8, "", "v", arrows_out=True)
sh.text(x8 - 1.0, cy - 16.5, "8JS9", H, rot=90, ha="center")
sh.dim(S(2, 25), S(2, -25), o - 16, "Ø50", "v")
# rechts: O85,3 (Rohrende), O125, O136h6, O170 (kleinster innen)
sh.dim(S(72, 42.63), S(72, -42.63), o + 86, "Ø85,3", "v")
sh.dim(S(62, 62.5), S(62, -62.5), o + 94, "Ø125", "v")
sh.dim(S(59, 68), S(59, -68), o + 102, "Ø136h6", "v")
sh.dim(S(55, 85), S(55, -85), o + 110, "Ø170", "v")

# ---------------- Schnitt A-A: Laengen ----------------
sh.dim(S(55, -85), S(62, -66.5), cy - 93, "7", "h")
sh.dim(S(0, -23), S(43, -83), cy - 100, "43", "h")
sh.dim(S(0, -23), S(55, -85), cy - 107, "55", "h")
sh.dim(S(0, -23), S(72, -42.63), cy - 114, "72", "h")
# Lagersitz 16 und Bohrungsende 18 (Masse in der Bohrung wie Vorlage Deckel)
sh.line([S(72, 36.5), S(72, 22.0)]); sh.line([S(56, 34.0), S(56, 28.0)])
sh.dim(S(56, 30), S(72, 30), cy + 30, "16", "h", ext1=False, ext2=False)
sh.dim(S(54, 24), S(72, 24), cy + 24, "18", "h", ext1=False, ext2=False)

# ---------------- Schnitt A-A: Senkung, Radien, Fase, Schraege ----------------
tip = S(43, 82.5); kn = S(25, 97)                     # Pfeil auf die Senkungskante (von aussen)
w1, w2 = tw("Ø15H13"), tw("8,6"); L = 1 + w1 + 1.0 + 1.8 + 1.0 + w2 + 1
sh.line([tip, kn, (kn[0] - L, kn[1])]); sh.arrow(tip, kn)
x0 = kn[0] - L + 1
sh.text(x0, kn[1] + 0.9, "Ø15H13", H); tiefe(x0 + w1 + 1.9, kn[1] + 0.9); sh.text(x0 + w1 + 3.8, kn[1] + 0.9, "8,6", H)
# R10 Nabe/Flansch (Rundungsmitte (33, 35))
tipR = S(33 + 10*math.cos(math.radians(-45)), 35 + 10*math.sin(math.radians(-45)))
sh.leader(tipR, S(26, 46), "R10", end_len=8)
# R5 in der Ausdrehung (beide Innenecken)
knR = S(68, 53.3)                                    # beide R5 (Ausdrehung / Rohransatz) mit gemeinsamer Hinweislinie
for ziel in ((56.46, 61.04), (56.46, 45.58)):
    b = S(*ziel); sh.line([knR, b]); sh.arrow(b, knR)
sh.line([knR, (knR[0] + tw("R5") + 2, knR[1])]); sh.text(knR[0] + 1, knR[1] + 0.9, "R5", H)
# Fase 1,5x45 am Zentrierring (Hinweislinie rechts vom Rundlauf-Pfeil)
tipF = S(61.25, 67.25); knF = S(62.5, 81.0)
sh.line([tipF, knF, (knF[0] + 17, knF[1])]); sh.arrow(tipF, knF)
sh.text(knF[0] + 1.0, knF[1] + 0.9, "1,5×45°", H)
# Aushebeschraege 5 Grad am Lagerrohr (unten, Bezug: Masshilfslinie O85,3)
p0 = S(72, -42.63); R = 8.0
sh.line([p0, (p0[0] + (R + 3)*math.cos(math.radians(5)), p0[1] + (R + 3)*math.sin(math.radians(5)))])
arc = [(p0[0] + R*math.cos(math.radians(t)), p0[1] + R*math.sin(math.radians(t))) for t in np.linspace(-12, 17, 30)]
sh.line(arc)
a0 = (p0[0] + R, p0[1]); a5 = (p0[0] + R*math.cos(math.radians(5)), p0[1] + R*math.sin(math.radians(5)))
sh.arrow(a0, arc[0]); sh.arrow(a5, arc[-1])
sh.line([arc[0], (o + 81.5, cy - 56)]); sh.text(o + 82.0, cy - 58.5, "5°", H)

# ---------------- Bezug, Form- und Lagetoleranzen ----------------
# Gesamtrundlauf O136h6 (Gehaeuseaufnahme) zu A
sh.gdt((o + 91.5, cy + 93), "trunout", "0,05", "A", leader_to=(o + 97, cy + 68), side="bottom", zellen=ZB)   # Pfeil auf Masshilfslinie O136
# Gesamtplanlauf Anlageflaeche Gehaeuse (x = 55) zu A: Pfeil auf die Masshilfslinie unten
sh.line([S(55, -110), (o + 55, 57.0)])
sh.gdt((o + 60, 55.0), "trunout", "0,05", "A", leader_to=(o + 55, 58.5), side="left", zellen=ZB)

# ---------------- Vorderansicht: Masse ----------------
# O75H7 mit Koaxialitaet (Masslinie steil, damit sie die Masshilfslinien unten nicht kreuzt)
al = math.radians(70); u = (math.cos(al), math.sin(al))
p1, p2 = F(37.5*u[0], 37.5*u[1]), F(-37.5*u[0], -37.5*u[1])
sh.line([p1, p2]); sh.arrow(p1, p2); sh.arrow(p2, p1)
tp = F(-25*u[0] - 1.2*u[1], -25*u[1] + 1.2*u[0]); sh.text(tp[0], tp[1], "Ø75H7", H, rot=70, ha="center")
le = F(101*u[0], 101*u[1]); sh.line([p1, le])
sh.gdt((le[0], le[1] - 3.5), "coax", "Ø0,05", "A", zellen=ZB)
# O70 (Schulter)
al = math.radians(112); u = (math.cos(al), math.sin(al))
p1, p2 = F(35*u[0], 35*u[1]), F(-35*u[0], -35*u[1])
sh.line([p1, p2]); sh.arrow(p1, p2); sh.arrow(p2, p1)
tp = F(22*u[0] + 1.0*u[1], 22*u[1] - 1.0*u[0]); sh.text(tp[0], tp[1], "Ø70", H, rot=112 - 180, ha="center")
# Bohrbild
a = math.radians(-30); hc = (75*math.cos(a), 75*math.sin(a)); kn = (86, -90)   # Hinweislinie zielt auf Bohrungsmitte
dl = math.hypot(kn[0] - hc[0], kn[1] - hc[1]); dv = ((kn[0] - hc[0])/dl, (kn[1] - hc[1])/dl)
sh.leader(F(hc[0] + 4.5*dv[0], hc[1] + 4.5*dv[1]), F(*kn), "6× Ø9H13", end_len=tw("6× Ø9H13") + 2)
a = math.radians(50)                                  # Lochkreis: radial, zwischen zwei Bohrungen
sh.leader(F(75*math.cos(a), 75*math.sin(a)), F(96*math.cos(a), 96*math.sin(a)), "Ø150", end_len=tw("Ø150") + 2)
arc = [F(80*math.cos(t), 80*math.sin(t)) for t in np.radians(np.linspace(90, 150, 60))]
sh.line(arc); sh.arrow(arc[0], arc[4]); sh.arrow(arc[-1], arc[-5])
tp = F(87*math.cos(math.radians(120)), 87*math.sin(math.radians(120))); sh.text(tp[0], tp[1], "6× 60° (=360°)", H, rot=30, ha="center")
# Bohrung O30H7 mit Bezug A und Nuttiefe 33,3 (Masse unter der Ansicht wie Vorlage 14.2.5.2)
y30, y33 = cy - 104, cy - 111
sh.dim(F(-15, 0), F(15, 0), y30, "Ø30H7", "h")
sh.datum((cx + 15, y30), (1, 0), "A", length=10.7)
sh.dim(F(18.3, -4), F(-15, 0), y33, "33,3 +0,2", "h")

# ---------------- Oberflaechen ----------------
sh.surf_symbol((cx - 15, cy - 96), "z", rot=90)                       # Bohrung O30H7 (an der Masshilfslinie)
sh.surf_symbol(S(66, -37.5), "z")                                     # Lagersitz O75H7
sh.surf_symbol(S(82, 68), "z")                                        # O136h6 (an der Masshilfslinie)
sh.line([S(55, 86), S(55, 95)]); sh.surf_symbol(S(55, 90.5), "z", rot=90)   # Anlageflaeche Gehaeuse x = 55
sh.surf_symbol(S(0, 19), "y", rot=90)                                 # Stirnflaeche Nabe

# ---------------- Oberflaechen allgemein, Kanten, Hinweise (wie Pos01) ----------------
SZ = 1.13
sh.surf_symbol((29.2, 55.95), removal=False, prohibited=True, size=SZ)
sh.text(38.4, 57.2, "(", 7.9); sh.surf_symbol((43.8, 55.95), removal=True, size=SZ); sh.text(49.7, 57.2, ")", 7.9)
for (l, rz), yt in zip((("x", "Rz 63"), ("y", "Rz 16"), ("z", "Rz 4")), (38.0, 26.06, 14.04)):
    sh.surf_symbol((29.2, yt), l, size=SZ, th=3.5, bar=45.9 - 29.2, tpos=(8.5, 6.5))
    sh.text(50.2, yt + 4.5, "=", 3.5)
    sh.surf_symbol((59.2, yt), text=rz, size=SZ, th=3.5, bar=81.0 - 59.2, tpos=(8.9, 6.5))
sh.edge_symbols(196, 61)
for yb, s in zip((41.0, 35.5, 30.25, 24.66, 18.82, 12.81), ["Nicht bemaßte Freistiche DIN 509 – E0,6×0,3", "Nicht bemaßte Radien R2",
                       "Oberflächen nach DIN EN ISO 1302", "Werkstückkanten nach DIN ISO 13715",
                       "Allgemeintoleranzen ISO 2768-mK", "Gusstoleranzen DIN 1686 – GTB 18"]):
    sh.text(110.0, yb, s, 3.5)

# ---------------- Schriftfeld wie Vorlage 14.2.5.2 ----------------
def lin(a, b): sh.line([a, b], lw=TH)
lin((229.97, 45.95), (410, 45.95)); lin((229.97, 37.0), (410, 37.0))
lin((229.97, 10), (229.97, 45.95))
for x in (254.99, 342.0, 385.0): lin((x, 37.0), (x, 45.95))
lin((299.0, 10), (299.0, 45.95)); lin((359.0, 10), (359.0, 37.0))
lin((299.0, 27.96), (410, 27.96)); lin((359.0, 19.0), (410, 19.0))
for x in (366.0, 391.0, 401.0): lin((x, 10), (x, 19.0))
T = lambda x, y, t, h=2.5, **k: sh.text(x, y, t, h, **k)
T(231.17, 42.37, "Verantw. Abt.")
T(256.25, 42.37, "Technische Referenz"); T(256.42, 38.34, "Projekt Fliehkraftkupplung")
T(300.34, 42.37, "Erstellt durch"); T(343.25, 42.37, "Genehmigt von")
T(300.42, 33.37, "Dokumentenart"); T(300.34, 29.44, "Einzelteilzeichnung")
T(300.17, 24.37, "Titel, Zusätzlicher Titel"); T(329.0, 16.3, "Abtriebsnabe (Pos.2)", 3.5, ha="center")
T(360.34, 33.37, "Dokumentenstatus"); T(360.25, 24.28, "Sachnummer"); T(360.4, 20.5, "14.2.5.3")
T(359.64, 15.3, "Änd."); T(367.15, 15.38, "Ausgabedatum"); T(392.23, 15.3, "Spr."); T(402.32, 15.38, "Blatt")
T(230.43, 54.27, "Werkstoff:", 3.5); T(255.42, 54.27, "EN-GJS-700-2", 3.5)
T(230.43, 48.3, "Maßstab:", 3.5); T(255.42, 48.3, "1:1", 3.5)
sh.ax.add_patch(MPoly([(392.3, 49.9), (392.3, 53.8), (399.6, 55.5), (399.6, 48.5)], closed=True, fill=False, lw=TH, color="k"))
sh.ax.add_patch(Circle((403.9, 51.8), 3.6, fill=False, lw=TH, color="k"))
sh.ax.add_patch(Circle((403.9, 51.8), 1.75, fill=False, lw=TH, color="k"))
sh.cl((390.8, 51.8), (408.2, 51.8)); sh.line([(403.9, 47.4), (403.9, 56.2)], lw=TN)

print(dxfout.export(sh, "Pos02_Abtriebsnabe.dxf"))
sh.save("Pos02_Abtriebsnabe.pdf", "prev_p2.png", dpi=150)
print("ok")
