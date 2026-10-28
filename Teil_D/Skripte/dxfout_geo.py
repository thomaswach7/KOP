"""DXF-Export fuer Creo, unabhaengig von Schriftarten und Linientyp-Tabellen:
- Texte werden als Geometrie ausgegeben (Umriss der Buchstaben + feine Fuelllinien), genau so wie sie
  matplotlib in der PDF setzt (Lage aus dem Renderer abgegriffen). Creo kann die Schrift damit nicht mehr ersetzen.
- Strich-Punkt-Linien werden in einzelne Striche zerlegt (Muster wie in der PDF).
- Breite Linien (0,5 / 0,7) als LWPOLYLINE mit konstanter Breite und Linienstaerke; schmale Linien 0,25.
- Gefuellte Flaechen (Pfeile, Hinweispunkte) als Umriss + Fuelllinien.
Layer: KANTEN (0,5), DUENN (0,25), MITTELLINIEN, SCHRAFFUR, TEXT, RAHMEN (0,7)."""
import math, ezdxf
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Rectangle, Polygon as MPoly, PathPatch
from matplotlib.textpath import TextPath
from matplotlib.backends.backend_agg import RendererAgg
from shapely.geometry import LineString, Polygon, MultiLineString, box
from shapely import affinity
PT = 25.4/72                 # Punkt -> mm
FILL = 0.06                  # Abstand der Fuelllinien in mm

def _lw(pt):
    mm = pt*PT
    for w in (13, 18, 25, 35, 50, 70, 100, 140):
        if mm*100 <= w + 2: return w
    return 140

def _texte(fig):
    """Alle Textaufrufe beim Schreiben der PDF abgreifen (gleicher Satz wie in der PDF):
    (X, Y) Grundlinienanfang in mm, Text, Schrift, Winkel. Blatt = Achse ueber die ganze Figur in mm."""
    import io
    from matplotlib.backends.backend_pdf import RendererPdf
    cap = []
    orig = RendererPdf.draw_text
    def hook(self, gc, x, y, s, prop, angle, ismath=False, mtext=None):
        cap.append((x*PT, y*PT, s, prop.copy(), angle))
        return orig(self, gc, x, y, s, prop, angle, ismath, mtext)
    RendererPdf.draw_text = hook
    try: fig.savefig(io.BytesIO(), format="pdf")
    finally: RendererPdf.draw_text = orig
    return cap

def _glyphen(s, prop):
    """Buchstabenflaechen (shapely) in mm, Grundlinienanfang im Ursprung."""
    tp = TextPath((0, 0), s, size=prop.get_size_in_points(), prop=prop)
    flaeche = None
    for ring in tp.to_polygons(closed_only=True):
        if len(ring) < 3: continue
        p = Polygon(np.asarray(ring)*PT).buffer(0)
        flaeche = p if flaeche is None else flaeche.symmetric_difference(p)
    return flaeche

def _fuellen(msp, poly, layer):
    if poly is None or poly.is_empty: return 0
    n = 0
    for g in getattr(poly, "geoms", [poly]):
        for ring in [g.exterior] + list(g.interiors):
            msp.add_lwpolyline(list(ring.coords), close=True, dxfattribs=dict(layer=layer, lineweight=13)); n += 1
    x0, y0, x1, y1 = poly.bounds
    ls = [LineString([(x0-1, y), (x1+1, y)]) for y in np.arange(y0 + FILL/2, y1, FILL)]
    inter = MultiLineString(ls).intersection(poly)
    for g in getattr(inter, "geoms", [inter]):
        if g.geom_type == "LineString" and g.length > 1e-3:
            msp.add_line(g.coords[0], g.coords[-1], dxfattribs=dict(layer=layer, lineweight=13)); n += 1
    return n

def _striche(pts, offset, seq):
    """Polylinie nach Strichmuster (mm) zerlegen."""
    L = LineString(pts); tot = L.length; out = []
    pos = -offset; i = 0
    while pos < tot:
        a = seq[i % len(seq)]
        if i % 2 == 0:
            s0, s1 = max(pos, 0), min(pos + a, tot)
            if s1 - s0 > 1e-4:
                seg = [L.interpolate(s0)] + [L.interpolate(t) for t in np.linspace(s0, s1, 2 + int((s1-s0)/0.5))[1:-1]] + [L.interpolate(s1)]
                out.append([(p.x, p.y) for p in seg])
        pos += a; i += 1
    return out

