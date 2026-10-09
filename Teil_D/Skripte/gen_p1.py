"""p1.pkl: Ansichten der Antriebsnabe MIT Freistichen (aus replay.pos1)."""
import pickle, cadquery as cq
from cadquery import Vector
import sys; sys.path.insert(0, "../Modellbaum/Skripte")
import replay, partviews
s = replay.pos1()
# Schnitt A-A: Ebene z=0 (Achse X + Arme Y), Betrachter bei +Z -> Haelfte z<=0 behalten
box = cq.Solid.makeBox(200, 200, 100, Vector(-50, -100, -100))
sec_l, sec_p = partviews.section_view(s, (0, 0, 1), (1, 0, 0), box, (0, 0, 0), (0, 0, 1))
# Vorderansicht: Blick entlang -X (Betrachter bei +X), rechts = -Z, oben = +Y
fv_l = partviews.project(s, (1, 0, 0), (0, 0, -1))
pickle.dump({"sec_l": sec_l, "sec_p": sec_p, "fv_l": fv_l}, open("p1.pkl", "wb"))
print(len(sec_l), len(sec_p), len(fv_l), s.Volume())
