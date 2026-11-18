"""Erzeugt die Beispiel-DXF-Dateien in samples/ und eine unabhängige Referenz
(tests/reference.json) mit ezdxf. Nur für die Entwicklung nötig:
    pip install ezdxf && python3 tools/make-samples.py
Die Referenzlängen stammen aus ezdxf (Pfad-Flattening) und dienen als zweite,
vom KerfQuote-Parser unabhängige Implementierung.
"""
import json
import math
import os

import ezdxf
from ezdxf import path as ezpath
from ezdxf.disassemble import recursive_decompose

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "samples")
B90 = math.tan(math.pi / 8)  # Bulge für einen 90°-Bogen

GEOMETRY = {"LINE", "ARC", "CIRCLE", "LWPOLYLINE", "POLYLINE", "ELLIPSE", "SPLINE"}


def reference(doc, skip_layers=()):
    """Gesamtlänge und Bounding-Box aller Geometrie im Modellbereich (in Zeichnungseinheiten)."""
    total = 0.0
    xs, ys = [], []
    for e in recursive_decompose(doc.modelspace()):
        if e.dxftype() not in GEOMETRY or e.dxf.layer in skip_layers:
            continue
        p = ezpath.make_path(e)
        pts = list(p.flattening(distance=1e-5))
        total += sum(a.distance(b) for a, b in zip(pts, pts[1:]))
        xs += [v.x for v in pts]
        ys += [v.y for v in pts]
    return {
        "length": total,
        "bbox": [min(xs), min(ys), max(xs), max(ys)],
    }


def flansch():
    doc = ezdxf.new("R2010")
    doc.units = 4
    msp = doc.modelspace()
    msp.add_circle((0, 0), 60)
    msp.add_circle((0, 0), 20)
    for i in range(6):
        a = math.radians(60 * i)
        msp.add_circle((45 * math.cos(a), 45 * math.sin(a)), 4.5)
    return doc, {"pierces": 8, "netArea": math.pi / 4 * (120**2 - 40**2 - 6 * 9**2), "open": 0}


def halteblech():
    doc = ezdxf.new("R2010")
    doc.units = 4
    doc.layers.add("HILFSLINIE", color=1)
    doc.layers.add("BEMASSUNG", color=3)
    msp = doc.modelspace()
    msp.add_lwpolyline(
        [(10, 0, 0), (140, 0, B90), (150, 10, 0), (150, 70, B90),
         (140, 80, 0), (10, 80, B90), (0, 70, 0), (0, 10, B90)],
        format="xyb", close=True)
    for x0 in (30, 85):
        msp.add_lwpolyline(
            [(x0, 35, 0), (x0 + 20, 35, 1), (x0 + 20, 45, 0), (x0, 45, 1)],
            format="xyb", close=True)
    # Rechteckausschnitt aus vier einzelnen Linien, absichtlich ungeordnet und gemischt gerichtet
    msp.add_line((85, 70), (85, 55))
    msp.add_line((65, 55), (85, 55))
    msp.add_line((65, 70), (65, 55))
    msp.add_line((65, 70), (85, 70))
    msp.add_circle((75, 20), 6)
    msp.add_line((-10, 40), (160, 40), dxfattribs={"layer": "HILFSLINIE"})
    msp.add_text("Halteblech t=3", dxfattribs={"layer": "BEMASSUNG", "height": 5}).set_placement((20, 90))
    area = (150 * 80 - (4 - math.pi) * 100) - 2 * (200 + math.pi * 25) - 300 - math.pi * 36
    return doc, {"pierces": 5, "netArea": area, "open": 0, "skipLayers": ["HILFSLINIE"]}


def offene_kontur():
    doc = ezdxf.new("R2010")
    doc.units = 4
    msp = doc.modelspace()
    msp.add_line((0, 0), (80, 0))
    msp.add_line((80, 0), (80, 50))
    msp.add_line((80, 50), (0, 50))
    msp.add_line((0, 50), (0, 0.5))   # 0,5 mm Lücke zum Startpunkt
    msp.add_line((0, 0), (80, 0))     # exaktes Duplikat
    msp.add_line((40, 10), (40, 10))  # Linie mit Länge 0
    msp.add_circle((40, 25), 8)
    return doc, {"pierces": 2, "open": 1, "duplicates": 1, "zeroLength": 1,
                 "cutLength": 259.5 + 2 * math.pi * 8}


def zoll_platte():
    doc = ezdxf.new("R2010")
    doc.units = 1  # Zoll
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (4, 0), (4, 2), (0, 2)], close=True)
    msp.add_circle((2, 1), 0.25)
    return doc, {"pierces": 2, "netArea": (8 - math.pi * 0.0625) * 645.16, "open": 0, "scale": 25.4}


