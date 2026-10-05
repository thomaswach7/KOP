"""Baut jedes Teil genau mit den KE der Creo-Anleitung nach (zur Kontrolle der Anleitung).
Achse der Drehteile = X. Skizzen-Koordinaten (x, r)."""
import math, cadquery as cq
from cadquery import Vector

def drehen(pts):
    """pts: Punkte (x, r) oder ('A', mitte, ende) fuer einen Bogen."""
    w = cq.Workplane("XY").moveTo(*pts[0])
    for p in pts[1:]:
        if p[0] == "A": w = w.threePointArc(p[1], p[2])
        else: w = w.lineTo(*p)
    return w.close().revolve(360, (0, 0, 0), (1, 0, 0)).val()
S2 = math.sqrt(2)

def kanten(shape, x, r, tol=0.05):
    """Kreiskanten mit Mittelpunkt bei x und Radius r (fuer Rundung/Fase)."""
    out = []
    for e in shape.Edges():
        if e.geomType() == "CIRCLE":
            c = e.Center(); rr = e.radius()
            if abs(c.x - x) < tol and abs(rr - r) < tol: out.append(e)
    return out

def rund(shape, R, sel):
    es = [e for (x, r) in sel for e in kanten(shape, x, r)]
    return shape.fillet(R, es)

def fase(shape, d, sel):
    es = [e for (x, r) in sel for e in kanten(shape, x, r)]
    return shape.chamfer(d, None, es)

def bohrbild(shape, x0, x1, d, n=6, r=75, a0=0.0, senk=None):
    """n Bohrungen Ø d auf Lochkreis r, von x0 nach x1; senk=(D, tiefe) Senkung ab x0."""
    for k in range(n):
        a = math.radians(a0 + 360/n*k); y, z = r*math.cos(a), r*math.sin(a)
        lo, hi = min(x0, x1), max(x0, x1)
        shape = shape.cut(cq.Solid.makeCylinder(d/2, hi-lo, Vector(lo, y, z), Vector(1, 0, 0)))
        if senk:
            D, t = senk; s0 = x0 if x1 > x0 else x0 - t
            shape = shape.cut(cq.Solid.makeCylinder(D/2, t, Vector(s0, y, z), Vector(1, 0, 0)))
    return shape

def nut(shape, x0, x1, b, t_bottom, richtung=1):
    """Passfedernut: Breite b, Nutgrund bei Abstand t_bottom von der Achse (Richtung +Z bzw. -Z)."""
    z0 = 0 if richtung > 0 else -t_bottom
    box = cq.Solid.makeBox(x1-x0, b, t_bottom, Vector(x0, -b/2, z0))
    return shape.cut(box)


# ---------------- Freistich DIN 509 - E 0,6 x 0,3 (r 0,6 / t1 0,3 / f 2,5 / 15 Grad) ----------------
FR_R, FR_T, FR_F = 0.6, 0.3, 2.5
FR_RAMPE = FR_T / math.tan(math.radians(15))      # 1,12 mm axialer Auslauf
C45 = math.cos(math.radians(45))
def freistich(xs, R, seite, innen=False):
    """Punkte (x, r) des Freistichs an der Schulter-Planflaeche x = xs.
    R = Radius der Zylinderflaeche, seite = -1: Zylinder liegt links der Schulter, +1: rechts.
    innen = True: Bohrung (Einstich nach aussen). Reihenfolge: von der Zylinderflaeche zur Planflaeche."""
    sg = 1 if innen else -1                            # Richtung des Einstichs in r
    rb = R + sg*FR_T                                   # Einstichgrund
    xe = xs + seite*FR_F                               # Ende Auslauf auf der Zylinderflaeche
    xc = xs + seite*FR_R                               # Mittelpunkt Radius (axial)
    rc = rb - sg*FR_R                                  # Mittelpunkt Radius (radial)
    mid = (xc - seite*FR_R*C45, rc + sg*FR_R*C45)
    return [(xe, R), (xe - seite*FR_RAMPE, rb), (xc, rb), ("A", mid, (xs, rc))]

