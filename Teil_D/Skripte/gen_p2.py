"""Ansichten Abtriebsnabe (Pos. 2) fuer d_pos2.py. Modell mit Freistichen aus replay.pos2 (wie Modellbaum-Anleitung),
um die Achse gedreht: Bohrungen oben/unten (+-Z), Passfedernut nach +Y.
Vorderansicht: Blick auf die Flanschseite (x = 72), rechts = +Y (Nut rechts), oben = +Z.
Schnitt A-A: Ebene y = 0 durch die zwei Bohrungen, Betrachter bei -Y (Nut bleibt sichtbar), rechts = +X (Nabe links)."""
import os, sys, pickle, cadquery as cq
from cadquery import Vector
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../Modellbaum/Skripte"))
import replay, partviews
s = replay.pos2().rotate((0, 0, 0), (1, 0, 0), -90)
keep = cq.Solid.makeBox(200, 200, 400, Vector(-50, 0, -200))            # y >= 0 behalten
sec_l, sec_p = partviews.section_view(s, (0, -1, 0), (1, 0, 0), keep, (0, 0, 0), (0, 1, 0))
fv_l = partviews.project(s, (1, 0, 0), (0, 1, 0), regularity=True)
pickle.dump({"sec_l": sec_l, "sec_p": sec_p, "fv_l": fv_l}, open("p2.pkl", "wb"))
print(len(sec_l), len(sec_p), len(fv_l), round(s.Volume(), 1))
