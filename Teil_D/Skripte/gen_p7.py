"""Ansicht der Zugfeder (Pos. 7) fuer d_pos7.py: Feder aus Modellbaum/Skripte/replay.py (ganze deutsche Oesen,
mit dem Federkoerper verbunden), Blick auf die Oesenebene, Oeffnung oben wie in Vorlage 14.2.5.8."""
import os, sys, pickle
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../Modellbaum/Skripte"))
import replay as R
import hlr
s = R.pos7().Solids()
f = s[0].fuse(s[1]).fuse(s[2]).clean()
pickle.dump({"v7": hlr.project([f], (0, -1, 0), (1, 0, 0))}, open("p7.pkl", "wb"))
print("ok", round(f.Volume(), 1))