# ---------------- Pos. 3 Gehaeuse ----------------
def pos3():
    s = drehen([(0, 68), (70, 68), (70, 85), (0, 85)])
    s = fase(s, 1.0, [(0, 68), (70, 68)])
    tip = 3.4/math.tan(math.radians(59))
    prof = cq.Workplane("XZ").polyline([(0, 0), (0, 3.4), (26, 3.4), (26+tip, 0)]).close().revolve(360, (0, 0, 0), (1, 0, 0)).val()
    for k in range(6):
        a = math.radians(30 + 60*k); y, z = 75*math.cos(a), 75*math.sin(a)
        s = s.cut(prof.translate((0, y, z)))
        s = s.cut(prof.mirror("YZ").translate((70, y, z)))
    return s

# ---------------- Pos. 4 Deckel ----------------
def _rev(pts):
    """Freistich-Punkte in Gegenrichtung (Planflaeche -> Zylinderflaeche)."""
    p = [q for q in pts if q[0] != "A"]; a = [q for q in pts if q[0] == "A"][0]
    # pts = [xe, rampe, floor, (A, mid, face)] -> [face, (A, mid, floor), rampe, xe]
    return [a[2], ("A", a[1], p[2]), p[1], p[0]]
DECKEL = ([(0, 23), (0, 85), (12, 85)] + _rev(freistich(12, 68, +1)) + [(19, 68), (19, 62.5), (12, 62.5), (12, 43.49), (29, 42.01),
          (29, 37.5)] + freistich(13, 37.5, +1, innen=True) + [(13, 35), ("A", (13 - 2/S2, 33 + 2/S2), (11, 33)), (11, 23), (8.24, 23), (7.5, 29), (3.5, 29), (2.76, 23)])
def pos4():
    s = drehen(DECKEL)
    s = rund(s, 5.0, [(12, 62.5), (12, 43.49)])
    s = rund(s, 2.0, [(0, 85)])
    s = fase(s, 1.5, [(19, 68)])
    s = bohrbild(s, 0, 12, 9.0, senk=(15.0, 8.6))
    return s

# ---------------- Pos. 2 Abtriebsnabe ----------------
ABTRIEB = ([(0, 15), (0, 25), (43, 25), (43, 85), (55, 85)] + _rev(freistich(55, 68, +1)) + [(62, 68), (62, 62.5), (55, 62.5),
           (55, 44.12), (72, 42.63), (72, 37.5)] + freistich(56, 37.5, +1, innen=True) + [(56, 35), ("A", (56 - 2/S2, 33 + 2/S2), (54, 33)), (54, 15)])
def pos2():
    s = drehen(ABTRIEB)
    s = rund(s, 10.0, [(43, 25)])
    s = rund(s, 5.0, [(55, 62.5), (55, 44.12)])
    s = rund(s, 2.0, [(0, 25), (43, 85)])
    s = fase(s, 1.5, [(62, 68)])
    s = nut(s, 0, 54, 8.0, 18.3, richtung=1)
    s = bohrbild(s, 43, 55, 9.0, senk=(15.0, 8.6))
    return s

# ---------------- Pos. 1 Antriebsnabe ----------------
ANTRIEB = ([(0, 15), (0, 22.5)] + freistich(29, 22.5, -1) + [(29, 25.5), ("A", (29 + 2/S2, 27.5 - 2/S2), (31, 27.5)), (31, 38.5), (63, 38.5),
           (63, 27.5), ("A", (65 - 2/S2, 27.5 - 2/S2), (65, 25.5))] + _rev(freistich(65, 22.5, +1)) + [(81, 22.5), (81, 15)])
