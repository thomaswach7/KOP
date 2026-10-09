"""Kleine Bibliothek fuer normgerechte Einzelteilzeichnungen (matplotlib, Blatt in mm)."""
import math, datetime
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon as MPoly
from shapely.geometry import LineString, MultiLineString, Polygon

MM = 72/25.4
TH, TN = 0.5*MM, 0.25*MM
H = 3.5                     # Schrifthoehe Masszahlen
FONT = dict(family="DejaVu Sans")
ARR_L, ARR_W = 3.0, 0.9     # Pfeil Laenge / halbe Breite

class Sheet:
    def __init__(self, fmt="A3"):
        self.W, self.Hh = (420, 297) if fmt == "A3" else (210, 297)
        self.fmt = fmt
        self.fig = plt.figure(figsize=(self.W/25.4, self.Hh/25.4))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, self.W); self.ax.set_ylim(0, self.Hh)
        self.ax.set_aspect("equal"); self.ax.axis("off")
        self.frame()

    # ---------- Grundelemente ----------
    def line(self, pts, lw=TN, **kw):
        a = np.asarray(pts, float)
        self.ax.plot(a[:, 0], a[:, 1], color="k", lw=lw, solid_capstyle="round", **kw)
    def cl(self, p, q):       # Mittellinie
        self.ax.plot([p[0], q[0]], [p[1], q[1]], color="k", lw=TN, dashes=(14, 3, 1.5, 3))
    def text(self, x, y, s, size=H, rot=0, ha="left", va="baseline", **kw):
        self.ax.text(x, y, s, fontsize=size*MM/0.72, rotation=rot, ha=ha, va=va,
                     rotation_mode="anchor", **FONT, **kw)
    def arrow(self, tip, frm):
        """gefuellter Pfeil mit Spitze in tip, Richtung von frm nach tip."""
        dx, dy = tip[0]-frm[0], tip[1]-frm[1]; L = math.hypot(dx, dy) or 1
        ux, uy = dx/L, dy/L
        b = (tip[0]-ux*ARR_L, tip[1]-uy*ARR_L)
        self.ax.add_patch(MPoly([tip, (b[0]-uy*ARR_W, b[1]+ux*ARR_W), (b[0]+uy*ARR_W, b[1]-ux*ARR_W)],
                                closed=True, color="k", lw=0))

    # ---------- Rahmen + Schriftfeld ----------
    def frame(self):
        W, Hh = self.W, self.Hh
        self.ax.add_patch(plt.Rectangle((20, 10), W-30, Hh-20, fill=False, lw=0.7*MM, color="k"))
        self.line([(10, Hh/2), (20, Hh/2)], lw=TH)
        self.line([(W/2+5, Hh-10), (W/2+5, Hh-5)], lw=TH)

    def titleblock(self, titel, sachnr, werkstoff, massstab, blatt="1/1"):
        X0, Y0, Wt = self.W-10-180, 10, 180
        if self.fmt == "A4":
            X0, Wt = 20, 180
        r = lambda x, y, w, h, lw=TH: self.ax.add_patch(plt.Rectangle((x, y), w, h, fill=False, lw=lw, color="k"))
        r(X0, Y0, Wt, 36)
        L = lambda a, b: self.line([a, b])
        L((X0, Y0+27), (X0+Wt, Y0+27)); L((X0+60, Y0+18), (X0+Wt, Y0+18))
        for x in (X0+40, X0+90, X0+135): L((x, Y0+27), (x, Y0+36))
        L((X0+60, Y0), (X0+60, Y0+27)); L((X0+130, Y0), (X0+130, Y0+27))
        L((X0+130, Y0+9), (X0+Wt, Y0+9))
        for x in (X0+138, X0+163, X0+171): L((x, Y0), (x, Y0+9))
        L((X0, Y0+13), (X0+60, Y0+13))
        s = 1.8; t = self.text
        t(X0+1, Y0+34, "Verantwortl. Abt.", s); t(X0+41, Y0+34, "Technische Referenz", s)
        t(X0+91, Y0+34, "Erstellt durch", s);   t(X0+136, Y0+34, "Genehmigt von", s)
        t(X0+41, Y0+29, "Projekt Fliehkraftkupplung", 2.2)
        t(X0+61, Y0+25, "Dokumentenart", s); t(X0+63, Y0+20, "Einzelteilzeichnung", 3.5)
        t(X0+131, Y0+25, "Dokumentenstatus", s); t(X0+133, Y0+20, "in Bearbeitung", 2.5)
        t(X0+61, Y0+16, "Titel, Zusätzlicher Titel", s)
        t(X0+95, Y0+6, titel, 4, ha="center")
        t(X0+131, Y0+16, "Sachnummer", s); t(X0+133, Y0+11, sachnr, 3.5)
        t(X0+131, Y0+7, "Änd.", s); t(X0+139, Y0+7, "Ausgabedatum", s); t(X0+164, Y0+7, "Spr.", s); t(X0+172, Y0+7, "Blatt", s)
        t(X0+132, Y0+2, "A", 2.5); t(X0+140, Y0+2, datetime.date.today().isoformat(), 2.5)
        t(X0+165, Y0+2, "de", 2.5); t(X0+173, Y0+2, blatt, 2.5)
        t(X0+1, Y0+24.5, "Werkstoff:", 2.5); t(X0+3, Y0+17.5, werkstoff, 3.5)
        t(X0+1, Y0+9, f"Maßstab {massstab}", 3.5)
        # Projektionssymbol Methode 1
        px, py = X0+48, Y0+5.5
        self.ax.add_patch(plt.Polygon([(px-7, py-1.5), (px-7, py+1.5), (px-1.5, py+3), (px-1.5, py-3)], fill=False, lw=TN, color="k"))
        self.ax.add_patch(Circle((px+4, py), 3, fill=False, lw=TN, color="k"))
        self.ax.add_patch(Circle((px+4, py), 1.5, fill=False, lw=TN, color="k"))
        return X0, Y0

    def notes(self, x, y, guss=True, freistich=None, radien=None, extra=()):
        """Allgemeine Angaben links unten (wie Angabe Teil D)."""
        lines = []
        if freistich: lines.append(f"Nicht bemaßte Freistiche DIN 509 – {freistich}")
        if radien: lines.append(f"Nicht bemaßte Radien {radien}")
        lines += list(extra)
        lines += ["Oberflächen nach DIN EN ISO 1302",
                  "Werkstückkanten nach DIN ISO 13715",
                  "Allgemeintoleranzen ISO 2768-mK, Passungssystem Einheitsbohrung"]
        if guss: lines.append("Gusstoleranzen DIN 1686 – GTB 18")
        for i, s in enumerate(reversed(lines)):
            self.text(x, y + i*5.2, s, 3.0)
        return y + len(lines)*5.2

    def edge_symbols(self, x, y):
        """Werkstueckkanten-Symbole ISO 13715: aussen -0,3 / innen +0,3."""
        self.line([(x, y), (x, y+6)], lw=TN); self.line([(x-4, y+6), (x, y+6)], lw=TN)
        self.line([(x, y+6), (x+4, y+10)], lw=TN); self.line([(x+4, y+10), (x+9, y+10)], lw=TN)
        self.line([(x+4, y+10), (x+4, y+13)], lw=TN); self.text(x+4.6, y+10.8, "−0,3", 2.5)
        x2 = x+18
        self.line([(x2, y+6), (x2, y+1)], lw=TN); self.line([(x2, y+1), (x2+5, y+1)], lw=TN)
        self.line([(x2, y+1), (x2+5, y+6)], lw=TN)  # Innenkante (stilisiert)
        self.line([(x2+5, y+6), (x2+10, y+6)], lw=TN); self.line([(x2+5, y+6), (x2+5, y+9)], lw=TN)
        self.text(x2+5.6, y+6.8, "+0,3", 2.5)

    # ---------- Oberflaechensymbol ISO 1302 ----------
    def surf_symbol(self, tip, letter="", text="", removal=True, prohibited=False, rot=0, size=1.0):
        """Spitze in tip; rot = Drehung in Grad (0: Symbol steht ueber der Flaeche)."""
        h = 5.0*size
        pts = {"tip": (0, 0), "s": (-h/math.sqrt(3)*1.0, h), "l": (2*h/math.sqrt(3), 2*h)}
        c, s_ = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        T = lambda p: (tip[0] + c*p[0] - s_*p[1], tip[1] + s_*p[0] + c*p[1])
        self.line([T(pts["s"]), T(pts["tip"]), T(pts["l"])], lw=TN)
        if removal:
            self.line([T(pts["s"]), T((h/math.sqrt(3), h))], lw=TN)
        if prohibited:
            cc = T((0, h*0.62)); self.ax.add_patch(Circle(cc, h*0.30, fill=False, lw=TN, color="k"))
        if letter or text:
            L = 2*h/math.sqrt(3) + (6 if text else 4)*size + (len(text)*1.9*size if text else 0)
            self.line([T(pts["l"]), T((L, 2*h))], lw=TN)
            s = text if text else letter
            self.text(*T((2*h/math.sqrt(3)+0.8, h+0.9)), s, 3.5*size, rot=rot)

    def surf_leader(self, p_surf, p_ref, letter, removal=True):
        """Hinweislinie mit Pfeil auf Flaeche, Symbol sitzt am Ende."""
        self.line([p_surf, p_ref]); self.arrow(p_surf, p_ref)
        self.surf_symbol(p_ref, letter, removal=removal)

    # ---------- Form- und Lagetoleranzen ----------
    def _sym(self, kind, cx, cy):
        k = 2.4
        if kind == "parallel":
            self.line([(cx-1.6, cy-k/1.2), (cx-0.4, cy+k/1.2)], lw=TN); self.line([(cx+0.4, cy-k/1.2), (cx+1.6, cy+k/1.2)], lw=TN)
        elif kind == "perp":
            self.line([(cx-2, cy-1.6), (cx+2, cy-1.6)], lw=TN); self.line([(cx, cy-1.6), (cx, cy+1.8)], lw=TN)
        elif kind == "coax":
            self.ax.add_patch(Circle((cx, cy), 2.0, fill=False, lw=TN, color="k"))
            self.ax.add_patch(Circle((cx, cy), 1.1, fill=False, lw=TN, color="k"))
        elif kind == "sym":
            self.line([(cx-2.2, cy), (cx+2.2, cy)], lw=TN)
            self.line([(cx-1.3, cy+1.3), (cx+1.3, cy+1.3)], lw=TN); self.line([(cx-1.3, cy-1.3), (cx+1.3, cy-1.3)], lw=TN)
        elif kind == "trunout":   # Gesamtlauf: 2 Pfeile + Grundlinie
            for dx in (-1.8, 0.4):
                a, b = (cx+dx-0.6, cy-1.6), (cx+dx+1.6, cy+1.6)
                self.line([a, b], lw=TN); self.arrow(b, a) if False else None
                self.ax.add_patch(MPoly([b, (b[0]-1.4, b[1]-0.3), (b[0]-0.3, b[1]-1.4)], closed=True, color="k", lw=0))
            self.line([(cx-2.4, cy-1.6), (cx-0.2+0.6, cy-1.6)], lw=TN)
        elif kind == "runout":
            a, b = (cx-1.2, cy-1.6), (cx+1.2, cy+1.6)
            self.line([a, b], lw=TN)
            self.ax.add_patch(MPoly([b, (b[0]-1.4, b[1]-0.3), (b[0]-0.3, b[1]-1.4)], closed=True, color="k", lw=0))

    def gdt(self, pos, kind, value, datum=None, leader_to=None, leader_via=None, side="left", zellen=(7.0, 3.0, 2.5, 7.0)):
        """Toleranzrahmen; pos = linke untere Ecke; leader_to = Pfeilspitze."""
        x, y = pos; hgt = 7.0
        w1 = zellen[0]; w2 = zellen[1] + len(value)*zellen[2]; w3 = zellen[3] if datum else 0
        cells = [w1, w2] + ([w3] if datum else [])
        xx = x
        for w in cells:
            self.ax.add_patch(plt.Rectangle((xx, y), w, hgt, fill=False, lw=TN, color="k")); xx += w
        self._sym(kind, x+w1/2, y+hgt/2)
        self.text(x+w1+1.4, y+2.0, value, 3.5)
        if datum: self.text(x+w1+w2+w3/2, y+2.0, datum, 3.5, ha="center")
        W = sum(cells)
        if leader_to is not None:
            start = (x, y+hgt/2) if side == "left" else ((x+W, y+hgt/2) if side == "right" else
                     ((x+w1/2, y) if side == "bottom" else (x+w1/2, y+hgt)))
            pts = [start] + ([leader_via] if leader_via else []) + [leader_to]
            self.line(pts); self.arrow(leader_to, pts[-2])
        return W

    def datum(self, foot, direction, letter, length=7.0):
        """Bezugsdreieck (gefuellt) mit Fuss auf Flaeche/Masslinie, direction: Einheitsvektor weg vom Teil."""
        dx, dy = direction; L = math.hypot(dx, dy); dx, dy = dx/L, dy/L
        px, py = -dy, dx
        tri = [(foot[0]+px*1.8, foot[1]+py*1.8), (foot[0]-px*1.8, foot[1]-py*1.8), (foot[0]+dx*3.1, foot[1]+dy*3.1)]
        self.ax.add_patch(MPoly(tri, closed=True, color="k", lw=0))
        end = (foot[0]+dx*length, foot[1]+dy*length)
        self.line([(foot[0]+dx*3.1, foot[1]+dy*3.1), end])
        bx, by = end[0]+dx*3.5, end[1]+dy*3.5
        self.ax.add_patch(plt.Rectangle((bx-3.5, by-3.5), 7, 7, fill=False, lw=TN, color="k"))
        self.text(bx, by-1.75, letter, 3.5, ha="center")

    # ---------- Masse ----------
    def dim(self, p1, p2, off, text, orient="h", tpos=0.5, ext1=True, ext2=True, arrows_out=None, text_side=+1):
        """Laengenmass zwischen p1 und p2 (Blattkoordinaten).
        orient 'h': Masslinie waagrecht bei y = max/min + off ; 'v': senkrecht bei x.
        off: absolute Koordinate der Masslinie (y bei 'h', x bei 'v')."""
        if orient == "h":
            a, b = (p1[0], off), (p2[0], off)
            for p, e in ((p1, ext1), (p2, ext2)):
                if e:
                    sgn = 1 if off > p[1] else -1
                    self.line([(p[0], p[1]+sgn*1.0), (p[0], off+sgn*2.0)])
        else:
            a, b = (off, p1[1]), (off, p2[1])
            for p, e in ((p1, ext1), (p2, ext2)):
                if e:
                    sgn = 1 if off > p[0] else -1
                    self.line([(p[0]+sgn*1.0, p[1]), (off+sgn*2.0, p[1])])
        L = math.hypot(b[0]-a[0], b[1]-a[1])
        out = arrows_out if arrows_out is not None else L < 9
        ux, uy = (b[0]-a[0])/L, (b[1]-a[1])/L
        if out:
            self.line([(a[0]-ux*7, a[1]-uy*7), (b[0]+ux*7, b[1]+uy*7)])
            self.arrow(a, (a[0]-ux*3, a[1]-uy*3)); self.arrow(b, (b[0]+ux*3, b[1]+uy*3))
        else:
            self.line([a, b]); self.arrow(a, b); self.arrow(b, a)
        mx, my = a[0]+(b[0]-a[0])*tpos, a[1]+(b[1]-a[1])*tpos
        if "|" in text:          # Nennmass|oberes Abmass|unteres Abmass
            main, up, lo = text.split("|")
            wm = len(main)*H*0.9; wt = max(len(up), len(lo))*2.2*0.62
            if orient == "h":
                x0 = mx - (wm+wt+0.8)/2
                self.text(x0, my+1.0, main, H); self.text(x0+wm+0.8, my+3.5, up, 2.2); self.text(x0+wm+0.8, my+0.5, lo, 2.2)
            else:
                y0 = my - (wm+wt+0.8)/2
                self.text(mx-1.0, y0, main, H, rot=90); self.text(mx-3.7, y0+wm+0.8, up, 2.2, rot=90); self.text(mx-0.9, y0+wm+0.8, lo, 2.2, rot=90)
            return a, b
        if orient == "h":
            self.text(mx, my+1.0, text, H, ha="center")
        else:
            self.text(mx-1.0, my, text, H, rot=90, ha="center")
        return a, b

    def dim_angle(self, c, r, a1, a2, text):
        th = np.radians(np.linspace(a1, a2, 60))
        pts = [(c[0]+r*math.cos(t), c[1]+r*math.sin(t)) for t in th]
        self.line(pts)
        self.arrow(pts[0], pts[3]); self.arrow(pts[-1], pts[-4])
        am = math.radians((a1+a2)/2)
        self.text(c[0]+(r+1.5)*math.cos(am), c[1]+(r+1.5)*math.sin(am), text, H, ha="center", va="bottom",
                  rot=(math.degrees(am)-90) if -90 < (a1+a2)/2 < 90 else 0)

    def leader(self, tip, knee, text, arrow=True, dot=False, end_len=None, size=H):
        """Hinweislinie mit Text auf Bezugslinie."""
        right = knee[0] >= tip[0]
        w = end_len if end_len else len(text)*size*0.62 + 2
        end = (knee[0]+w, knee[1]) if right else (knee[0]-w, knee[1])
        self.line([tip, knee, end])
        if arrow: self.arrow(tip, knee)
        if dot: self.ax.add_patch(Circle(tip, 0.6, color="k"))
        self.text(knee[0]+1 if right else end[0]+1, knee[1]+0.9, text, size)

    def radius(self, center, r, ang, text, outside=True, ext=10):
        """Radiusmass: Masslinie radial, Pfeil auf Bogen (von innen), Text auf Verlaengerung."""
        a = math.radians(ang)
        tip = (center[0]+r*math.cos(a), center[1]+r*math.sin(a))
        if outside:
            far = (center[0]+(r+ext)*math.cos(a), center[1]+(r+ext)*math.sin(a))
            self.line([tip, far]); self.arrow(tip, far)
            knee = far
        else:
            self.line([center, tip]); self.arrow(tip, center); knee = tip
        hor = (knee[0] + (len(text)*2.4+2)*(1 if math.cos(a) >= 0 else -1), knee[1])
        self.line([knee, hor])
        self.text(min(knee[0], hor[0])+1, knee[1]+0.9, text, H)

    # ---------- Ansichten ----------
    def polylines(self, pls, T, lw=TH):
        for pl in pls:
            self.line([T(*p) for p in pl], lw=lw)

    def hatch(self, poly, T, ang=45, sp=2.5):
        """poly: shapely-Polygon in Teilkoordinaten, T: Abbildung auf Blatt (nur Verschiebung/Massstab)."""
        if poly.is_empty: return
        minx, miny, maxx, maxy = poly.bounds; cx, cy = (minx+maxx)/2, (miny+maxy)/2
        R = math.hypot(maxx-minx, maxy-miny)
        angs = [45, 135] if ang == "x" else [ang]
        for a in angs:
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            ls = []; k = -R
            while k <= R:
                ox, oy = cx - sa*k, cy + ca*k
                ls.append(LineString([(ox-ca*R, oy-sa*R), (ox+ca*R, oy+sa*R)])); k += sp
            inter = MultiLineString(ls).intersection(poly)
            for g in getattr(inter, "geoms", [inter]):
                for gg in getattr(g, "geoms", [g]):
                    if gg.geom_type == "LineString" and not gg.is_empty:
                        self.line([T(*p) for p in gg.coords], lw=TN)

    def save(self, path, png=None, dpi=110):
        self.fig.savefig(path)
        if png: self.fig.savefig(png, dpi=dpi)
        plt.close(self.fig)
