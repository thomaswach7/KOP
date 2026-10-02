import pickle, math
from dimlib import *
d = pickle.load(open("p7.pkl", "rb"))
sh = Sheet("A4")
M = 2.0; OX, OY = 85.0, 190.0
T = lambda x, y: (OX + M*x, OY + M*y)
sh.polylines(d["v7"], T)
sh.cl(T(-10, 0), T(26, 0))
for cx in (-3.0, 18.4): sh.cl(T(cx, -6), T(cx, 6))
sh.dim(T(-7, 0), T(0, -4), T(0, -9)[1], "7", "h")
sh.dim(T(0, -4), T(15.4, -4), T(0, -9)[1], "15,4", "h")
sh.dim(T(-2.0, 3.0), T(0, 4), T(0, 9)[1], "2", "h", tpos=2.2)
sh.dim(T(15.4, 4), T(15.4, -4), T(25, 0)[0], "Ø8", "v")
a = math.radians(-35); c = (18.4, 0); r = 3.45 + 0.55
tip = T(c[0] + r*math.cos(a), c[1] + r*math.sin(a))
sh.leader(tip, T(25, -9), "Ø1,1", end_len=12)
sh.text(OX+5, OY-40, "if = 13  (federnde Windungen)", 3.5)
sh.text(OX+5, OY-47, "Ösen: ganze deutsche Öse, beidseitig", 3.5)
sh.edge_symbols(130, 64)
sh.text(23, 55.2, "Werkstückkanten nach DIN ISO 13715", 3.0)
sh.text(23, 50, "Allgemeintoleranzen ISO 2768-mK", 3.0)
sh.titleblock("Zugfeder (Pos. 7)", "14.2.5.8", "46Si7 (Federstahl)", "2:1")
sh.save("Pos07_Zugfeder.pdf", "prev_p7.png")
print("ok")