def block_insert():
    doc = ezdxf.new("R2010")
    doc.units = 4
    bohrung = doc.blocks.new("BOHRUNG")
    bohrung.add_circle((0, 0), 4)
    langloch = doc.blocks.new("LANGLOCH")
    langloch.add_lwpolyline([(-10, -4, 0), (10, -4, 1), (10, 4, 0), (-10, 4, 1)], format="xyb", close=True)
    paar = doc.blocks.new("PAAR")
    paar.add_blockref("BOHRUNG", (-8, 0))
    paar.add_blockref("BOHRUNG", (8, 0))
    msp = doc.modelspace()
    msp.add_line((0, 0), (100, 0))
    msp.add_line((100, 0), (100, 60))
    msp.add_line((100, 60), (20, 60))
    # Eckenrundung als Bogen mit Extrusionsrichtung (0,0,-1): im WKS Mittelpunkt (20,40), 90°..180°
    msp.add_arc((-20, 40), 20, 0, 90, dxfattribs={"extrusion": (0, 0, -1)})
    msp.add_line((0, 40), (0, 0))
    msp.add_blockref("BOHRUNG", (15, 15))
    msp.add_blockref("BOHRUNG", (85, 15), dxfattribs={"xscale": 1.5, "yscale": 1.5})
    msp.add_blockref("BOHRUNG", (15, 45), dxfattribs={"xscale": -1})
    msp.add_blockref("BOHRUNG", (85, 45), dxfattribs={"rotation": 45})
    msp.add_blockref("LANGLOCH", (50, 25), dxfattribs={"rotation": 90})
    msp.add_blockref("PAAR", (50, 50))
    outer = 6000 - (400 - math.pi * 100)
    holes = 3 * math.pi * 16 + math.pi * 36 + 2 * math.pi * 16 + (160 + math.pi * 16)
    return doc, {"pierces": 8, "netArea": outer - holes, "open": 0}


def uniform_cubic_closed(ctrl, per_segment=2000):
    """Geschlossener uniformer kubischer B-Spline in Matrixform (unabhängig von de Boor)."""
    n = len(ctrl)
    pts = []
    for i in range(n):
        p0, p1, p2, p3 = (ctrl[(i + k) % n] for k in range(4))
        for j in range(per_segment):
            t = j / per_segment
            b0 = (1 - t) ** 3 / 6
            b1 = (3 * t**3 - 6 * t**2 + 4) / 6
            b2 = (-3 * t**3 + 3 * t**2 + 3 * t + 1) / 6
            b3 = t**3 / 6
            pts.append((b0 * p0[0] + b1 * p1[0] + b2 * p2[0] + b3 * p3[0],
                        b0 * p0[1] + b1 * p1[1] + b2 * p2[1] + b3 * p3[1]))
    return pts


def poly_length(pts, closed=False):
    seq = list(zip(pts, pts[1:] + (pts[:1] if closed else [])))
    return sum(math.dist(a, b) for a, b in seq)


def poly_area(pts):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))) / 2


def spline_ellipse():
    doc = ezdxf.new("R2010")
    doc.units = 4
    msp = doc.modelspace()
    msp.add_line((0, 0), (100, 0))
    msp.add_line((100, 0), (100, 40))
    ctrl = [(100, 40), (80, 70), (60, 30), (40, 70), (20, 30), (0, 40)]
    spl = msp.add_open_spline(ctrl, degree=3)  # geklemmter B-Spline
    msp.add_line((0, 40), (0, 0))
    msp.add_ellipse((50, 18), major_axis=(20, 0), ratio=0.4)
    blob_ctrl = [(120, 0), (160, 0), (170, 30), (140, 50), (115, 30)]
    closed = msp.add_spline()
    closed.set_closed([(x, y, 0) for x, y in blob_ctrl], degree=3)  # periodisch, ungeklemmte Knoten

    # Referenz von Hand: ezdxf wertet ungeklemmte Splines außerhalb des gültigen
    # Parameterbereichs aus, deshalb hier Matrixform bzw. numerische Integration.
    sp = [(v.x, v.y) for v in ezpath.make_path(spl).flattening(distance=1e-6)]
    ell = [(50 + 20 * math.cos(2 * math.pi * k / 200000), 18 + 8 * math.sin(2 * math.pi * k / 200000))
           for k in range(200000)]
    blob = uniform_cubic_closed(blob_ctrl)
    length = 180 + poly_length(sp) + poly_length(ell, closed=True) + poly_length(blob, closed=True)
    outer = poly_area([(0, 0), (100, 0)] + sp)
    area = outer - math.pi * 20 * 8 + poly_area(blob)
    allpts = [(0, 0), (100, 0)] + sp + blob
    bbox = [min(p[0] for p in allpts), min(p[1] for p in allpts),
            max(p[0] for p in allpts), max(p[1] for p in allpts)]
    return doc, {"pierces": 3, "netArea": area, "open": 0, "refLength": length, "refBbox": bbox}


def r12_polyline():
    doc = ezdxf.new("R12")
    msp = doc.modelspace()
    msp.add_polyline2d(
        [(5, 0, 0), (55, 0, B90), (60, 5, 0), (60, 25, B90), (55, 30, 0), (5, 30, B90), (0, 25, 0), (0, 5, B90)],
        format="xyb", close=True)
    msp.add_circle((30, 15), 5)
    area = 60 * 30 - (4 - math.pi) * 25 - math.pi * 25
    return doc, {"pierces": 2, "netArea": area, "open": 0}


SAMPLES = {
    "flansch": flansch,
    "halteblech": halteblech,
    "offene-kontur": offene_kontur,
    "zoll-platte": zoll_platte,
    "block-insert": block_insert,
    "spline-ellipse": spline_ellipse,
    "r12-polyline": r12_polyline,
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    ref = {}
    for name, build in SAMPLES.items():
        doc, expected = build()
        doc.saveas(os.path.join(OUT, name + ".dxf"))
        r = reference(doc, skip_layers=expected.get("skipLayers", ()))
        scale = expected.get("scale", 1)
        if "refLength" in expected:
            r = {"length": expected.pop("refLength"), "bbox": expected.pop("refBbox")}
        r["length"] *= scale
        r["bbox"] = [v * scale for v in r["bbox"]]
        ref[name] = {**r, **expected}
        print(f"{name:16s} L={r['length']:.4f}  bbox={[round(v, 3) for v in r['bbox']]}")
    with open(os.path.join(ROOT, "tests", "reference.json"), "w") as f:
        json.dump(ref, f, indent=2)
