"""Zwischenvolumen nach jedem KE, genau in der Reihenfolge der Schritt-fuer-Schritt-Anleitung."""
import math, pickle, cadquery as cq
from cadquery import Vector
import replay as R
V = {}
def rec(teil, ke, s): V.setdefault(teil, []).append((ke, round(s.Volume()))); return s

# Pos 1
s = rec("pos1", "KE 1 Drehen", R.drehen(R.ANTRIEB))
s = rec("pos1", "KE 2 Rundung R2", R.pos1(stop=2))
rec("pos1", "KE 4 Arme", R.pos1(stop=4)); rec("pos1", "KE 5 Rundung R9", R.pos1(stop=5)); s = rec("pos1", "KE 6 Fuß", R.pos1(stop=6))
for yc in (52, -52): s = s.cut(cq.Solid.makeCylinder(4, 30, Vector(32, yc, 0), Vector(1, 0, 0)))
rec("pos1", "KE 7 Bohrungen", s); rec("pos1", "KE 8 Passfedernut", R.pos1())

# Pos 2
s = rec("pos2", "KE 1 Drehen", R.drehen(R.ABTRIEB))
s = rec("pos2", "KE 2 Rundung R10", R.rund(s, 10.0, [(43, 25)]))
s = rec("pos2", "KE 3 Rundung R5", R.rund(s, 5.0, [(55, 62.5), (55, 44.12)]))
s = rec("pos2", "KE 4 Rundung R2", R.rund(s, 2.0, [(0, 25), (43, 85)]))
s = rec("pos2", "KE 5 Fase", R.fase(s, 1.5, [(62, 68)]))
s = rec("pos2", "KE 6 Passfedernut", R.nut(s, 0, 54, 8.0, 18.3, richtung=1))
rec("pos2", "KE 7 Bohrung (1 Stück)", R.bohrbild(s, 43, 55, 9.0, n=1, senk=(15.0, 8.6)))
rec("pos2", "KE 8 Muster (6 Stück)", R.pos2())

# Pos 3
s = rec("pos3", "KE 1 Drehen", R.drehen([(0, 68), (70, 68), (70, 85), (0, 85)]))
s = rec("pos3", "KE 2 Fase", R.fase(s, 1.0, [(0, 68), (70, 68)]))
tip = 3.4/math.tan(math.radians(59))
prof = cq.Workplane("XZ").polyline([(0, 0), (0, 3.4), (26, 3.4), (26+tip, 0)]).close().revolve(360, (0, 0, 0), (1, 0, 0)).val()
def loch(s, k, seite):
    a = math.radians(30 + 60*k); y, z = 75*math.cos(a), 75*math.sin(a)
    return s.cut(prof.translate((0, y, z)) if seite == 0 else prof.mirror("YZ").translate((70, y, z)))
s = rec("pos3", "KE 3 Gewindebohrung (1 Stück)", loch(s, 0, 0))
for k in range(1, 6): s = loch(s, k, 0)
s = rec("pos3", "KE 4 Muster (6 Stück)", s)
rec("pos3", "KE 6 Spiegeln (12 Stück)", R.pos3())

# Pos 4
s = rec("pos4", "KE 1 Drehen", R.drehen(R.DECKEL))
s = rec("pos4", "KE 2 Rundung R5", R.rund(s, 5.0, [(12, 62.5), (12, 43.49)]))
s = rec("pos4", "KE 3 Rundung R2", R.rund(s, 2.0, [(0, 85)]))
s = rec("pos4", "KE 4 Fase", R.fase(s, 1.5, [(19, 68)]))
rec("pos4", "KE 5 Bohrung (1 Stück)", R.bohrbild(s, 0, 12, 9.0, n=1, senk=(15.0, 8.6)))
rec("pos4", "KE 6 Muster (6 Stück)", R.pos4())

# Pos 5.1
pol = R.pol
schuh = R.bogen_langloch(55.75, 8.5, 52.13, -27, 27).fuse(R.sektor(59.0, 62, 51, -27, 27)).clean()
s = rec("pos51", "KE 1 Schuh", schuh)
arm = R.bogen_langloch(51.5, 17, 67.5, 9, 18)
rec("pos51", "KE 3 Arm", schuh.fuse(arm).clean())
for z0, name in ((17, "KE 4 Planfläche außen"), (9, "KE 5 Planfläche innen")):
    for sg in (1, -1):
        ex, ey = pol(51.5, 67.5*sg); arm = arm.cut(cq.Solid.makeCylinder(9.0, 1.0, Vector(ex, ey, z0), Vector(0, 0, 1)))
    rec("pos51", name, schuh.fuse(arm).clean())
rec("pos51", "KE 6 Spiegeln", schuh.fuse(arm).fuse(arm.mirror("XY")).clean())
rec("pos51", "KE 7 Bohrungen", R.pos51())

# Pos 5.2
s = rec("pos52", "KE 1 Extrudieren", R.sektor(62, 65, 46, -27, 27)); rec("pos52", "KE 2 Fase", R.pos52())
# Pos 6, 12
rec("pos6", "KE 1 Extrudieren", R.pos6()); rec("pos12", "KE 1 Drehen", R.pos12())
# Pos 9
s = rec("pos9", "KE 1 Drehen", R.drehen([(0, 0), (0, 4), (50, 4), (50, 0)]))
s = rec("pos9", "KE 2 Nut", s.cut(R.drehen([(7, 3.5), (7, 4.1), (7.94, 4.1), (7.94, 3.5)])))
s = rec("pos9", "KE 3 Einstich", s.cut(cq.Solid.makeTorus(4.0, 0.6, pnt=Vector(3.0, 0, 0), dir=Vector(1, 0, 0))))
rec("pos9", "KE 5 Spiegeln", R.pos9())
# Pos 7
p7 = R.pos7(); sol = p7.Solids()
rec("pos7", "KE 1 Federkörper", sol[0]); rec("pos7", "KE 2 Öse 1", cq.Compound.makeCompound(sol[:2])); rec("pos7", "KE 4 Spiegeln (Öse 2)", p7)
pickle.dump(V, open("mb/zwischenvolumen.pkl", "wb"))
for k, v in V.items(): print(k, v)
