"""Gesamtzeichnung Fliehkraftkupplung (14.2.3) im Halbschnitt, Lage und Schriftfeld wie Vorlage.
Ansichten aus gen_gz.py (gz_buch.pkl). Lagen aus dem Scan der Vorlage (200 dpi, Rahmen 390 x 277 mm) gemessen."""
import pickle, math, os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../Teil_D/Skripte"))   # dimlib, dxfout_geo
from dimlib import *
from shapely.geometry import LineString as LS, box, MultiLineString
from shapely.ops import unary_union as uu
import dxfout_geo as dxfout, dimlib, build
# VARIANTE=vorlage: Blatt genau wie Vorlage 14.2.3 (ohne Schnittverlauf, ohne Stueckliste); sonst Abgabe nach Angabe Teil A
VORLAGE = os.environ.get("VARIANTE") == "vorlage"
dimlib.FONT = dict(family="Liberation Sans")
def _rahmen(self):
    self.ax.add_patch(plt.Rectangle((20, 10), self.W-30, self.Hh-20, fill=False, lw=TH, color="k"))
Sheet.frame = _rahmen

d = pickle.load(open("gz_buch.pkl", "rb"))
sh = Sheet("A3")
cx, cy = 116.77, 176.07          # Mitte Vorderansicht
ox, oy = 249.05, 176.07          # Schnitt: X = 0 Deckel-Aussenflaeche, Achse
F = lambda u, v: (cx + u, cy + v)
S = lambda x, z: (ox + x, oy + z)

def clip(pls, keep):
    out = []
    for pl in pls:
        if len(pl) < 2: continue
        g = LS(pl).intersection(keep)
        for s in getattr(g, "geoms", [g]):
            if s.geom_type == "LineString" and s.length > 1e-4: out.append(list(s.coords))
    return out
lower, upper = box(-1e3, -1e3, 1e3, 1e-6), box(-1e3, 0, 1e3, 1e3)

# ---------------- Schnitt (unten) + Aussenansicht (oben) ----------------
polys = []
for pos, p in d["polys"]:
    p = p.intersection(box(-1e3, -1e3, 1e3, 0))
    for g in getattr(p, "geoms", [p]):
        if g.geom_type == "Polygon" and g.area > 1e-3: polys.append((pos, g))
# Linienstuecke, die im Inneren einer Schnittflaeche liegen, sind unsichtbar (Kanten hinter der Schnittebene,
# z. B. Kreiskanten genau in einer Stossebene) -> je Teil herausschneiden. Grenzen zwischen zwei Teilen bleiben.
innen = [p.buffer(-0.05) for _, p in polys]
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
sec = sichtbar(clip(d["sec_lines"], lower))
sec = [pl for pl in sec if not all(abs(p[1]) < 1e-6 for p in pl)]
ext = [pl for pl in clip(d["ext_lines"], upper) if not all(abs(p[1]) < 1e-6 for p in pl)]
sh.polylines(sec, S); sh.polylines(ext, S)
HATCH = {"1": (45, 3.0), "2": (135, 3.0), "3": (45, 2.0), "4": (135, 3.0), "5.1": (45, 1.6), "5.2": ("x", 1.4),
         "6": (135, 0.9), "11": (135, 0.9), "12": ("x", 0.8)}
for pos, p in polys:
    a, s = HATCH[pos]; sh.hatch(p, S, a, s)

# Gewinde M8 (Schraube eingeschraubt: Kern schmal; freier Gewinderest im Gehaeuse: Nenn-Durchmesser schmal, Gewindeende breit)
zs = -75
for x0, x1 in ((8.6, 28.6), (65.4, 85.4)):
    for dz in (3.4, -3.4): sh.line([S(x0, zs+dz), S(x1, zs+dz)], lw=TN)
for x0, x1 in ((28.6, 32), (62, 65.4)):
    for dz in (4, -4): sh.line([S(x0, zs+dz), S(x1, zs+dz)], lw=TN)
for xe in (32, 62): sh.line([S(xe, zs-4), S(xe, zs+4)], lw=TH)

# Mittellinien Schnitt
sh.cl(S(-2.3, 0), S(139.6, 0))
sh.cl(S(-3.6, -75), S(44.3, -75)); sh.cl(S(49.8, -75), S(97.4, -75))
sh.cl(S(19.3, -52), S(75.2, -52))
for xb in (21.0, 73.0):
    sh.cl(S(xb, -30-8.1), S(xb, -30+8.1)); sh.cl(S(xb-6.3, -30), S(xb+6.3, -30))

