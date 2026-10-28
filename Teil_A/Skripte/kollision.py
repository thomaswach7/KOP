"""Kollisionspruefung aller Teile (paarweise, Bounding-Box-Vorfilter). Gewollt: Schrauben im Gewinde."""
import itertools, build2
parts = build2.build_all()
flat = []
for p, n, s in parts:
    subs = list(s) if p == "11" and hasattr(s, "__iter__") else [s]
    for i, sub in enumerate(subs): flat.append((p, n + ("" if len(subs) == 1 else f"#{i}"), sub))
bbs = [s.BoundingBox() for _, _, s in flat]
treffer = []
for i, j in itertools.combinations(range(len(flat)), 2):
    a, b = bbs[i], bbs[j]
    if a.xmax < b.xmin or b.xmax < a.xmin or a.ymax < b.ymin or b.ymax < a.ymin or a.zmax < b.zmin or b.zmax < a.zmin: continue
    v = flat[i][2].intersect(flat[j][2]).Volume()
    if v > 1e-3: treffer.append((round(v, 3), flat[i][1], flat[j][1]))
gewollt = [t for t in treffer if ("Zylinderschraube" in t[1] or "Zylinderschraube" in t[2]) and ("Gehaeuse" in t[1] + t[2] or "Gehäuse" in t[1] + t[2])]
rest = [t for t in treffer if t not in gewollt]
print("Teile:", len(flat), " Ueberschneidungen gesamt:", len(treffer), " davon Schraube/Gewinde (gewollt):", len(gewollt))
for t in sorted(rest, reverse=True): print("  ", t)
