"""Portrait -> Creo-importierbare CAD-Daten (DXF-Linienzeichnung + STL-Relief)."""
import sys
import cv2
import ezdxf
import numpy as np
from stl import mesh

src, out = sys.argv[1], sys.argv[2]

img = cv2.imread(src)
H, W = img.shape[:2]
crop = img[int(.02 * H):int(.66 * H), int(.24 * W):int(.86 * W)]
crop = cv2.resize(crop, None, fx=0.6, fy=0.6, interpolation=cv2.INTER_AREA)
h_px, w_px = crop.shape[:2]
gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

# ---------- Person freistellen (GrabCut) ----------
mask = np.zeros((h_px, w_px), np.uint8)
rect = (int(.06 * w_px), int(.02 * h_px), int(.88 * w_px), int(.97 * h_px))
cv2.grabCut(crop, mask, rect, np.zeros((1, 65)), np.zeros((1, 65)), 6, cv2.GC_INIT_WITH_RECT)
m = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
_, lab, st, _ = cv2.connectedComponentsWithStats(m)
m = np.where(lab == 1 + np.argmax(st[1:, 4]), 255, 0).astype(np.uint8)
cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
outline = max(cs, key=cv2.contourArea)
m = np.zeros_like(m)
cv2.drawContours(m, [outline], -1, 255, cv2.FILLED)          # Löcher (Augen) füllen
outline = cv2.approxPolyDP(outline, 1.5, True)

# ---------- Gesichtslinien ----------
g = cv2.bilateralFilter(gray, 9, 40, 9)
th = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 9)
ed = cv2.Canny(cv2.GaussianBlur(g, (5, 5), 0), 25, 60)
feat = cv2.bitwise_or(th, ed)
feat = cv2.bitwise_and(feat, cv2.erode(m, np.ones((11, 11), np.uint8)))
feat = cv2.morphologyEx(feat, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
_, lab, st, _ = cv2.connectedComponentsWithStats(feat)
keep = np.isin(lab, 1 + np.where(st[1:, 4] >= 25)[0])
feat = np.where(keep, 255, 0).astype(np.uint8)
skel = cv2.ximgproc.thinning(feat)

# Skelett in Einzel-Polylinien zerlegen (keine Doppellinien)
S = skel > 0
N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
def nb(y, x):
    return [(y + dy, x + dx) for dy, dx in N8
            if 0 <= y + dy < h_px and 0 <= x + dx < w_px and S[y + dy, x + dx]]
deg = {(y, x): len(nb(y, x)) for y, x in zip(*np.nonzero(S))}
seen = set()
paths = []
def walk(a, b):
    p = [a, b]
    seen.add(frozenset((a, b)))
    while deg[p[-1]] == 2:
        nxt = [q for q in nb(*p[-1]) if frozenset((p[-1], q)) not in seen]
        if not nxt:
            break
        seen.add(frozenset((p[-1], nxt[0])))
        p.append(nxt[0])
    return p
for v, d in deg.items():
    if d != 2:
        for q in nb(*v):
            if frozenset((v, q)) not in seen:
                paths.append(walk(v, q))
for v in deg:                                   # reine Schleifen
    for q in nb(*v):
        if frozenset((v, q)) not in seen:
            paths.append(walk(v, q))

# ---------- DXF schreiben ----------
H_MM = 200.0
s = H_MM / h_px
W_MM = w_px * s
def mm(x, y):
    return (float(x) * s, float(h_px - y) * s)

doc = ezdxf.new("R2010", setup=True)
doc.units = ezdxf.units.MM
doc.layers.add("KONTUR", color=7, lineweight=50)
doc.layers.add("DETAIL", color=7, lineweight=25)
doc.layers.add("RAHMEN", color=1)
msp = doc.modelspace()
preview = np.full((h_px, w_px), 255, np.uint8)

msp.add_lwpolyline([mm(*p[0]) for p in outline], close=True, dxfattribs={"layer": "KONTUR"})
cv2.polylines(preview, [outline], True, 0, 2)

n = 0
for p in paths:
    if len(p) < 8:
        continue
    arr = np.array([[x, y] for y, x in p], np.int32).reshape(-1, 1, 2)
    arr = cv2.approxPolyDP(arr, 0.9, False)
    msp.add_lwpolyline([mm(*q[0]) for q in arr], dxfattribs={"layer": "DETAIL"})
    cv2.polylines(preview, [arr], False, 0, 1)
    n += 1

r = 10.0
msp.add_lwpolyline([(-r, -r), (W_MM + r, -r), (W_MM + r, H_MM + r), (-r, H_MM + r)],
                   close=True, dxfattribs={"layer": "RAHMEN"})
doc.saveas(f"{out}/portrait_linien.dxf")
cv2.imwrite(f"{out}/vorschau_linien.png", preview)
print(f"DXF: 1 Kontur + {n} Detail-Polylinien, {W_MM:.1f} x {H_MM:.1f} mm")

# ---------- 3D: Lithophanie-Relief -> STL ----------
W3 = 100.0
H3 = W3 * h_px / w_px
T_MIN, T_MAX = 0.8, 3.0
res = 0.4
nx, ny = int(W3 / res), int(H3 / res)
gg = cv2.equalizeHist(cv2.GaussianBlur(gray, (3, 3), 0))
gg = cv2.resize(gg, (nx, ny), interpolation=cv2.INTER_AREA)
z = T_MIN + (1.0 - gg.astype(np.float32) / 255.0) * (T_MAX - T_MIN)   # dunkel = dick
z = z[::-1]

X, Y = np.meshgrid(np.linspace(0, W3, nx), np.linspace(0, H3, ny))
top = np.dstack([X, Y, z])
bot = np.dstack([X, Y, np.zeros_like(z)])

def grid(P, flip):
    a, b, c, d = P[:-1, :-1], P[:-1, 1:], P[1:, 1:], P[1:, :-1]
    t = np.concatenate([np.stack([a, b, c], -2).reshape(-1, 3, 3),
                        np.stack([a, c, d], -2).reshape(-1, 3, 3)])
    return t[:, ::-1] if flip else t
def wall(te, be, flip):
    a, b, c, d = te[:-1], te[1:], be[1:], be[:-1]
    t = np.concatenate([np.stack([a, d, c], 1), np.stack([a, c, b], 1)])
    return t[:, ::-1] if flip else t

T = np.concatenate([grid(top, False), grid(bot, True),
                    wall(top[0], bot[0], False), wall(top[-1], bot[-1], True),
                    wall(top[:, 0], bot[:, 0], True), wall(top[:, -1], bot[:, -1], False)])
m3 = mesh.Mesh(np.zeros(len(T), dtype=mesh.Mesh.dtype))
m3.vectors = T
m3.save(f"{out}/portrait_relief.stl")
print(f"STL: {len(T)} Dreiecke, {W3:.1f} x {H3:.1f} x {T_MAX} mm, Volumen {m3.get_mass_properties()[0]:.0f} mm3")
cv2.imwrite(f"{out}/vorschau_relief.png", gg)
