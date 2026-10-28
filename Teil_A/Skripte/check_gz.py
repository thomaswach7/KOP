"""Pruefung Gesamtzeichnung: (1) Hinweislinien-Punkte liegen im richtigen Teil, (2) aneinandergrenzende Schnittflaechen
haben unterschiedliche Schraffur (Winkel oder Abstand)."""
import pickle, re, cadquery as cq
from cadquery import Vector
from shapely.ops import unary_union
import build2
src = open("d_gz.py").read()
HATCH = eval(re.search(r"HATCH = (\{.*?\})\n", src, re.S).group(1))
POS = eval(re.search(r"POS = (\[.*?\])\n", src, re.S).group(1))
parts = build2.build_all()
def solids(pos):
    out = []
    for p, n, s in parts:
        if p == pos or (pos == "5" and p in ("5.1", "5.2")):
            out += list(s.Solids()) if hasattr(s, "Solids") else [s]
    return out
print("== Hinweispunkte (Schnitt, Ebene Y=+0,01) ==")
for nr, t, a, pt in POS:
    if nr in ("8", "9", "10"):      # nicht geschnitten: ganzes Teil in Ansicht, Strahl in Blickrichtung (+Y)
        ray = cq.Solid.makeCylinder(0.05, 400, Vector(pt[0], -200, pt[1]), Vector(0, 1, 0))
        hit = [s for s in solids(nr) if s.intersect(ray).Volume() > 1e-6]
    else:
        hit = [s for s in solids(nr) if s.isInside(Vector(pt[0], 0.01, pt[1]), 1e-4)]
    print(f"Pos {nr:>3} Punkt {pt}: {'OK' if hit else 'FEHLER - nicht im Teil'}")
# Pos 7 in der Vorderansicht: Strahl in -X durch (Y,Z)
u, v = -18.7, -47.8
ray = cq.Solid.makeCylinder(0.05, 400, Vector(-100, u, v), Vector(1, 0, 0))
h7 = any(s.intersect(ray).Volume() > 1e-6 for s in solids("7"))
print(f"Pos   7 Punkt ({u}, {v}) Vorderansicht: {'OK' if h7 else 'FEHLER'}")
print("== Schraffur benachbarter Teile ==")
d = pickle.load(open("gz_buch.pkl", "rb"))
from shapely.geometry import box
low = box(-1e3, -1e3, 1e3, 0)
polys = {}
for pos, p in d["polys"]:
    polys.setdefault(pos, []).append(p.intersection(low))
U = {k: unary_union(v) for k, v in polys.items()}
keys = sorted(U)
bad = 0
for i, a in enumerate(keys):
    for b in keys[i+1:]:
        dist = U[a].distance(U[b])
        if dist < 0.6:
            same = HATCH[a] == HATCH[b]
            sameang = HATCH[a][0] == HATCH[b][0]
            flag = "FEHLER gleiche Schraffur" if same else ("ok (gleicher Winkel, anderer Abstand)" if sameang else "ok")
            if same: bad += 1
            print(f"{a:>4} - {b:<4} Abstand {dist:.2f} mm  {HATCH[a]} / {HATCH[b]}  {flag}")
print("Fehler Schraffur:", bad)