# ---------------- Vorderansicht ----------------
sh.polylines(d["fv_lines"], F)
sh.cl(F(-87.4, 0), F(87.4, 0)); sh.cl(F(0, 87.4), F(0, -87.4))
th = np.linspace(0, 2*math.pi, 400)
sh.ax.plot(cx+75*np.cos(th), cy+75*np.sin(th), color="k", lw=TN, dashes=(14, 3, 1.5, 3))
for k in range(6):
    a = math.radians(30+60*k); x, y = cx+75*math.cos(a), cy+75*math.sin(a)
    sh.cl((x-7*math.cos(a), y-7*math.sin(a)), (x+7*math.cos(a), y+7*math.sin(a)))

# Schnittverlauf A-A: senkrecht durch Stifte und Schrauben, Blick in +Y (Pfeile nach rechts)
if not VORLAGE:
    for sgn in (1, -1):
        y0, y1 = cy+sgn*91, cy+sgn*97
        sh.line([(cx, y0), (cx, y1)], lw=2*TH)
        ya = y1-sgn*1.5
        sh.line([(cx-0.3, ya), (cx+8, ya)]); sh.arrow((cx+8, ya), (cx-0.3, ya))
        sh.text(cx+9.5, ya-2.5, "A", 5)
    sh.text(ox+60, oy+92, "A-A", 5, ha="center")
    sh.text(cx, 64.5, "(ohne Pos. 2 und Pos. 10 gezeichnet)", 3.5, ha="center")
else:
    sh.text(116.84, 54.78, "(ohne Pos.2 und Pos.10 gezeichnet)", 3.5, ha="center")    # Lage wie Vorlage

# ---------------- Positionsnummern im Uhrzeigersinn (Lage wie Vorlage) ----------------
# Nr, Textmitte (X,Z) im Schnitt, Hinweislinie von, Punkt
POS = [("1", (111.1, -30.6), (105.7, -28.6), (77.1, -17.7)),
       ("2", (111.1, -45.6), (105.7, -45.3), (88.3, -44.4)),
       ("3", (111.1, -61.0), (105.7, -62.2), (77.9, -69.6)),
       ("5", (44.2, -102.4), (46.5, -96.5), (60.6, -57.4)),
       ("6", (30.5, -102.4), (31.4, -96.5), (37.7, -58.2)),
       ("8", (16.5, -102.4), (18.4, -96.5), (29.5, -57.6)),
       ("9", (2.5, -102.4), (5.6, -96.5), (23.5, -53.7)),
       ("10", (-13.1, -102.4), (-8.6, -96.5), (4.8, -77.6)),
       ("4", (-21.5, -40.0), (-15.6, -43.2), (5.7, -54.7)),
       ("11", (-21.3, -25.3), (-13.7, -27.3), (16.1, -35.6)),
       ("12", (-21.3, -10.0), (-13.7, -14.6), (5.1, -25.4))]
for nr, t, a, p in POS:
    sh.text(*S(*t), nr, 5, ha="center", va="center")
    sh.line([S(*a), S(*p)], lw=TN)
    sh.ax.add_patch(Circle(S(*p), 0.6, color="k"))
sh.text(*F(-7.6, -102.6), "7", 5, ha="center", va="center")
sh.line([F(-8.6, -96.3), F(-18.7, -47.8)], lw=TN)

