"""Bemasste Skizzenbilder fuer die Modellbaum-Anleitung."""
import math, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import dimlib
from dimlib import TH, TN, MM

class SK(dimlib.Sheet):
    def __init__(self, xmin, xmax, ymin, ymax, scale=1.0, title=""):
        self.M = scale
        w, h = (xmax-xmin)*scale, (ymax-ymin)*scale + 12
        self.W, self.Hh = w, h
        self.fig = plt.figure(figsize=(w/25.4, h/25.4))
        self.ax = self.fig.add_axes([0, 0, 1, 1]); self.ax.set_xlim(0, w); self.ax.set_ylim(0, h)
        self.ax.set_aspect("equal"); self.ax.axis("off")
        self.ox, self.oy = xmin, ymin
        if title: self.text(3, h-6, title, 4)
    def T(self, x, y): return ((x-self.ox)*self.M, (y-self.oy)*self.M)
    def prof(self, pts, lw=TH, close=True):
        """pts wie replay: (x, r) oder ('A', mitte, ende)."""
        P = [self.T(*pts[0])]; cur = pts[0]
        seq = pts[1:] + ([pts[0]] if close else [])
        for p in seq:
            if p[0] == "A":
                P += arcpts(cur, p[1], p[2], self.T); cur = p[2]
            else:
                P.append(self.T(*p)); cur = p
        self.line(P, lw=lw)
    def axis(self, x0, x1, y=0):
        self.cl(self.T(x0, y), self.T(x1, y))
    def hdim(self, x1, x2, y_feature1, y_feature2, level, text, **kw):
        return self.dim(self.T(x1, y_feature1), self.T(x2, y_feature2), self.T(0, level)[1], text, "h", **kw)
    def ddim(self, x, r, xdim, text, **kw):
        """Durchmessermass ab Mittellinie (Creo-Sketcher: Ø-Bemassung zur Mittellinie)."""
        p0 = self.T(xdim, 0); p1 = self.T(xdim, r)
        if abs(x - xdim) > 0.01: self.line([self.T(x, r), (p1[0] + (2 if xdim > x else -2), p1[1])])
        self.line([p0, p1]); self.arrow(p1, p0)
        self.text(p1[0]-1.0, (p0[1]+p1[1])/2, text, 3.5, rot=90, ha="center")
    def png(self, path, dpi=160):
        self.fig.savefig(path, dpi=dpi); plt.close(self.fig)

def arcpts(p0, pm, p2, T, n=30):
    (x1, y1), (x2, y2), (x3, y3) = p0, pm, p2
    d = 2*(x1*(y2-y3) + x2*(y3-y1) + x3*(y1-y2))
    ux = ((x1*x1+y1*y1)*(y2-y3) + (x2*x2+y2*y2)*(y3-y1) + (x3*x3+y3*y3)*(y1-y2))/d
    uy = ((x1*x1+y1*y1)*(x3-x2) + (x2*x2+y2*y2)*(x1-x3) + (x3*x3+y3*y3)*(x2-x1))/d
    r = math.hypot(x1-ux, y1-uy)
    a1, am, a3 = (math.atan2(y-uy, x-ux) for x, y in (p0, pm, p2))
    def norm(a, ref):
        while a < ref: a += 2*math.pi
        return a
    am_, a3_ = norm(am, a1), norm(a3, a1)
    if am_ > a3_: a3_ -= 2*math.pi
    return [T(ux + r*math.cos(t), uy + r*math.sin(t)) for t in np.linspace(a1, a3_, n)]
