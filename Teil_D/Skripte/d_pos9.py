import pickle, math
from dimlib import *
d = pickle.load(open("p69.pkl", "rb"))
sh = Sheet("A4")
M = 2.0; OX, OY = 58.0, 185.0
T = lambda x, y: (OX + M*x, OY + M*y)
sh.polylines(d["v9"], T)
sh.cl(T(-3, 0), T(53, 0))
# oben: Kettenmasse
sh.dim(T(0, 4), T(2.4, 4), T(0, 8)[1], "2,4", "h", tpos=-0.9)
sh.dim(T(0, 4), T(7, 4), T(0, 13)[1], "7", "h")
sh.dim(T(7, 4), T(43, 4), T(0, 13)[1], "36|+0,3|0", "h")
sh.dim(T(2.4, 4), T(47.6, 4), T(0, 18.5)[1], "45,2", "h")
sh.dim(T(0, 4), T(50, 4), T(0, 24)[1], "(50)", "h")
# Durchmesser
sh.line([T(3.0, 3.4), T(-4, 3.4)]); sh.line([T(3.0, -3.4), T(-4, -3.4)])
sh.dim(T(-2, 3.4), T(-2, -3.4), T(-4, 0)[0], "Ø6,8", "v", ext1=False, ext2=False)
sh.dim(T(50, 4), T(50, -4), T(55, 0)[0], "Ø8h8", "v")
sh.line([T(42.5, 3.5), T(25, 3.5)]); sh.line([T(42.5, -3.5), T(25, -3.5)])
sh.dim(T(26, 3.5), T(26, -3.5), T(26, 0)[0], "Ø7 −0,09", "v", ext1=False, ext2=False, arrows_out=True, tpos=2.75)
# unten: Einstichbreiten
sh.dim(T(7, -4), T(7.94, -4), T(0, -9)[1], "0,94|+0,05|0", "h", tpos=-3.2)
sh.dim(T(42.06, -4), T(43, -4), T(0, -9)[1], "0,94|+0,05|0", "h", tpos=4.0)
sh.leader(T(3.0-0.42, -3.6), T(-4, -12), "R0,6", end_len=10)
# Oberflaechen
sh.surf_leader(T(20, 4.05), T(16, 30), "y")
gx, gy = 30, 120
sh.surf_symbol((gx, gy), "y"); sh.text(gx+12, gy+2, "=", 3.5); sh.surf_symbol((gx+21, gy), text="Rz 16")
sh.edge_symbols(130, 108)
sh.text(23, 55.2, "Oberflächen DIN EN ISO 1302, Werkstückkanten DIN ISO 13715", 3.0)
sh.text(23, 50, "Allgemeintoleranzen ISO 2768-mK", 3.0)
sh.titleblock("Zylinderstift (Pos. 9)", "14.2.5.9", "C45E", "2:1")
sh.save("Pos09_Zylinderstift.pdf", "prev_p9.png")
print("ok")
