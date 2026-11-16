"""Glyphen-Bibliothek aus der Schriftprobe (Foto 63c5a387) bauen."""
import sys, pickle, string
import numpy as np
import heft

S = '/root/.claude/uploads/a12a72ca-1e1f-5f0a-9d9d-c465b27ff07e/63c5a387-image.jpg'
OUT = sys.argv[1] if len(sys.argv) > 1 else 'lib.pkl'
KW = dict(pxmm=5.5, upscale=2, mode='darkline', thr=45, alpha=(30, 70))

low = list('abcdefghijklmnopqrstuvwxyz')
spec_low = [c for c in low]
spec_low[0] = {'a': [0, 1, 2, 3, 4]}
spec_low[22] = {'w': [0, 1, 2]}          # 4. 'w' wird vom Spaltenrand abgeschnitten
spec_low[24] = {'y': [0, 1, 2]}          # 4. 'y' liegt in der Großbuchstaben-Spalte
spec_low[25] = {'z': [0, 1, 2]}

up = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
spec_up = [c for c in up]
spec_up[22] = {'W': [1, 2, 3, 4]}         # Gruppe 0 = Rest vom kleinen w
spec_up[24] = {'Y': [1, 2, 3, 4], 'y': [0]}
spec_up[25] = {'Z': [1, 2, 3, 4], 'z': [0]}

spec_dig = list('0123456789') + ['#']
# Symbolzeilen: .  ,(lang)  ;oben ;unten  o  +  -  :oben :unten  ()
spec_sym = ['.', ',', '#', '#', '#', '+', '-', '#', '#', {'(': [0, 3], ')': [1, 4]}]

parts = [((300, 260, 500, 1730), spec_low), ((500, 260, 780, 1730), spec_up),
         ((770, 260, 1020, 830), spec_dig), ((770, 1030, 1100, 1560), spec_sym)]
lib, rep = {}, []
for box, spec in parts:
    seg = heft.segment_sample(S, box=box, **KW)
    # Einzelzeichen-Zeilen als dict (alle Gruppen) -> keine automatische Teilung/Lückensuche
    spec = [{sp: list(range(len(row['groups'])))} if isinstance(sp, str) and len(sp) == 1 and sp != '#' else sp
            for sp, row in zip(spec, seg['rows'])]
    l, r = heft.build_library(seg, spec, out='/dev/null')
    for ch, vs in l.items():
        lib.setdefault(ch, []).extend(vs)
    rep += r
pxmm = seg['pxmm']

# ---- Grundlinien: Unterlängen-Buchstaben sitzen mit dem Bauch auf der Linie
xh_chars = 'acemnorsuvwxz'
xh = np.median([v['bot'] - v['top'] for c in xh_chars for v in lib[c]])
for c in 'gjpqy':
    for v in lib[c]:
        v['base'] = float(v['top'] + xh)
for c in lib:
    if c not in 'gjpqy':
        for v in lib[c]:
            v['base'] = float(v['bot'])
dh = np.median([v['bot'] - v['top'] for c in '0123568' for v in lib[c]])
for v in lib['9']:
    v['base'] = float(min(v['bot'], (v['top'] + dh * 1.05 + v['bot']) / 2))   # halbe Unterlänge (5-mm-Zeilen)
print('x-Höhe %.2f mm, Ziffernhöhe %.2f mm' % (xh / pxmm, dh / pxmm))
print(' '.join(rep))
pickle.dump(dict(lib=lib, pxmm=pxmm), open(OUT, 'wb'))

# ---- Zusatz-Varianten aus dem Referenzsatz "Das ist ein Referenzsatz"
import cv2
seg = heft.segment_sample(S, box=(840, 1600, 1340, 1700), **KW)
ls, _ = heft.build_library(seg, [{'r': [9], 'e': [7, 10], 't': [4], 'R': [6], 'D': [0]}], out='/dev/null')
for c in 'etRD':
    for v in ls[c]: v['base'] = float(v['bot'])
    lib[c] += ls[c]
r0 = ls['r'][0]; r0['base'] = float(r0['bot'])


