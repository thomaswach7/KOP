"""Ansichten Antriebsnabe wie Buchzeichnung 14.2.5.2: Nut nach +Z (in der Vorderansicht links),
A-A als Halbschnitt (oben Ansicht, unten Schnitt). Modell mit Freistichen aus replay.pos1."""
import pickle, cadquery as cq
from cadquery import Vector
import sys; sys.path.insert(0, "../Modellbaum/Skripte")
import replay, partviews
s = replay.pos1().mirror("XY")                       # Nut von -Z nach +Z
# Halbschnitt: Betrachter bei +Z; entfernt wird der Quadrant y<0, z>0
box = cq.Solid.makeBox(200, 100, 100, Vector(-50, -100, 0))
sec_l, sec_p = partviews.half_section_view(s, (0, 0, 1), (1, 0, 0), box, (0, 0, 0), (0, 0, 1), regularity=True)
fv_l = partviews.project(s, (1, 0, 0), (0, 0, -1), regularity=True)   # Blick von +X: rechts = -Z, oben = +Y
pickle.dump({"sec_l": sec_l, "sec_p": sec_p, "fv_l": fv_l}, open("p1_buch.pkl", "wb"))
print(len(sec_l), len(sec_p), len(fv_l), round(s.Volume(), 1))
