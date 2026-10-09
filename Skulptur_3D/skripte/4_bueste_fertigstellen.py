"""Hull-Volumen -> Büste: Kopf freistellen, Halsschnitt, Sockel, Maßstab, Glättung, STL."""
import sys
from pathlib import Path
import numpy as np
import trimesh
from scipy import ndimage
from skimage import measure

root = Path(sys.argv[1]); RES = int(sys.argv[2]); out = sys.argv[3]
HEIGHT_MM = float(sys.argv[4]) if len(sys.argv) > 4 else 235.0   # Scheitel (inkl. Haar) -> Kinn
THR = float(sys.argv[5]) if len(sys.argv) > 5 else 0.93
SMOOTH = int(sys.argv[6]) if len(sys.argv) > 6 else 10
FACES = int(sys.argv[7]) if len(sys.argv) > 7 else 200000

vol = np.load(root / f"frac_{RES}.npy") >= THR

# Komponente im Kopfzentrum
lab, _ = ndimage.label(vol)
c, r = RES // 2, RES // 16
core = lab[c - r:c + r, c - r:c + r, c - r:c + r]
ids, cnt = np.unique(core[core > 0], return_counts=True)
vol = lab == ids[np.argmax(cnt)]

top = np.where(vol.any((0, 1)))[0].max()
head = vol[:, :, top - RES // 4:top + 1]
L = max(np.ptp(np.argwhere(head[:, :, k]), 0).max() for k in range(head.shape[2]) if head[:, :, k].sum() > 20)
cx, cy = np.argwhere(head.any(2)).mean(0)

# Hintergrund weg: nur Zylinder um die Kopfachse
X, Y = np.ogrid[:RES, :RES]
cyl = (X - cx) ** 2 + (Y - cy) ** 2 <= (0.65 * L) ** 2
vol &= cyl[:, :, None]
# dünne Fahnen (abstehende Haarsträhnen, Maskenfehler) entfernen
ball = ndimage.iterate_structure(ndimage.generate_binary_structure(3, 1), 2)
vol = ndimage.binary_opening(vol, ball)

# Hals = kleinste Querschnittsfläche unterhalb des Kopfes
area = vol.sum((0, 1))
lo_k, hi_k = int(top - 1.3 * L), int(top - 0.7 * L)
neck = lo_k + int(np.argmin(area[lo_k:hi_k]))
cut = int(neck - 0.15 * L)
print(f"Scheitel z={top}, Hals z={neck}, Schnitt z={cut}, Kopflänge {L} Voxel")

vol[:, :, :cut] = False
lab, _ = ndimage.label(vol)
vol = lab == lab[int(cx), int(cy), top - 5] if lab[int(cx), int(cy), top - 5] else vol

# Sockel (Zylinder) + Hohlkehle
sl = np.argwhere(vol[:, :, cut])
px, py = sl.mean(0)
rad, hgt = 0.48 * L, int(round(0.12 * L))
disk = (X - px) ** 2 + (Y - py) ** 2 <= rad ** 2
vol = np.pad(vol, ((0, 0), (0, 0), (hgt + 2, 0)))
cut += hgt + 2
vol[:, :, cut - hgt:cut] |= disk[:, :, None]
for i in range(6):
    vol[:, :, cut + i] |= ndimage.binary_dilation(vol[:, :, cut + 6], iterations=6 - i) & disk
vol = ndimage.binary_fill_holes(vol)

verts, faces, _, _ = measure.marching_cubes(np.pad(vol, 2).astype(np.float32), 0.5)
mesh = trimesh.Trimesh(verts - 2, faces)
if mesh.volume < 0:
    mesh.invert()
trimesh.smoothing.filter_taubin(mesh, lamb=0.5, nu=-0.53, iterations=SMOOTH)
if FACES and len(mesh.faces) > FACES:
    mesh = mesh.simplify_quadric_decimation(face_count=FACES)
mesh.apply_scale(HEIGHT_MM / (top - neck))
b = mesh.bounds
mesh.apply_translation([-(b[0, 0] + b[1, 0]) / 2, -(b[0, 1] + b[1, 1]) / 2, -b[0, 2]])
mesh.fix_normals()
print("Dreiecke:", len(mesh.faces), "wasserdicht:", mesh.is_watertight,
      "Maße [mm]:", np.round(mesh.extents, 1), "Volumen [cm3]:", round(mesh.volume / 1000, 1),
      "Maßstab mm/Voxel:", round(HEIGHT_MM / (top - neck), 3))
mesh.export(out)
