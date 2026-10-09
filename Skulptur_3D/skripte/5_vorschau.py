"""Einfacher Software-Renderer: STL aus mehreren Blickwinkeln schattiert als PNG."""
import sys
import cv2
import numpy as np
import trimesh

m = trimesh.load(sys.argv[1])
out = sys.argv[2]
V = m.vertices - m.bounds.mean(0)
F = m.faces
S = 400
tiles = []
for az in [0, 45, 90, 135, 180, 225, 270, 315]:
    a = np.radians(az)
    R = np.array([[np.cos(a), np.sin(a), 0], [-np.sin(a), np.cos(a), 0], [0, 0, 1]])
    P = V @ R.T                       # Blick entlang +y, z oben
    sc = 0.9 * S / (2 * np.abs(V).max())
    x = (P[:, 0] * sc + S / 2)
    y = (S / 2 - P[:, 2] * sc)
    tri = P[F]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    vis = n[:, 1] < 0
    Lt = np.array([-0.4, -1.0, 0.6]); Lt /= np.linalg.norm(Lt)
    shade = 0.15 + 0.85 * np.clip(n @ Lt, 0, 1)
    depth = tri[:, :, 1].mean(1)
    img = np.full((S, S), 255, np.uint8)
    for i in np.argsort(-depth):
        if not vis[i]:
            continue
        pts = np.stack([x[F[i]], y[F[i]]], 1).round().astype(np.int32)
        cv2.fillConvexPoly(img, pts, int(40 + 200 * shade[i]))
    cv2.putText(img, f"{az} deg", (8, 24), 0, 0.7, 0, 2)
    tiles.append(img)
cv2.imwrite(out, np.vstack([np.hstack(tiles[:4]), np.hstack(tiles[4:])]))