def export(sheet, ziel):
    fig, ax = sheet.fig, sheet.ax
    doc = ezdxf.new("R2010", setup=False, units=4)
    doc.header["$INSUNITS"] = 4; doc.header["$MEASUREMENT"] = 1; doc.header["$LIMMAX"] = (sheet.W, sheet.Hh)
    for name, lw in (("KANTEN", 50), ("DUENN", 25), ("MITTELLINIEN", 25), ("SCHRAFFUR", 25), ("TEXT", 13), ("RAHMEN", 70)):
        doc.layers.add(name, lineweight=lw, color=7)
    msp = doc.modelspace()
    n = dict(linien=0, text_elemente=0, texte=0)
    for art in ax.get_children():
        if art is ax.patch or not art.get_visible() or isinstance(art, type(ax.title)): continue
        if isinstance(art, Line2D):
            pts = [(float(a), float(b)) for a, b in zip(art.get_xdata(), art.get_ydata())]
            if len(pts) < 2: continue
            lw = _lw(art.get_linewidth())
            off, seq = art._dash_pattern
            if seq:
                for st in _striche(pts, off*PT, [s*PT for s in seq]):
                    msp.add_lwpolyline(st, dxfattribs=dict(layer="MITTELLINIEN", lineweight=25)); n["linien"] += 1
                continue
            if len(pts) > 3: pts = list(LineString(pts).simplify(0.004).coords)
            layer = "KANTEN" if lw >= 50 else "DUENN"
            attr = dict(layer=layer, lineweight=lw)
            if lw >= 50: attr["const_width"] = lw/100
            closed = len(pts) > 2 and math.dist(pts[0], pts[-1]) < 1e-6
            msp.add_lwpolyline(pts[:-1] if closed else pts, close=closed, dxfattribs=attr); n["linien"] += 1
        elif isinstance(art, PathPatch):            # z. B. gestauchter Text als Umriss: gefuellte Flaeche
            pfad = art.get_path().transformed(art.get_patch_transform())
            fl = None
            for ring in pfad.to_polygons(closed_only=True):
                if len(ring) < 3: continue
                q = Polygon(ring).buffer(0)
                fl = q if fl is None else fl.symmetric_difference(q)
            n["text_elemente"] += _fuellen(msp, fl, "TEXT")
        elif isinstance(art, (Circle, Rectangle, MPoly)):
            pfad = art.get_path().transformed(art.get_patch_transform())
            pts = [tuple(map(float, p)) for p in pfad.to_polygons()[0]] if isinstance(art, Circle) else \
                  [tuple(map(float, p)) for p in pfad.vertices]
            if len(pts) > 1 and math.dist(pts[0], pts[-1]) < 1e-9: pts = pts[:-1]
            if art.get_fill() and art.get_facecolor()[3] > 0:
                n["linien"] += _fuellen(msp, Polygon(pts).buffer(0), "DUENN")
            else:
                lw = _lw(art.get_linewidth())
                attr = dict(layer="RAHMEN" if lw >= 70 else ("KANTEN" if lw >= 50 else "DUENN"), lineweight=lw)
                if lw >= 50: attr["const_width"] = lw/100
                msp.add_lwpolyline(pts, close=True, dxfattribs=attr); n["linien"] += 1
    assert tuple(ax.get_xlim()) == (0, sheet.W) and tuple(ax.get_ylim()) == (0, sheet.Hh)   # 1 Einheit = 1 mm
    for X, Y, s, prop, angle in _texte(fig):
        if not s.strip(): continue
        g = _glyphen(s, prop)
        if g is None: continue
        g = affinity.rotate(g, angle, origin=(0, 0))
        n["text_elemente"] += _fuellen(msp, affinity.translate(g, X, Y), "TEXT"); n["texte"] += 1
    doc.saveas(ziel)
    return n
