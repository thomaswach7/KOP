import pickle
from dimlib import *
d = pickle.load(open("p69.pkl", "rb"))
sh = Sheet("A4")
M = 5.0; OX, OY = 92.0, 180.0
T = lambda x, y: (OX + M*x, OY + M*y)
sh.polylines(d["l6"], T)
for p in d["p6"]: sh.hatch(p, T, 45, 0.5)
sh.cl(T(-2, 0), T(3.5, 0))
sh.dim(T(0, 8), T(1.5, 8), T(0, 11)[1], "1,5 −0,1", "h", tpos=2.4)
sh.dim(T(1.5, 4.5), T(1.5, -4.5), T(4.5, 0)[0], "Ø9", "v")
sh.dim(T(1.5, 8), T(1.5, -8), T(7.5, 0)[0], "Ø16", "v")
sh.datum(T(1.5, -6.2), (1, 0), "A", length=4)
sh.gdt((T(-5.5, -6.2)[0]-27, T(0, -6.2)[1]-3.5), "parallel", "0,05", "A")
sh.line([(T(-5.5, 0)[0], T(0, -6.2)[1]), T(-0.02, -6.2)]); sh.arrow(T(-0.02, -6.2), T(-2, -6.2))
gx, gy = 30, 75
sh.surf_symbol((gx, gy), text="Rz 63")
sh.edge_symbols(130, 64)
sh.text(23, 55.2, "Oberflächen DIN EN ISO 1302, Werkstückkanten DIN ISO 13715", 3.0)
sh.text(23, 50, "Allgemeintoleranzen ISO 2768-mK", 3.0)
sh.titleblock("Scheibe (Pos. 6)", "14.2.5.7", "S235JR", "5:1")
sh.save("Pos06_Scheibe.pdf", "prev_p6.png")
print("ok")
