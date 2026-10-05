"""Baugruppe Fliehkraftkupplung, Pos. 1-8. Achse = globale X-Achse.
Vorderansicht (Ansicht 2): Blick von +X; Bildschirm rechts = +Y, oben = +Z."""
import math, cadquery as cq
from util import load
from cadquery import Location, Vector

X0 = 47.0          # axiale Mitte Fliehgewichte / Naben-Arme
R_PIN = 52.0       # Radius Bohrungen Antriebsnabe (104/2)

from OCP.gp import gp_Trsf
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
def tf(shape, M):
    t = gp_Trsf(); t.SetValues(*[float(v) for row in M for v in row])
    return cq.Shape.cast(BRepBuilderAPI_Transform(shape.wrapped, t, True).Shape())
def rotx(shape, deg):  return shape.rotate((0,0,0),(1,0,0),deg)

# ---------- Pos 1 Antriebsnabe ----------
def antriebsnabe():
    return rotx(load(1), 90)                  # Arme nach oben/unten, Nut nach +Y

# ---------- Pos 2 Abtriebsnabe (gespiegelt eingebaut: lokale Planfläche x=55 -> X=82) ----------
def abtriebsnabe():
    s = load(2).rotate((0,0,0),(0,0,1),180)   # x -> -x
    s = s.translate((137,0,0))                # X = 137 - x_lokal
    return rotx(s, 90)

# ---------- Pos 3 Gehaeuse (nach Zeichnung 14.2.5.4) ----------
def gehaeuse():
    L, Ra, Ri = 70.0, 85.0, 68.0
    g = (cq.Workplane("YZ").circle(Ra).circle(Ri).extrude(L))
    g = g.faces("<X or >X").edges("%CIRCLE").edges(cq.selectors.RadiusNthSelector(0)).chamfer(1.0)
    # 2 x 6 Gewindebohrungen M8 (Kernloch 6,8, Bohrtiefe 26, 118 Grad Spitze)
    tip = 3.4/math.tan(math.radians(59))
    drill = (cq.Workplane("XY").polyline([(0,0),(26,0),(26+tip,3.4),(26+tip,0)]))
    prof = cq.Workplane("XZ").polyline([(0,0),(0,3.4),(26,3.4),(26+tip,0)]).close().revolve(360,(0,0,0),(1,0,0))
    holes = None
    for k in range(6):
        a = math.radians(30+60*k); y, z = 75*math.cos(a), 75*math.sin(a)
        for side in (0,1):
            h = prof.val()
            if side: h = h.mirror("YZ").translate((L,0,0))
            h = h.translate((0,y,z))
            holes = h if holes is None else holes.fuse(h)
    return g.val().cut(holes).translate((12,0,0))

# ---------- Pos 4 Deckel ----------
def deckel():
    return rotx(load(4), 90)

# ---------- Pos 5 Fliehgewicht (5.1 Gewicht, 5.2 Belag) ----------
HOLE_L = (-47.88559214402024, -19.244699835932547)    # Bohrung Drehpunkt im STEP (lokal, exakt)
HOLE_R = ( 47.88559214402021, -19.244699835932572)
def _weight_tf(shape, pivot_deg):
    # lokal (x,y,z) -> global (X=z+X0, Y=x, Z=y)
    s = tf(shape, [[0,0,1,X0],[1,0,0,0],[0,1,0,0]])
    a_loc = math.degrees(math.atan2(HOLE_L[1], HOLE_L[0]))
    r_loc = math.hypot(*HOLE_L)
    s = rotx(s, pivot_deg - a_loc)
    d = R_PIN - r_loc
    return s.translate((0, d*math.cos(math.radians(pivot_deg)), d*math.sin(math.radians(pivot_deg))))
def weight_free_hole(pivot_deg):
    a_loc = math.degrees(math.atan2(HOLE_L[1], HOLE_L[0]))
    rot = pivot_deg - a_loc
    b = math.radians(math.degrees(math.atan2(HOLE_R[1], HOLE_R[0])) + rot)
    r = math.hypot(*HOLE_R); d = R_PIN - r
    p = math.radians(pivot_deg)
    return (r*math.cos(b)+d*math.cos(p), r*math.sin(b)+d*math.sin(p))
def fliehgewichte():
    sols = load(5).Solids()
    sols = sorted(sols, key=lambda s: s.Volume())   # [Belag, Gewicht]
    out = []
    for piv in (90, 270):
        out.append(("5.1", _weight_tf(sols[1], piv)))
        out.append(("5.2", _weight_tf(sols[0], piv)))
    return out

# Bolzenachsen (Y,Z): Drehpunkte 90/270 Grad, freie Enden
PIVOTS = [(0.0, R_PIN), (0.0, -R_PIN)]
FREE = [weight_free_hole(90), weight_free_hole(270)]
PINS = PIVOTS + FREE

