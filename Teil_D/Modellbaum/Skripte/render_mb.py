"""Baut die Teile nach replay.py, speichert Volumen (mb/vol.pkl) und 3D-Bilder (mb/*_3d.png).
Aufruf: python3 render_mb.py [pos1 pos2 ...]  (ohne Argument: alle)"""
import sys, pickle, os
import replay as R
from rpart import render_shapes
grey = (0.78, 0.78, 0.80)
alle = ["pos1", "pos2", "pos3", "pos4", "pos51", "pos52", "pos6", "pos7", "pos9", "pos12"]
wahl = sys.argv[1:] or alle
vol = pickle.load(open("mb/vol.pkl", "rb")) if os.path.exists("mb/vol.pkl") else {}
for k in wahl:
    s = getattr(R, k)()
    vol[k] = s.Volume()
    if k in ("pos51", "pos52"): render_shapes([(s, grey if k == "pos51" else (0.6, 0.4, 0.25))], f"mb/{k}_3d.png", d=(0.6, 0.9, 1.0), up=(0, 1, 0))
    elif k == "pos7": render_shapes([(s, (0.85, 0.2, 0.2))], f"mb/{k}_3d.png", d=(-0.3, -0.5, 1.0), up=(0, 1, 0))
    else: render_shapes([(s, grey)], f"mb/{k}_3d.png", d=(-1, -1.2, 0.9))
    print(k, round(vol[k]), "gueltig" if s.isValid() else "UNGUELTIG", flush=True)
pickle.dump(vol, open("mb/vol.pkl", "wb"))
