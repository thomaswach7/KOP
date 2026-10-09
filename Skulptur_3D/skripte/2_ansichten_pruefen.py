import sys, numpy as np, cv2, pycolmap
from pathlib import Path
from scipy import ndimage
root = Path("v30"); RES = 220
frac = np.load(root / f"frac_{RES}.npy"); g = np.load(root / f"grid_{RES}.npy")
lo, hi, center, Bm = g[0], g[1], g[2:5], g[5:14].reshape(3, 3)
occ = frac >= 0.9
lab, n = ndimage.label(occ); c = RES // 2; r = RES // 8
core = lab[c-r:c+r, c-r:c+r, c-r:c+r]; ids, cnt = np.unique(core[core > 0], return_counts=True)
occ = lab == ids[np.argmax(cnt)]
idx = np.argwhere(occ)
# nur Oberflächen-Voxel (empfindlich für Masken-Fehler)
surf = occ & ~ndimage.binary_erosion(occ)
idx = np.argwhere(surf)
lin = np.linspace(lo, hi, RES)
Pw = lin[idx] @ Bm + center
rec = pycolmap.Reconstruction(str(root / "sparse/0"))
res = []
for im in sorted(rec.images.values(), key=lambda i: i.name):
    p = im.cam_from_world(); R = p.rotation.matrix(); t = np.asarray(p.translation)
    cam = rec.cameras[im.camera_id]
    Xc = Pw @ R.T + t
    uv = np.asarray(cam.img_from_cam(Xc))[:, :2]
    m = cv2.imread(str(root / "mask" / im.name.replace(".jpg", ".png")), 0) > 127
    h, w = m.shape
    u = np.round(uv[:, 0]).astype(int); v = np.round(uv[:, 1]).astype(int)
    ok = (Xc[:, 2] > 0) & (u >= 0) & (u < w) & (v >= 0) & (v < h)
    out = ok.copy(); out[ok] = ~m[v[ok], u[ok]]
    res.append((im.name, ok.mean(), out.sum() / max(ok.sum(), 1)))
for nme, a, b in res:
    pass
bad=[n for n,a,b in res if b>0.15]; open(root/"exclude.txt","w").write("\n".join(bad)); print(len(bad),"ausgeschlossen")
