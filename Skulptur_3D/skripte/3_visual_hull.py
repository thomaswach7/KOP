"""Visual Hull aus COLMAP-Posen + Personenmasken -> wasserdichte Büste als STL."""
import sys
from pathlib import Path
import cv2
import numpy as np
import pycolmap
import trimesh
from skimage import measure

root = Path(sys.argv[1])
out_stl = sys.argv[2]
RES = int(sys.argv[3]) if len(sys.argv) > 3 else 220
HEAD_MM = float(sys.argv[4]) if len(sys.argv) > 4 else 235.0   # Scheitel->Kinn real

rec = pycolmap.Reconstruction(str(root / "sparse" / "0"))
print(rec.summary())

def pose(img):
    p = img.cam_from_world
    p = p() if callable(p) else p
    return p.rotation.matrix(), np.asarray(p.translation)

# ---------- Masken laden + säubern ----------
excl = set((root / "exclude.txt").read_text().split()) if (root / "exclude.txt").exists() else set()
views = []
for img in rec.images.values():
    if img.name in excl:
        continue
    m = cv2.imread(str(root / "mask" / img.name.replace(".jpg", ".png")), 0)
    m = (m > 127).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        m = (lab == 1 + np.argmax(st[1:, 4])).astype(np.uint8)
    R, t = pose(img)
    views.append(dict(name=img.name, cam=rec.cameras[img.camera_id], R=R, t=t, m=m,
                      area=m.mean(), C=-R.T @ t))
views.sort(key=lambda v: v["name"])
areas = np.array([v["area"] for v in views])
med = np.array([np.median(areas[max(0, i - 4):i + 5]) for i in range(len(areas))])
good = areas > 0.6 * med
views = [v for v, g in zip(views, good) if g]
print(f"Ansichten: {len(good)} registriert, {good.sum()} mit plausibler Maske")

def project(v, X):
    Xc = X @ v["R"].T + v["t"]
    z = Xc[:, 2]
    uv = np.full((len(X), 2), -1.0)
    ok = z > 1e-6
    uv[ok] = np.asarray(v["cam"].img_from_cam(Xc[ok]))[:, :2]
    return uv, ok

# ---------- Orientierung: Orbit-Ebene, "oben" ----------
C = np.array([v["C"] for v in views])
c0 = C.mean(0)
_, _, Vt = np.linalg.svd(C - c0)
up = Vt[2]
cam_up = np.mean([-v["R"][1] for v in views], 0)        # -y der Kamera = Bild oben
if up @ cam_up < 0:
    up = -up

# Kopfzentrum: Punkt, der den Blickachsen am nächsten liegt
A = np.zeros((3, 3)); b = np.zeros(3)
for v in views:
    d = v["R"][2]
    P = np.eye(3) - np.outer(d, d)
    A += P; b += P @ v["C"]
center = np.linalg.solve(A, b)
radius = np.median(np.linalg.norm(C - center, axis=1))
print("Orbit-Radius (SfM-Einheiten):", radius)

# lokales Koordinatensystem: z = oben
ex = np.cross(up, [1, 0, 0]); ex /= np.linalg.norm(ex)
ey = np.cross(up, ex)
Bm = np.stack([ex, ey, up])               # welt -> lokal

half = 0.55 * radius
lin = np.linspace(-half, half, RES)
gx, gy, gz = np.meshgrid(lin, lin, lin, indexing="ij")
Ploc = np.stack([gx, gy, gz], -1).reshape(-1, 3)
Pw = Ploc @ Bm + center

inside = np.zeros(len(Pw), np.int32)
seen = np.zeros(len(Pw), np.int32)
for v in views:
    uv, ok = project(v, Pw)
    h, w = v["m"].shape
    u = np.round(uv[:, 0]).astype(int); vv = np.round(uv[:, 1]).astype(int)
    inimg = ok & (u >= 0) & (u < w) & (vv >= 0) & (vv < h)
    hit = np.zeros(len(Pw), bool)
    hit[inimg] = v["m"][vv[inimg], u[inimg]] > 0
    seen += inimg
    inside += hit
frac = np.where(seen > 0, inside / np.maximum(seen, 1), 0)
occ = (frac >= 0.93) & (seen >= 0.3 * len(views))
vol = occ.reshape(RES, RES, RES)
np.save(root / "seenfrac.npy", (seen / len(views)).reshape(RES, RES, RES))

np.save(root / f"occ_{RES}.npy", vol)
np.save(root / f"frac_{RES}.npy", frac.reshape(RES, RES, RES).astype(np.float32))
np.save(root / f"grid_{RES}.npy", np.concatenate([lin[[0, -1]], center, Bm.ravel(), [radius]]))
print("gespeichert")
