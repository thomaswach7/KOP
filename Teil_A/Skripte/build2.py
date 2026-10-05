"""Komplette Baugruppe Pos. 1-12. Baut auf build.py (Pos. 1-8) auf.
Achse = X. X = 0 an der Aussenflaeche des Deckels."""
import math, cadquery as cq
from cadquery import Vector
import build
from build import tf, rotx, X0, PINS

# ---- Korrektur Pos. 7/8 mit Bolzen-Einstichen laut Zeichnung 14.2.5.9 ----
# Bolzen 50 lang, mittig auf X0=47 -> Enden bei X=22 und X=72
PIN_L, PIN_X0 = 50.0, X0 - 25.0
build.RING_X = (PIN_X0 + 7.0 + 0.04, PIN_X0 + 50 - 7.94)          # Ring in Nut 0,94 (7 mm vom Ende)
build.X_SPRING = (PIN_X0 + 3.0, PIN_X0 + 50 - 3.0)              # Oese mittig im Einstich R0,6

# ---- Pos. 9 Zylinderstift ISO 2338 8 m6 x 50 (Ausfuehrung nach 14.2.5.9) ----
def stift_lokal():
    p = cq.Workplane("XY").circle(4).extrude(50).val()
    for zc in (3.0, 47.0):
        p = p.cut(cq.Solid.makeTorus(4.0, 0.6, pnt=Vector(0, 0, zc), dir=Vector(0, 0, 1)))
    for z0 in (7.0, 50 - 7.94):
        p = p.cut(cq.Workplane("XY").workplane(offset=z0).circle(5).circle(3.5).extrude(0.94).val())
    return p.rotate((0, 0, 0), (0, 1, 0), 90)            # Achse X, x 0..50
def zylinderstifte():
    s = stift_lokal()
    return [s.translate((PIN_X0, y, z)) for (y, z) in PINS]

# ---- Pos. 10 Zylinderschraube ISO 4762 M8 x 20 (dk 13, k 8, SW 6, t 4) ----
def schraube_lokal():
    head = cq.Workplane("YZ").circle(6.5).extrude(8).faces("<X").workplane().polygon(6, 6/math.cos(math.radians(30))).cutBlind(-4).val()
    shank = cq.Workplane("YZ").workplane(offset=8).circle(4).extrude(20).val()
    return head.fuse(shank)                               # Kopfoberseite bei x=0, Schaft bis x=28
def schrauben():
    s = schraube_lokal(); out = []
    for k in range(6):
        a = math.radians(30 + 60*k); y, z = 75*math.cos(a), 75*math.sin(a)
        out.append(s.translate((8.6 - 8.0, y, z)))                                      # Deckelseite: Kopf liegt auf Senkungsgrund X=8,6
        out.append(s.rotate((0, 0, 0), (0, 0, 1), 180).translate((137 - 51.6 + 8.0, y, z)))   # Abtriebsseite: Senkungsgrund X=85,4
    return out

# ---- Pos. 11 Rillenkugellager DIN 625 6009-2Z (d 45, D 75, B 16) vereinfacht ----
def lager_lokal():
    B = 16.0
    ir = cq.Workplane("YZ").circle(26.0).circle(22.5).extrude(B).edges().chamfer(0.8).val()
    orr = cq.Workplane("YZ").circle(37.5).circle(34.0).extrude(B).edges().chamfer(0.8).val()
    race = cq.Solid.makeTorus(30.0, 4.6, pnt=Vector(B/2, 0, 0), dir=Vector(1, 0, 0))
    ir, orr = ir.cut(race), orr.cut(race)
    balls = [cq.Solid.makeSphere(4.5, Vector(B/2, 30*math.cos(2*math.pi*i/12), 30*math.sin(2*math.pi*i/12)))
             for i in range(12)]
    shields = [cq.Workplane("YZ").workplane(offset=xo).circle(34.0).circle(26.6).extrude(0.6).val() for xo in (0.8, B - 1.4)]
    return [ir, orr] + balls + shields
def lager():
    out = []
    for x0 in (13.0, 64.995):   # rechts 0,005 mm Luft zur Schulter (reine Anlage)
        out.append([p.translate((x0, 0, 0)) for p in lager_lokal()])
    return out

# ---- Pos. 12 Filzring DIN 5419 fuer Welle 45 (fuellt die Nut Ø58 / 4H13 / 14 Grad im Deckel) ----
def filzring():
    pts = [(2.78, 22.5), (2.78, 23.0), (3.52, 28.98), (7.48, 28.98), (8.22, 23.0), (8.22, 22.5)]
    return cq.Workplane("XY").polyline(pts).close().revolve(360, (0, 0, 0), (1, 0, 0)).val()

def build_all():
    parts = build.build()
    for i, s in enumerate(zylinderstifte()): parts.append(("9", f"Zylinderstift_{i+1}", s))
    for i, s in enumerate(schrauben()): parts.append(("10", f"Zylinderschraube_{i+1}", s))
    for i, comp in enumerate(lager()):
        parts.append(("11", f"Rillenkugellager_{i+1}", cq.Compound.makeCompound(comp)))
    parts.append(("12", "Filzring", filzring()))
    return parts