# ---------------- Stueckliste (DIN EN ISO 7200), links unten ----------------
if not VORLAGE:
    ROWS = [("1", "1", "Stk", "Antriebsnabe", "", "EN-GJS-700-2"), ("2", "1", "Stk", "Abtriebsnabe", "", "EN-GJS-700-2"),
            ("3", "1", "Stk", "Gehäuse", "", "E295"), ("4", "1", "Stk", "Deckel", "", "EN-GJS-700-2"),
            ("5", "2", "Stk", "Fliehgewicht (komplett)", "", ""), ("5.1", "2", "Stk", "Gewicht", "", "EN-GJS-700-2"),
            ("5.2", "2", "Stk", "Belag", "", "geklebt"), ("6", "4", "Stk", "Scheibe", "", "S235JR"),
            ("7", "4", "Stk", "Zugfeder", "", "Federstahl"), ("8", "8", "Stk", "Sicherungsscheibe", "DIN 6799 – 7", ""),
            ("9", "4", "Stk", "Zylinderstift", "ISO 2338 – 8 m6 × 50 – St", ""),
            ("10", "12", "Stk", "Zylinderschraube", "ISO 4762 – M8 × 20 – 8.8", ""),
            ("11", "2", "Stk", "Rillenkugellager", "DIN 625 – 6009 – 2Z", ""), ("12", "1", "Stk", "Filzring", "DIN 5419 – M5 × 45", "")]
    COLS = [0, 12, 24, 36, 88, 145, 180]
    HDR = ["Pos.", "Menge", "Einh.", "Benennung", "Sachnummer/Norm – Kurzbezeichnung", "Werkstoff/Bemerkung"]
    rh, X0S, yb = 3.4, 20.0, 10.0
    n = len(ROWS)+1
    sh.ax.add_patch(plt.Rectangle((X0S, yb), 180, rh*n, fill=False, lw=TH, color="k"))
    for i in range(1, n): sh.line([(X0S, yb+rh*i), (X0S+180, yb+rh*i)], lw=TH if i == 1 else TN)
    for c in COLS[1:-1]: sh.line([(X0S+c, yb), (X0S+c, yb+rh*n)], lw=TN)
    for c, h in zip(COLS, HDR): sh.text(X0S+c+0.8, yb+0.8, h, 1.8)
    for i, row in enumerate(ROWS):
        for c, v in zip(COLS, row): sh.text(X0S+c+1, yb+rh*(i+1)+0.8, v, 2.1)

# ---------------- Schriftfeld (wie Vorlage 14.2.3 / 14.2.5.x) ----------------
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
T(300.42, 33.37, "Dokumentenart"); T(300.34, 29.44, "Gesamtzeichnung")
T(300.17, 24.37, "Titel, Zusätzlicher Titel")
# Titel und Untertitel sind in der Vorlage schmaler gesetzt als die uebrigen Texte -> Umriss gestaucht (Lage/Groesse aus dem Scan)
from matplotlib.textpath import TextPath
from matplotlib.patches import PathPatch
from matplotlib.font_manager import FontProperties
import matplotlib.transforms as mtr
def text_gestaucht(xm, y, s, h, sx):
    tp = TextPath((0, 0), s, size=h*MM/0.72, prop=FontProperties(family="Liberation Sans"))
    PTMM = 25.4/72
    ext = tp.get_extents()
    tr = mtr.Affine2D().scale(PTMM*sx, PTMM).translate(xm - (ext.x0 + ext.x1)/2*PTMM*sx, y)
    sh.ax.add_patch(PathPatch(tr.transform_path(tp), facecolor="k", edgecolor="none", lw=0))
text_gestaucht(329.06, 17.35, "Fliehkraftkupplung", 3.87, 0.910)
text_gestaucht(328.87, 12.98, "mit Passfederverbindung", 2.915, 0.863)
T(360.34, 33.37, "Dokumentenstatus"); T(360.25, 24.28, "Sachnummer"); T(360.4, 20.5, "14.2.3")
T(359.64, 15.3, "Änd."); T(367.15, 15.38, "Ausgabedatum"); T(392.23, 15.3, "Spr."); T(402.32, 15.38, "Blatt")
T(230.4, 49.57, "Maßstab", 3.5); T(253.6, 49.57, "1:1", 3.5)          # wie Vorlage 14.2.3
sh.ax.add_patch(MPoly([(392.3, 49.9), (392.3, 53.8), (399.6, 55.5), (399.6, 48.5)], closed=True, fill=False, lw=TH, color="k"))
sh.ax.add_patch(Circle((403.9, 51.8), 3.6, fill=False, lw=TH, color="k"))
sh.ax.add_patch(Circle((403.9, 51.8), 1.75, fill=False, lw=TH, color="k"))
sh.cl((390.8, 51.8), (408.2, 51.8)); sh.line([(403.9, 47.4), (403.9, 56.2)], lw=TN)

name = "Gesamtzeichnung_Fliehkraftkupplung" + ("_wie_Vorlage" if VORLAGE else "")
print(dxfout.export(sh, name + ".dxf"))
sh.save(name + ".pdf", "prev_gz" + ("_vorlage" if VORLAGE else "") + ".png", dpi=150)
print("ok")