def pos1(stop=None):
    s = drehen(ANTRIEB)                                                        # KE1 Drehen
    s = rund(s, 2.0, [(31, 38.5), (63, 38.5)])                                 # KE2 Rundung R2 Koerperkanten
    if stop == 2: return s
    # KE3/4 Arme: Skizze auf DTM1 (x = 47), symmetrisch 17; Arme liegen auf +-Y
    arm = (cq.Workplane("YZ", origin=(47-8.5, 0, 0)).center(41, 0).rect(22, 18).extrude(17)
           .union(cq.Workplane("YZ", origin=(47-8.5, 0, 0)).center(52, 0).circle(9).extrude(17))).val()
    s = s.fuse(arm).fuse(arm.mirror("XZ"))
    if stop == 4: return s
    # KE5 Rundung R9: Armseiten (z = +-9) <-> Koerper R38,5
    yk = (38.5**2 - 9**2) ** 0.5
    es = [e for e in s.Edges() if e.geomType() == "LINE" and abs(abs(e.Center().z) - 9) < 0.05
          and abs(abs(e.Center().y) - yk) < 0.05]
    s = s.fillet(9.0, es)
    if stop == 5: return s
    # KE6 Fuss: symmetrisch 20, bis R39,5 (Breite 18)
    fuss = cq.Workplane("YZ", origin=(47-10, 0, 0)).center(34.75, 0).rect(9.5, 18).extrude(20).val()
    s = s.fuse(fuss).fuse(fuss.mirror("XZ")).clean()
    if stop == 6: return s
    for yc in (52, -52):                                                       # KE7 Bohrung Ø8H8
        s = s.cut(cq.Solid.makeCylinder(4, 30, Vector(32, yc, 0), Vector(1, 0, 0)))
    s = nut(s, 0, 81, 8.0, 18.3, richtung=-1)                                  # KE8 Passfedernut
    return s

# ---------------- Pos. 5.1 Gewicht ----------------
def sektor(r1, r2, half_deg, z0, z1):
    a = math.radians(half_deg)
    w = (cq.Workplane("XY").workplane(offset=z0)
         .moveTo(r1*math.sin(-a), -r1*math.cos(a)).lineTo(r2*math.sin(-a), -r2*math.cos(a))
         .threePointArc((0, -r2), (r2*math.sin(a), -r2*math.cos(a)))
         .lineTo(r1*math.sin(a), -r1*math.cos(a)).threePointArc((0, -r1), (r1*math.sin(-a), -r1*math.cos(a))).close())
    return w.extrude(z1 - z0).val()
def pol(r, deg):  # Winkel von -Y aus, positiv nach +X
    return (r*math.sin(math.radians(deg)), -r*math.cos(math.radians(deg)))
def bogen_langloch(rm, b, half_deg, z0, z1):
    """Bogen-Langloch: Mittenradius rm, Breite b, Endmittelpunkte bei +-half_deg (von -Y), runde Enden R=b/2."""
    r1, r2, re = rm - b/2, rm + b/2, b/2
    s = sektor(r1, r2, half_deg, z0, z1)
    for sg in (1, -1):
        ex, ey = pol(rm, half_deg*sg)
        s = s.fuse(cq.Solid.makeCylinder(re, z1 - z0, Vector(ex, ey, z0), Vector(0, 0, 1)))
    return s
def pos51():
    s = bogen_langloch(55.75, 8.5, 52.13, -27, 27)               # KE1 Schuh (innen R51,5, Enden R4,25)
    s = s.fuse(sektor(59.0, 62, 51, -27, 27))                     # KE2 Belagsitz R62 ueber 102 Grad
    arm = bogen_langloch(51.5, 17, 67.5, 9, 18)                   # KE3 Arm R43/R60, Enden R8,5, 135 Grad
    s = s.fuse(arm).fuse(arm.mirror("XY"))                        # KE4 Spiegeln
    for sg in (1, -1):
        ex, ey = pol(51.5, 67.5*sg)
        for z0 in (9, 17, -10, -18):                              # KE5 Planflaechen R9, 1 mm tief
            s = s.cut(cq.Solid.makeCylinder(9.0, 1.0, Vector(ex, ey, z0), Vector(0, 0, 1)))
        s = s.fuse(cq.Solid.makeCylinder(8.5, 7, Vector(ex, ey, 10), Vector(0, 0, 1))).fuse(cq.Solid.makeCylinder(8.5, 7, Vector(ex, ey, -17), Vector(0, 0, 1)))
        s = s.cut(cq.Solid.makeCylinder(4, 60, Vector(ex, ey, -30), Vector(0, 0, 1)))   # KE6 Bohrung
    return s.clean()

