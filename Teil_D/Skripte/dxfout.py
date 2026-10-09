"""Exportiert ein dimlib-Sheet (matplotlib) als DXF fuer den Import in Creo (Datei -> Oeffnen -> .dxf).
Linien -> LWPOLYLINE/LINE je Layer und Linienbreite, Strich-Punkt -> Linientyp CENTER,
gefuellte Pfeile -> SOLID, Punkte -> gefuellter Kreisring, Texte -> TEXT (Hoehe = Schrifthoehe in mm)."""
import math, ezdxf
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Rectangle, Polygon as MPoly
from matplotlib.text import Text
from shapely.geometry import LineString
from dimlib import MM

ERSATZ = {"−": "-", "–": "-", "…": "...", "↧": "v"}
HA = {"left": 0, "center": 1, "right": 2}
VA = {"baseline": 0, "bottom": 1, "center": 2, "center_baseline": 0, "top": 3}

def _lw(pt):
    mm = pt / MM
    for w in (13, 18, 25, 35, 50, 70, 100, 140):
        if mm*100 <= w + 2: return w
    return 140

def export(sheet, ziel):
    doc = ezdxf.new("R2010", setup=True, units=4)          # units 4 = mm
    doc.header["$LTSCALE"] = 1.0; doc.header["$INSUNITS"] = 4; doc.header["$MEASUREMENT"] = 1
    doc.header["$LIMMAX"] = (sheet.W, sheet.Hh)
    for name, lt, lw, col in (("KANTEN", "CONTINUOUS", 50, 7), ("DUENN", "CONTINUOUS", 25, 7),
                              ("MITTELLINIEN", "CENTER", 25, 7), ("SCHRAFFUR", "CONTINUOUS", 25, 7),
                              ("TEXT", "CONTINUOUS", 25, 7), ("RAHMEN", "CONTINUOUS", 70, 7)):
        doc.layers.add(name, linetype=lt, lineweight=lw, color=col)
    st = doc.styles.get("Standard"); st.dxf.font = "arial.ttf"
    msp = doc.modelspace()
    ax = sheet.ax
    n = dict(lin=0, txt=0, sol=0, kreis=0)
    for art in ax.get_children():
        if art is ax.patch or not art.get_visible(): continue
        if isinstance(art, Line2D):
            x, y = art.get_xdata(), art.get_ydata()
            pts = [(float(a), float(b)) for a, b in zip(x, y)]
            if len(pts) < 2: continue
            lw = _lw(art.get_linewidth())
            dash = getattr(art, "_unscaled_dash_pattern", (0, None))[1]
            if dash and len(dash) >= 4: layer, lw = "MITTELLINIEN", 25
            elif lw >= 50: layer = "KANTEN"
            else: layer = "DUENN"
            if len(pts) > 3:
                pts = list(LineString(pts).simplify(0.004).coords)
            if len(pts) == 2:
                msp.add_line(pts[0], pts[1], dxfattribs=dict(layer=layer, lineweight=lw))
            else:
                closed = math.dist(pts[0], pts[-1]) < 1e-6
                if closed: pts = pts[:-1]
                msp.add_lwpolyline(pts, close=closed, dxfattribs=dict(layer=layer, lineweight=lw))
            n["lin"] += 1
        elif isinstance(art, Circle):
            c, r = art.center, art.get_radius()
            if art.get_fill() and art.get_facecolor()[3] > 0:
                # gefuellter Punkt: Kreisring mit Breite r
                msp.add_lwpolyline([(c[0]-r/2, c[1], r, r, 1), (c[0]+r/2, c[1], r, r, 1)], format="xyseb", close=True,
                                   dxfattribs=dict(layer="DUENN"))
            else:
                msp.add_circle(c, r, dxfattribs=dict(layer="DUENN", lineweight=_lw(art.get_linewidth())))
            n["kreis"] += 1
        elif isinstance(art, (Rectangle, MPoly)):
            pfad = art.get_path().transformed(art.get_patch_transform())
            pts = [tuple(map(float, p)) for p in pfad.vertices]
            if len(pts) > 1 and math.dist(pts[0], pts[-1]) < 1e-9: pts = pts[:-1]
            if art.get_fill() and art.get_facecolor()[3] > 0 and len(pts) == 3:
                a, b, c = pts
                msp.add_solid([a, b, c, c], dxfattribs=dict(layer="DUENN")); n["sol"] += 1
            else:
                lw = _lw(art.get_linewidth())
                msp.add_lwpolyline(pts, close=True, dxfattribs=dict(layer="RAHMEN" if lw >= 70 else ("KANTEN" if lw >= 50 else "DUENN"), lineweight=lw))
                n["lin"] += 1
        elif isinstance(art, Text):
            s = art.get_text()
            if not s.strip(): continue
            for k, v in ERSATZ.items(): s = s.replace(k, v)
            hgt = art.get_fontsize() * 0.72 / MM
            x, y = art.get_position()
            t = msp.add_text(s, height=hgt, rotation=art.get_rotation(),
                             dxfattribs=dict(layer="TEXT", style="Standard", width=1.0))
            h, v = HA.get(art.get_ha(), 0), VA.get(art.get_va(), 0)
            t.dxf.halign = h; t.dxf.valign = v
            t.dxf.insert = (x, y); t.dxf.align_point = (x, y)
            n["txt"] += 1
    doc.saveas(ziel)
    return n