# ---------- Pos 6 Scheibe 16 x 9 x 1,5 (nur auf Drehpunkt-Bolzen, beidseitig der Nabenarme) ----------
def scheiben():
    out = []
    for (y,z) in PIVOTS:
        for x in (38.5-1.5, 55.5):
            out.append(cq.Workplane("YZ").circle(8).circle(4.5).extrude(1.5).val().translate((x,y,z)))
    return out

# ---------- Pos 7 Zugfeder, gespannt eingebaut (Draht 1,1; De 8; Oesen in Bolzen-Einstich d=6,8) ----------
DW, DM = 1.1, 6.9          # Drahtdurchmesser, mittlerer Windungsdurchmesser
N_COILS = 13
EYE_RM = 3.4 + DW/2        # Oese liegt im Einstich Ø6,8
X_SPRING = (X0-25+2.85, X0+25-2.85)   # Oese im Einstich R0,6 (ca. 3 mm vom Bolzenende), Windungen frei vor Pos. 8
def _spring_local(L):
    """Feder entlang +x, Oesenmitten bei x=0 und x=L, Oesen in der x-y-Ebene."""
    off = EYE_RM + DW/2 + 0.3          # Oesenmitte -> Federkoerper
    body = L - 2*off
    pitch = body / N_COILS
    helix = cq.Wire.makeHelix(pitch, body, DM/2, center=Vector(0,0,0), dir=Vector(0,0,1))
    prof = cq.Wire.makeCircle(DW/2, center=Vector(DM/2,0,0), normal=Vector(0,1,0))
    coil = cq.Solid.sweep(prof, [], helix, isFrenet=True)
    coil = coil.rotate((0,0,0),(0,1,0),90).translate((off,0,0))
    eyes = []
    for cx in (0.0, L):
        t = cq.Solid.makeTorus(EYE_RM, DW/2, pnt=Vector(cx,0,0), dir=Vector(0,0,1))
        eyes.append(t)
    # Uebergang Oese -> Koerper (gerade Drahtstuecke)
    links = []
    for x1, x2 in ((EYE_RM, off), (L-off, L-EYE_RM)):
        links.append(cq.Solid.makeCylinder(DW/2, x2-x1+0.4, Vector(x1-0.2,0,0), Vector(1,0,0)))
    s = coil
    for e in eyes+links: s = s.fuse(e)
    return s
def zugfedern():
    out = []
    pairs = [(PIVOTS[0], FREE[1]), (PIVOTS[1], FREE[0])]
    pairs = []
    # Feder 1: Drehpunkt 90 Grad <-> freies Ende Gewicht B ; Feder 2: 270 Grad <-> freies Ende Gewicht A
    pairs = [(PIVOTS[0], FREE[1]), (PIVOTS[1], FREE[0])]
    for (a, b) in pairs:
        L = math.hypot(b[0]-a[0], b[1]-a[1])
        loc = _spring_local(L)                       # in lokaler x-y-Ebene, Achse x
        # lokal x -> Richtung a->b in Y-Z, lokal y -> senkrecht dazu in Y-Z, lokal z -> X
        ang = math.atan2(b[1]-a[1], b[0]-a[0])
        c, s_ = math.cos(ang), math.sin(ang)
        for xs in X_SPRING:
            M = ([[0,0,1,xs],[c,-s_,0,a[0]],[s_,c,0,a[1]]])
            out.append(tf(loc, M))
    return out

# ---------- Pos 8 Sicherungsscheibe DIN 6799 - 7 (s=0,9; Nut-d 7; Aussen-d 14,3; Oeffnung 5,84) ----------
def _rs():
    ring = cq.Workplane("XY").circle(7.15).circle(3.5).extrude(0.9)
    slot = cq.Workplane("XY").center(0, 6).rect(5.84, 12).extrude(0.9)
    return ring.cut(slot).val()
RING_X = (X0-17.21-0.9, X0+17.21)
def sicherungsscheiben():
    base = _rs()
    out = []
    for (y,z) in PINS:
        ang = math.degrees(math.atan2(z,y))        # Oeffnung radial nach aussen
        for xr in RING_X:
            # lokal z -> X, lokal y (Oeffnung) -> radial
            r = math.radians(ang)
            M = ([[0,0,1,xr],[-math.sin(r),math.cos(r),0,y],[math.cos(r),math.sin(r),0,z]])
            out.append(tf(base, M))
    return out

def build():
    parts = []   # (pos, name, shape)
    parts.append(("1","Antriebsnabe",antriebsnabe()))
    parts.append(("2","Abtriebsnabe",abtriebsnabe()))
    parts.append(("3","Gehaeuse",gehaeuse()))
    parts.append(("4","Deckel",deckel()))
    for i,(p,s) in enumerate(fliehgewichte()):
        parts.append((p, ("Gewicht" if p=="5.1" else "Belag")+f"_{i//2+1}", s))
    for i,s in enumerate(scheiben()): parts.append(("6",f"Scheibe_{i+1}",s))
    for i,s in enumerate(zugfedern()): parts.append(("7",f"Zugfeder_{i+1}",s))
    for i,s in enumerate(sicherungsscheiben()): parts.append(("8",f"Sicherungsscheibe_{i+1}",s))
    return parts