# ---------------- Pos. 5.2 Belag ----------------
def pos52():
    s = sektor(62, 65, 46, -27, 27)
    for sg in (1, -1):
        p1 = pol(65, (46 - math.degrees(5/65))*sg); p2 = pol(63.5, 46*sg); p3 = pol(70, 46*sg); p4 = pol(70, (46 - math.degrees(5/65))*sg)
        tri = cq.Workplane("XY").workplane(offset=-30).polyline([p1, p2, p3, p4]).close().extrude(60).val()
        s = s.cut(tri)
    return s

# ---------------- Pos. 6 / 9 / 12 ----------------
def pos6():
    return cq.Workplane("YZ").circle(8).extrude(1.5).val().cut(cq.Solid.makeCylinder(4.5, 1.5, Vector(0, 0, 0), Vector(1, 0, 0)))
def pos9():
    s = drehen([(0, 0), (0, 4), (50, 4), (50, 0)])
    for x0 in (7.0, 50-7.94):
        s = s.cut(drehen([(x0, 3.5), (x0, 4.1), (x0+0.94, 4.1), (x0+0.94, 3.5)]))
    for xc in (3.0, 47.0):
        s = s.cut(cq.Solid.makeTorus(4.0, 0.6, pnt=Vector(xc, 0, 0), dir=Vector(1, 0, 0)))
    return s
def pos12():
    return drehen([(2.76, 22.5), (2.76, 23.0), (3.5, 29.0), (7.5, 29.0), (8.24, 23.0), (8.24, 22.5)])

# ---------------- Pos. 7 Zugfeder (ungespannt, nach Zeichnung) ----------------
def pos7(steigung=1.1, laenge=14.3):
    d, rm = 1.1, 3.45
    helix = cq.Wire.makeHelix(steigung*1.0005, laenge, rm, center=Vector(0, 0, 0), dir=Vector(0, 0, 1))
    prof = cq.Wire.makeCircle(d/2, center=Vector(rm, 0, 0), normal=Vector(0, 1, 0))
    body = cq.Solid.sweep(prof, [], helix, isFrenet=True).rotate((0, 0, 0), (0, 1, 0), 90).translate((0.55, 0, 0))
    gap = 2.0/rm
    out = [body]
    for cx, sg in ((-3.0, 1), (0.55 + laenge + 0.55 + 3.0, -1)):
        a0 = math.pi/2 + sg*gap/2 if sg > 0 else math.pi/2 - gap/2
        traj = cq.Workplane("XY").moveTo(cx + rm*math.cos(math.pi/2 + gap/2*sg), rm*math.sin(math.pi/2 + gap/2*sg))
        mid = (cx + rm*math.cos(math.pi/2 + math.pi*sg), rm*math.sin(math.pi/2 + math.pi*sg))
        end = (cx + rm*math.cos(math.pi/2 - gap/2*sg + 2*math.pi*sg*0), rm*math.sin(math.pi/2 - gap/2*sg))
        traj = traj.threePointArc(mid, end).val()
        start = traj.startPoint(); tng = traj.tangentAt(0)
        sec = cq.Wire.makeCircle(d/2, center=start, normal=tng)
        out.append(cq.Solid.sweep(sec, [], cq.Wire.assembleEdges([traj])))
    return cq.Compound.makeCompound(out)