def warp_variant(v, shear=0.0, sx=1.0):
    """Zusätzliche Variante desselben echten Glyphs durch leichte Scherung/Streckung."""
    a = v['a']; h, w = a.shape; pad = 6
    A = np.array([[sx, -shear, pad + shear * h], [0, 1, pad]], np.float32)
    b = cv2.warpAffine(a, A, (int(w * sx + 2 * pad + abs(shear) * h), h + 2 * pad), flags=cv2.INTER_LINEAR)
    ys = np.where(b.max(1) > 0.25)[0]; xs = np.where(b.max(0) > 0.25)[0]
    nv = dict(v, a=b, x0=v['x0'] - pad, y0=v['y0'] - pad)
    nv.update(top=nv['y0'] + ys.min(), bot=nv['y0'] + ys.max(), base=v['base'], iy0=ys.min(), iy1=ys.max(),
              ix0=xs.min(), ix1=xs.max())
    return nv


# Probenzeile 'r' sieht wie 'm' aus -> nur das 'r' aus dem Satz + 2 leicht verzerrte Varianten davon
lib['r'] = [r0, warp_variant(r0, 0.12, 1.08), warp_variant(r0, -0.08, 0.92)]

# ---- schlechte Varianten entfernen (nach Sichtung des Kontaktblatts)
DROP = {'q': [3], 'z': [0, 3], 't': [1], 'H': [0, 2], 'T': [0], 'F': [1], 'Z': [0], 'S': [0],
        'G': [0], '4': [1], 'U': [3], 's': [3], 'k': [0, 2], 'l': [0], '2': [2], '5': [0]}
for c, idx in DROP.items():
    lib[c] = [v for i, v in enumerate(lib[c]) if i not in idx]
# ---- Streupunkte (Fremd-Krümel) aus den Glyphen entfernen
for c, vs in lib.items():
    if c in '.,': continue
    for v in vs:
        m = (v['a'] > 0.25).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
        if n <= 2: continue
        big = st[1:, 4].max()
        for k in range(1, n):
            if st[k, 4] < 0.08 * big:
                v['a'][cv2.dilate((lab == k).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0] = 0
        ys = np.where(v['a'].max(1) > 0.25)[0]; xs = np.where(v['a'].max(0) > 0.25)[0]
        v['iy0'], v['iy1'], v['ix0'], v['ix1'] = ys.min(), ys.max(), xs.min(), xs.max()

# ---- lokaler Maßstab pro Glyph (Perspektive der Probe!): Karo-Gitter der Probe tracken
img = heft.load(S)
nodes, _, _ = heft.track_grid(img, pitch=24)
nodes = heft.clean_nodes(nodes)
keys = np.array(list(nodes.keys())); P = np.array(list(nodes.values()))
up = KW['upscale']


def local_pitch(x, y):
    k = tuple(keys[np.argmin(np.hypot(P[:, 0] - x, P[:, 1] - y))])
    def d(a, b):
        return np.linalg.norm(nodes[a] - nodes[b]) if a in nodes and b in nodes else np.nan
    i, j = k
    px = np.nanmean([d((i + 1, j), k), d(k, (i - 1, j)), d((i + 1, j + 1), (i, j + 1))])
    py = np.nanmean([d((i, j + 1), k), d(k, (i, j - 1)), d((i + 1, j + 1), (i + 1, j))])
    return px, py


for c, vs in lib.items():
    for v in vs:
        px, py = local_pitch(v['cx'] / up, (v['top'] + v['bot']) / 2 / up)
        v['pxx'], v['pxy'] = px * up / 5.0, py * up / 5.0
allx = [v['pxx'] for vs in lib.values() for v in vs]; ally = [v['pxy'] for vs in lib.values() for v in vs]
print('lokale px/mm (hochskaliert): x %.2f-%.2f, y %.2f-%.2f' % (min(allx), max(allx), min(ally), max(ally)))
hts = {c: np.median([(v['bot'] - v['top']) / v['pxy'] for v in lib[c]]) for c in 'aenoxHEDT08'}
print('Höhen mm:', {c: round(h, 2) for c, h in hts.items()})
pickle.dump(dict(lib=lib, pxmm=pxmm), open(OUT, 'wb'))
print({c: len(v) for c, v in lib.items() if len(v) < 3})
