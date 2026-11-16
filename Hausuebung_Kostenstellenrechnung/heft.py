"""heft.py – Handschrift aus Schriftprobe auf leere Heftfotos setzen.
Abhängigkeiten: pip install --break-system-packages opencv-python-headless scipy pillow pillow-heif numpy
"""
import math, random, pickle
from collections import deque
import numpy as np, cv2
from PIL import Image, ImageOps
from scipy.interpolate import RBFInterpolator

try:
    import pillow_heif; pillow_heif.register_heif_opener()
except ImportError:
    pass


# =========================================================== 0. Laden
def load(path, rotate180=False):
    """Bild (auch HEIC) laden, EXIF-Drehung anwenden, als BGR float32 zurückgeben."""
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    if rotate180: im = im.rotate(180)
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR).astype(np.float32)


# =========================================================== 1. Tinte vom Papier trennen
def ink_map(img, mode='blue'):
    """Tintenstärke pro Pixel relativ zur Umgebung.
    mode='blue': Blau minus Rot (blaue Tinte; graue Karolinien fallen weg).
    mode='dark': Dunkelheit (schwarze Tinte; Karolinien danach per Schwellwert/Strichbreite trennen)."""
    if mode == 'blue':
        C = img[..., 0] - img[..., 2]
        bg = cv2.GaussianBlur(cv2.erode(C, np.ones((25, 25), np.uint8)), (0, 0), 15)
        return C - bg
    G = img.mean(2)
    bg = cv2.GaussianBlur(cv2.dilate(G, np.ones((25, 25), np.uint8)), (0, 0), 15)
    d = bg - G
    if mode == 'darkline':
        # dunkle (fast graue) Kulitinte: lange waagrechte/senkrechte Strukturen (= Karolinien) per
        # Öffnung mit langem Linien-Kern schätzen und abziehen; Buchstabenstriche sind kürzer als der Kern
        k = 81; lines = np.zeros_like(d)
        for ang in (-4, -2, 0, 2, 4):
            for base in (0, 90):
                t = math.radians(base + ang); ker = np.zeros((k, k), np.uint8); c = k // 2
                dx, dy = math.cos(t) * c, math.sin(t) * c
                cv2.line(ker, (int(round(c - dx)), int(round(c - dy))), (int(round(c + dx)), int(round(c + dy))), 1, 1)
                lines = np.maximum(lines, cv2.morphologyEx(d, cv2.MORPH_OPEN, ker))
        return d - lines
    thin = cv2.morphologyEx(d, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))   # 1-px-Karolinien dämpfen
    return thin


# =========================================================== 2./3. Glyphen-Bibliothek
def grid_pitch_px(img):
    """Kästchengröße (px pro 5 mm) über Autokorrelation in einem leeren Bereich (Mitte unten)."""
    R = img[..., 2]; h, w = R.shape
    reg = R[int(h * .75):int(h * .95), int(w * .15):int(w * .85)]
    p = reg.mean(0) - reg.mean()
    ac = np.correlate(p, p, 'full')[len(p) - 1:]
    lag = np.argmax(ac[20:200]) + 20
    k = 10; lo, hi = lag * k - 25, lag * k + 25
    return (np.argmax(ac[lo:hi]) + lo) / k if hi < len(ac) else float(lag)


def segment_sample(sample_path, thr=22, min_x=None, mode='blue', rotate180=False, box=None, pxmm=None, upscale=1,
                   alpha=(10, 40)):
    """Schriftprobe -> Zeilen -> Zeichen-Gruppen. Rückgabe dict mit allem, was build_library braucht.
    box=(x0,y0,x1,y1): nur diesen Bereich auswerten (Koordinaten im Originalfoto, z.B. eine Spalte der Probe).
    upscale: niedrig aufgelöste Proben (< 8 px/mm) vorher vergrößern, damit die Pixel-Konstanten passen."""
    img = load(sample_path, rotate180)
    if pxmm is None: pxmm = grid_pitch_px(img) / 5.0
    if upscale != 1:
        img = cv2.resize(img, None, fx=upscale, fy=upscale, interpolation=cv2.INTER_CUBIC); pxmm *= upscale
        if box: box = tuple(int(v * upscale) for v in box)
        if min_x: min_x = int(min_x * upscale)
    cd = ink_map(img, mode)
    mask = (cd > thr).astype(np.uint8)
    if min_x: mask[:, :min_x] = 0
    if box:
        bx0, by0, bx1, by1 = box; keep = np.zeros_like(mask); keep[by0:by1, bx0:bx1] = 1; mask *= keep
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask, 8)
    comps = [dict(i=i, x=st[i, 0], y=st[i, 1], w=st[i, 2], h=st[i, 3], a=st[i, 4]) for i in range(1, n) if st[i, 4] > 25]
    prof = mask.sum(1)                                   # Tintenpixel pro Bildzeile
    rows, inrow = [], False
    for y, v in enumerate(prof):
        if v > 3 and not inrow: s0, inrow = y, True
        elif v <= 3 and inrow:
            if y - s0 > 1.6 * pxmm: rows.append((s0, y))
            inrow = False
    out = []
    for ry0, ry1 in rows:
        cs = sorted([c for c in comps if ry0 <= c['y'] + c['h'] / 2 <= ry1], key=lambda c: c['x'])
        groups = []                                      # Flecken -> Zeichen (horizontale Überlappung)
        for c in cs:
            x0, x1 = c['x'], c['x'] + c['w']
            if groups:
                g = groups[-1]; ov = min(x1, g['x1']) - max(x0, g['x0'])
                if ov > 0.3 * min(c['w'], g['x1'] - g['x0']) or ((c['a'] < 400 or g['a'] < 400) and ov > -4):
                    g['ids'].append(c['i']); g['x0'] = min(g['x0'], x0); g['x1'] = max(g['x1'], x1)
                    g['y0'] = min(g['y0'], c['y']); g['y1'] = max(g['y1'], c['y'] + c['h']); g['a'] += c['a']
                    continue
            groups.append(dict(ids=[c['i']], x0=x0, x1=x1, y0=c['y'], y1=c['y'] + c['h'], a=c['a']))
        for g in groups: g['fill'] = g['a'] / max(1, (g['x1'] - g['x0']) * (g['y1'] - g['y0']))
        out.append(dict(y0=ry0, y1=ry1, groups=groups))
    return dict(img=img, cd=cd, lab=lab, pxmm=pxmm, rows=out, alpha=alpha)


def inspect_sample(seg, path='rows.png'):
    """Kontrollbild: jede Zeile mit nummerierten Gruppen (für manuelle Zuordnung)."""
    from PIL import ImageDraw
    strips = []
    gx0 = max(0, min(g['x0'] for r in seg['rows'] for g in r['groups']) - 60)
    gx1 = max(g['x1'] for r in seg['rows'] for g in r['groups']) + 20
    for r, row in enumerate(seg['rows']):
        y0, y1 = max(0, row['y0'] - 30), row['y1'] + 10
        a = np.clip((seg['cd'][y0:y1, gx0:gx1] - seg['alpha'][0]) / seg['alpha'][1], 0, 1)
        im = Image.fromarray(((1 - a) * 255).astype(np.uint8)).convert('RGB'); d = ImageDraw.Draw(im)
        d.text((5, 5), f'Z{r}', fill=(255, 0, 0))
        for gi, g in enumerate(row['groups']):
            d.rectangle([g['x0'] - gx0, g['y0'] - y0, g['x1'] - gx0, g['y1'] - y0], outline=(0, 160, 0))
            d.text((g['x0'] - gx0, 2), str(gi), fill=(200, 0, 0))
        strips.append(im)
    W = max(s.width for s in strips); H = sum(s.height for s in strips)
    out = Image.new('RGB', (W, H), 'white'); y = 0
    for s_ in strips: out.paste(s_, (0, y)); y += s_.height
    out.thumbnail((1600, 3000)); out.save(path)


def build_library(seg, rows_spec, out='lib.pkl', per=4):
    """rows_spec: pro Zeile ENTWEDER ein String mit einem Zeichen pro Satz ('abcdef' für 'aaaa bbbb ...',
    '#' = Kritzel/ignorieren; Sätze werden über die größten Lücken getrennt) ODER ein dict
    {'a': [0,1,2,3], 'b': [5,6], ...} mit Gruppennummern aus inspect_sample (bei Problemen)."""
    lab, pxmm = seg['lab'], seg['pxmm']
    a_lo, a_rng = seg.get('alpha', (10, 40))
    alpha_all = np.clip((seg['cd'] - a_lo) / float(a_rng), 0, 1).astype(np.float32)
    if len(seg['rows']) != len(rows_spec):
        raise ValueError(f"{len(seg['rows'])} Zeilen gefunden, rows_spec hat {len(rows_spec)}")
    lib, report = {}, []
    for row, spec in zip(seg['rows'], rows_spec):
        groups = row['groups']
        if isinstance(spec, dict):
            sets = [(ch, [groups[i] for i in idx]) for ch, idx in spec.items()]
        else:
            k = len(spec)
            rowmed = np.median([g['x1'] - g['x0'] for g in groups])
            # zusammengeklebte Zeichen (z.B. 'TTTT' als ein Fleck) in gleich breite Stücke teilen
            g2 = []
            for g in groups:
                nsplit = int(round((g['x1'] - g['x0']) / rowmed))
                if nsplit >= 2 and g['fill'] < 0.5:
                    w_ = (g['x1'] - g['x0']) / nsplit
                    for t in range(nsplit):
                        g2.append(dict(g, x0=int(g['x0'] + t * w_), x1=int(g['x0'] + (t + 1) * w_), a=g['a'] / nsplit, xr=True))
                else: g2.append(g)
            groups = g2
            if len(groups) == per * k:                    # Idealfall: genau 'per' Exemplare pro Zeichen
                sets = [(spec[t], groups[t * per:(t + 1) * per]) for t in range(k)]
                groups = None
        if groups is not None and not isinstance(spec, dict):
            gaps = [groups[i + 1]['x0'] - groups[i]['x1'] for i in range(len(groups) - 1)]
            cut = sorted(np.argsort(gaps)[::-1][:k - 1]) if k > 1 else []
            parts, st_ = [], 0
            for c_ in cut: parts.append(groups[st_:c_ + 1]); st_ = c_ + 1
            parts.append(groups[st_:])
            sets = list(zip(spec, parts))
        for ch, gs in sets:
            if ch == '#' or not gs: continue
            wmed = np.median([g['x1'] - g['x0'] for g in gs]); merged = []
            for g in gs:                                  # Bruchstücke (z.B. geteiltes %) verschmelzen
                if merged and g['x0'] - merged[-1]['x1'] < 10 and min(g['x1'] - g['x0'], merged[-1]['x1'] - merged[-1]['x0']) < .6 * wmed:
                    h_ = merged[-1]; h_['ids'] = h_['ids'] + g['ids']; h_['x1'] = max(h_['x1'], g['x1']); h_['a'] += g['a']
                else: merged.append(dict(g))
            gs = merged
            wmed = np.median([g['x1'] - g['x0'] for g in gs]); amed = np.median([g['a'] for g in gs])
            fmed = np.median([g['fill'] for g in gs])
            keep = [g for g in gs if (g['x1'] - g['x0']) <= 1.55 * wmed and g['a'] <= 2.0 * amed and g['fill'] <= 1.5 * fmed]
            report.append(f"{ch}:{len(keep)}/{len(gs)}")
            for g in keep:
                m = np.isin(lab, g['ids']).astype(np.uint8)
                if g.get('xr'):
                    m[:, :g['x0']] = 0; m[:, g['x1']:] = 0
                ys, xs = np.where(m)
                y0, x0 = max(0, ys.min() - 4), max(0, xs.min() - 4)
                y1, x1 = ys.max() + 5, xs.max() + 5
                mk = cv2.dilate(m, np.ones((5, 5), np.uint8))[y0:y1, x0:x1]
                a = alpha_all[y0:y1, x0:x1] * mk
                yy, xx = np.where(a > 0.25)
                lib.setdefault(ch, []).append(dict(a=a, x0=x0, y0=y0, top=y0 + yy.min(), bot=y0 + yy.max(),
                                                   cx=x0 + xx.mean(), row=(row['y0'], row['y1'])))
    # 3. Grundlinie pro Zeile: robuste Gerade durch Unterkanten (ohne Unterlängen)
    desc = set('gjpqyf')
    byrow = {}
    for ch, vs in lib.items():
        for v in vs: v['ch'] = ch; byrow.setdefault(v['row'], []).append(v)
    for r, vs in byrow.items():
        P = np.array([(v['cx'], v['bot']) for v in vs if v['ch'].isalnum() and v['ch'] not in desc], float)
        if len(P) >= 6 and np.ptp(P[:, 0]) > 300:
            good = np.ones(len(P), bool)
            for _ in range(4):
                A = np.c_[P[good, 0], np.ones(good.sum())]
                (kk, dd), *_ = np.linalg.lstsq(A, P[good, 1], rcond=None)
                res = np.abs(P[:, 1] - (kk * P[:, 0] + dd))
                good = res < max(8, 2 * np.median(res[good]))
            if abs(kk) > 0.05: kk, dd = 0.0, float(np.median(P[:, 1]))       # unplausibel schräg
            for v in vs: v['base'] = float(kk * v['cx'] + dd)
        else:
            for v in vs: v['base'] = float(v['bot'])                         # Symbolzeilen: eigene Unterkante
    for ch in ('€', '%', 'F'):
        for v in lib.get(ch, []): v['base'] = float(v['bot'])
    for ch, vs in lib.items():
        for v in vs:
            a = v['a']; ys = np.where(a.max(1) > 0.25)[0]; xs = np.where(a.max(0) > 0.25)[0]
            v['iy0'], v['iy1'], v['ix0'], v['ix1'] = ys.min(), ys.max(), xs.min(), xs.max()
    pickle.dump(dict(lib=lib, pxmm=pxmm), open(out, 'wb'))
    return lib, report


def contact_sheet_big(lib, path='sheet_big.png', chars=None, cols=6, cell=(110, 120)):
    """Großes Kontrollbild: pro Zeichen alle Varianten nebeneinander, rote Linie = Grundlinie."""
    from PIL import ImageDraw, ImageFont
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
    except OSError: font = ImageFont.load_default()
    chars = chars or sorted(lib); TW, TH = cell
    rows = (len(chars) + cols - 1) // cols; nv = max(len(lib[c]) for c in chars)
    im = Image.new('RGB', (cols * (40 + nv * TW), rows * TH), 'white'); d = ImageDraw.Draw(im)
    for idx, ch in enumerate(chars):
        cx, cy = (idx % cols) * (40 + nv * TW), (idx // cols) * TH
        d.text((cx + 6, cy + 40), ch, fill=(0, 0, 200), font=font)
        by_ref = int(TH * 0.72)
        d.line([(cx + 36, cy + by_ref), (cx + 36 + nv * TW, cy + by_ref)], fill=(255, 120, 120))
        for k, v in enumerate(lib[ch]):
            a = v['a']; oy = by_ref - int(v['base'] - v['y0'])
            t = Image.fromarray(((1 - a) * 255).astype(np.uint8)).convert('RGB')
            im.paste(Image.composite(t, im.crop((cx + 40 + k * TW, cy + oy, cx + 40 + k * TW + t.width, cy + oy + t.height)),
                                     Image.fromarray((a * 255).astype(np.uint8))), (cx + 40 + k * TW, cy + oy))
            d.text((cx + 40 + k * TW, cy + 2), str(k), fill=(150, 150, 150))
    im.save(path)


def contact_sheet(lib, pxmm, path='sheet.png'):
    """Kontrollbild: jede Zeile = ein Zeichen mit allen Varianten, Strich = Grundlinie."""
    from PIL import ImageDraw
    chars = sorted(lib); TW, TH = 110, 130
    per = (len(chars) + 1) // 2
    im = Image.new('L', (2 * (60 + 4 * TW), per * TH), 255); d = ImageDraw.Draw(im)
    for idx, ch in enumerate(chars):
        cx, cy = (idx // per) * (60 + 4 * TW), (idx % per) * TH
        d.text((cx + 8, cy + 50), repr(ch), fill=0)
        for k, v in enumerate(lib[ch][:4]):
            a = v['a']; s = min(1, (TH - 10) / a.shape[0], (TW - 10) / a.shape[1])
            t = Image.fromarray(((1 - a) * 255).astype(np.uint8)).resize((max(1, int(a.shape[1] * s)), max(1, int(a.shape[0] * s))))
            im.paste(t, (cx + 60 + k * TW, cy))
            by = int((v['base'] - v['y0']) * s)
            d.line([(cx + 60 + k * TW, cy + by), (cx + 60 + k * TW + 20, cy + by)], fill=100)
    im.save(path)


# =========================================================== 4./5. Schreib-Motor
RES, MARGIN = 14.0, 12.0          # Canvas-Pixel pro mm, Rand um das Gitter (mm)
CENTER = {'+': 2.1, '-': 2.1, '<': 2.1, '>': 2.1, '(': 2.1, ')': 2.1, '|': 2.4}
UML = {'ä': 'a', 'ö': 'o', 'ü': 'u', 'Ä': 'A', 'Ö': 'O', 'Ü': 'U'}


class Page:
    """Flache Seite in mm (Ursprung = linke obere Gitterecke, y nach unten)."""
    def __init__(self, lib, pxmm, W, H, seed=1, size_fix=None):
        self.lib, self.pxmm, self.W, self.H = lib, pxmm, W, H
        self.R = random.Random(seed); self.last = {}
        self.size_fix = size_fix or {}            # z.B. {'l': 6.0} = Zielhöhe in mm für zu kleine Zeichen
        self.ink = np.zeros((int((H + 2 * MARGIN) * RES), int((W + 2 * MARGIN) * RES)), np.float32)

    def px(self, x, y): return (x + MARGIN) * RES, (y + MARGIN) * RES

    def _stamp(self, a, M):
        h, w = a.shape
        cor = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]], np.float32) @ M.T
        x0, y0 = np.maximum(np.floor(cor.min(0)).astype(int) - 2, 0)
        x1 = min(int(np.ceil(cor[:, 0].max())) + 2, self.ink.shape[1]); y1 = min(int(np.ceil(cor[:, 1].max())) + 2, self.ink.shape[0])
        if x1 <= x0 or y1 <= y0: return
        M2 = M.copy(); M2[0, 2] -= x0; M2[1, 2] -= y0
        patch = cv2.warpAffine(a, M2, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderValue=0)
        reg = self.ink[y0:y1, x0:x1]; self.ink[y0:y1, x0:x1] = 1 - (1 - reg) * (1 - patch)

    def _variant(self, ch):
        idx = list(range(len(self.lib[ch])))
        if len(idx) > 1 and ch in self.last: idx.remove(self.last[ch])
        i = self.R.choice(idx); self.last[ch] = i
        return self.lib[ch][i]

    def _place(self, base, x, y, size, ang, scale=1.0, anchor='base', lift=0.0, draw=True, v=None, rot=None):
        """Ein Bibliothekszeichen setzen. anchor: base|center|top|bottom (vertikaler Bezugspunkt bei y-lift)."""
        R = self.R
        v = v or self._variant(base); a = v['a']
        f = size * scale * R.uniform(0.95, 1.05)
        kx = RES / v.get('pxx', self.pxmm) * f; ky = RES / v.get('pxy', self.pxmm) * f   # lokaler Probenmaßstab
        if base in self.size_fix:
            fx = self.size_fix[base] / ((v['bot'] - v['top']) / v.get('pxy', self.pxmm)); kx *= fx; ky *= fx
        th = math.radians(ang + (R.gauss(0, 2.2) if rot is None else rot))
        ax = v['ix0']
        ay = {'base': v['base'] - v['y0'], 'center': (v['iy0'] + v['iy1']) / 2, 'top': v['iy0'], 'bottom': v['iy1']}[anchor]
        tx, ty = self.px(x, y - lift + R.gauss(0, 0.18))
        c, s = math.cos(th), math.sin(th)
        M = np.array([[kx * c, -ky * s, 0], [kx * s, ky * c, 0]], np.float32)
        M[:, 2] = np.array([tx, ty]) - M[:, :2] @ np.array([ax, ay])
        if draw: self._stamp(a, M)
        return v, ky, M, (v['ix1'] - v['ix0']) * kx / RES

    def _dot(self, x, y, size, scale=0.6, draw=True):
        dv = self.lib['.'][self.R.randrange(len(self.lib['.']))]
        kd = RES / self.pxmm * size * scale
        Md = np.array([[kd, 0, 0], [0, kd, 0]], np.float32)
        px_, py_ = self.px(x + self.R.gauss(0, .12), y + self.R.gauss(0, .12))
        Md[:, 2] = np.array([px_, py_]) - Md[:, :2] @ np.array([(dv['ix0'] + dv['ix1']) / 2, (dv['iy0'] + dv['iy1']) / 2])
        if draw: self._stamp(dv['a'], Md)

    def glyph(self, ch, x, y, size=1.0, ang=0.0, draw=True):
        R = self.R; t = math.tan(math.radians(ang))
        if ch in UML:                                            # Umlaut = Grundbuchstabe + zwei Punkte
            v, k, M, w = self._place(UML[ch], x, y, size, ang, draw=draw)
            top = (v['iy0'] - (v['base'] - v['y0'])) * k / RES
            for f in (0.28, 0.72):
                self._dot(x + w * f, y + w * f * t + top - 1.0 * size, size, 0.55, draw)
            return x + w
        if ch in 'ij':                                           # i/j-Punkt (fehlt in der Probe)
            v, k, M, w = self._place(ch, x, y, size, ang, draw=draw)
            a = v['a']; r0 = int(v['iy0']); xs = np.where(a[r0:r0 + 4].max(0) > 0.3)[0]
            xt = xs.mean() if len(xs) else (v['ix0'] + v['ix1']) / 2
            pt = M @ np.array([xt, v['iy0'], 1.0])
            dx, dy = pt[0] / RES - MARGIN, pt[1] / RES - MARGIN
            self._dot(dx + 0.25 * size, dy - 1.2 * size, size, 0.6, draw)
            return x + w
        if ch == ':':
            self._dot(x + 0.3 * size, y - 0.4 * size, size, 0.6, draw)
            self._dot(x + 0.35 * size, y - 2.6 * size, size, 0.6, draw)
            return x + 0.7 * size
        if ch == '·':
            self._dot(x + 0.3 * size, y - 1.9 * size, size, 0.55, draw)
            return x + 0.6 * size
        if ch == '=':                                            # zwei eigene Minus-Striche
            v1, k1, _, w1 = self._place('-', x, y, size, ang, 0.75, 'center', 2.6 * size, draw, rot=R.gauss(0, 1.5))
            v2, k2, _, w2 = self._place('-', x + R.gauss(0, .2), y, size, ang, 0.75, 'center', 1.3 * size, draw, rot=R.gauss(0, 1.5))
            return x + max(w1, w2)
        if ch == '/':
            v, k, M, w = self._place(',', x, y, size, ang, 1.15, 'center', 2.1 * size, draw)
            return x + w
        if ch == ',':
            v, k, M, w = self._place(',', x, y, size, ang, 0.5, 'top', 0.9 * size, draw)
            return x + w
        if ch == '%':                                            # o / o aus eigenen Glyphen
            w0 = self._place('o', x, y, size, ang, 0.55, 'center', 3.2 * size, draw)[3]
            ws = self._place(',', x + 0.2 * size, y, size, ang, 1.15, 'center', 2.1 * size, draw)[3]
            w1 = self._place('o', x + ws * 0.62 + 0.2 * size, y, size, ang, 0.55, 'center', 0.9 * size, draw)[3]
            return x + max(ws + 0.2 * size, ws * 0.62 + 0.2 * size + w1)
        if ch == '€':                                            # fehlt in der Probe: Bogen + zwei Querstriche
            h = 4.0 * size * R.uniform(.93, 1.07); rx = 1.45 * size; cx = x + 0.3 * size + rx; cy = y - h / 2
            if draw:
                t0, t1 = math.radians(R.uniform(35, 50)), math.radians(R.uniform(305, 320))
                ts = np.linspace(t0, t1, 28)
                tl = math.tan(math.radians(ang))
                self.stroke([(cx + rx * math.cos(q), cy - h / 2 * math.sin(q) + (rx * math.cos(q)) * tl) for q in ts], w=0.17, alpha=0.9, jitter=0.05)
                for hh in (0.62, 0.40):
                    yy = y - hh * h + R.gauss(0, .08)
                    self.stroke([(x - 0.1 * size, yy), (cx + 0.35 * rx, yy - 0.15 + R.gauss(0, .08))], w=0.17, alpha=0.9, jitter=0.02)
            return cx + rx * 0.75
        base = ch
        if base not in self.lib: raise KeyError(f'Zeichen fehlt in der Probe: {ch!r}')
        if base in CENTER:
            v, k, M, w = self._place(base, x, y, size, ang, 1.0, 'center', CENTER[base] * size, draw)
        elif base == '.':
            v, k, M, w = self._place(base, x, y, size, ang, 0.65, 'bottom', 0.0, draw)
        else:
            v, k, M, w = self._place(base, x, y, size, ang, 1.0, 'base', 0.0, draw)
        return x + w

    def text(self, x, y, s, size=1.0, ang=0.0, draw=True, gap=1.1):
        """Schreibt s ab Grundlinienpunkt (x,y) mm entlang Winkel ang (Grad). Gibt End-x zurück."""
        R = self.R; t = math.tan(math.radians(ang)); x0 = x; drift = 0.0
        for ch in s:
            if ch == ' ': x += 3.8 * size * R.uniform(0.85, 1.25); continue
            drift += R.gauss(0, 0.06)
            x = self.glyph(ch, x, y + (x - x0) * t + drift, size, ang, draw) + gap * size * R.uniform(0.65, 1.3)
        return x - gap * size

    def width(self, s, size=1.0):
        st, last = self.R.getstate(), dict(self.last)
        w = self.text(0, 0, s, size, 0, draw=False)
        self.R.setstate(st); self.last = last
        return w

    def rtext(self, xr, y, s, size=1.0, ang=0.0):
        w = self.width(s, size); self.text(xr - w, y - w * math.tan(math.radians(ang)), s, size, ang); return xr - w

    # ---- Striche
    @staticmethod
    def curve(pts, n=30):
        pts = np.asarray(pts, float)
        if len(pts) == 2: return pts
        if len(pts) == 3:
            p0, pm, p1 = pts; c = 2 * pm - (p0 + p1) / 2; t = np.linspace(0, 1, n)[:, None]
            return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t ** 2 * p1
        P = np.vstack([pts[0], pts, pts[-1]]); out = []
        for i in range(1, len(P) - 2):
            p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
            for t in np.linspace(0, 1, 12, endpoint=False):
                out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
        out.append(pts[-1]); return np.array(out)

    def stroke(self, pts, w=0.21, alpha=0.9, jitter=0.12):
        R = self.R; pts = np.asarray(pts, float); dense = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            m = max(2, int(np.linalg.norm(b - a) / 1.5))
            dense += [a + (b - a) * t for t in np.linspace(0, 1, m + 1)[1:]]
        D = np.array(dense)
        if len(D) > 6:
            d = np.gradient(D, axis=0); nrm = np.c_[-d[:, 1], d[:, 0]]; nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
            wob = np.cumsum([R.gauss(0, jitter) for _ in D]); wob -= np.linspace(wob[0], wob[-1], len(wob))
            wob = cv2.GaussianBlur(wob.reshape(-1, 1).astype(np.float32), (1, 0), 3).ravel()
            D = D + nrm * wob[:, None]
        Pf = np.array([self.px(*p) for p in D])                  # nur im umgebenden Rechteck arbeiten (schnell)
        pad = int(w * RES) + 8
        x0 = max(int(Pf[:, 0].min()) - pad, 0); y0 = max(int(Pf[:, 1].min()) - pad, 0)
        x1 = min(int(Pf[:, 0].max()) + pad, self.ink.shape[1]); y1 = min(int(Pf[:, 1].max()) + pad, self.ink.shape[0])
        if x1 <= x0 or y1 <= y0: return
        SS = 8                                                   # Überabtastung: Strichbreite feiner als 1 px steuerbar
        layer = np.zeros(((y1 - y0) * SS, (x1 - x0) * SS), np.uint8)
        P = ((Pf - [x0, y0]) * SS * 4).astype(np.int32)
        cv2.polylines(layer, [P], False, 255, max(1, int(round(w * RES * SS))), cv2.LINE_AA, shift=2)
        layer = cv2.resize(layer, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA).astype(np.float32)
        a = cv2.GaussianBlur(layer / 255 * alpha * R.uniform(.85, 1), (0, 0), .7)
        reg = self.ink[y0:y1, x0:x1]; self.ink[y0:y1, x0:x1] = 1 - (1 - reg) * (1 - a)

    def line(self, x1, y1, x2, y2, **kw):
        R = self.R; L = math.hypot(x2 - x1, y2 - y1) + 1e-9; bow = R.gauss(0, .004 * L)
        nx, ny = -(y2 - y1) / L, (x2 - x1) / L
        self.stroke(self.curve([(x1 + R.gauss(0, .2), y1 + R.gauss(0, .2)), ((x1 + x2) / 2 + nx * bow, (y1 + y2) / 2 + ny * bow),
                                (x2 + R.gauss(0, .3), y2 + R.gauss(0, .3))]), **kw)

    def underline(self, x1, x2, y, double=False):
        self.line(x1 - .8, y + 1.3, x2 + 1, y + 1.3 + self.R.uniform(-.5, .5))
        if double: self.line(x1 - .3, y + 2.5, x2 + 1.5, y + 2.5 + self.R.uniform(-.5, .5))

    def result(self, x, y, s, size=1.0, ang=0.0):
        """Ergebnis schreiben + doppelt unterstreichen. Gibt (x_start, x_end) zurück."""
        x1 = self.text(x, y, s, size, ang)
        self.underline(x, x1, y + (x1 - x) * math.tan(math.radians(ang)) / 2 + .3, double=True)
        return x, x1

    def arrow(self, p0, p1, bend=0.0, via=None, head=2.2):
        """Pfeil p0->p1. bend = Krümmung (Anteil der Länge, +/-), via = Zwischenpunkte um Text herum."""
        R = self.R; p0, p1 = np.array(p0, float), np.array(p1, float)
        if via: pts = self.curve([p0] + [np.array(v, float) for v in via] + [p1])
        else:
            d = p1 - p0; L = np.linalg.norm(d); n = np.array([-d[1], d[0]]) / (L + 1e-9)
            pts = self.curve([p0, (p0 + p1) / 2 + n * bend * L, p1])
        self.stroke(pts)
        dv = pts[-1] - pts[-4]; dv /= np.linalg.norm(dv) + 1e-9
        for sg in (1, -1):
            a = math.radians(152 * sg + R.gauss(0, 6))
            r = np.array([dv[0] * math.cos(a) - dv[1] * math.sin(a), dv[0] * math.sin(a) + dv[1] * math.cos(a)])
            self.stroke([p1, p1 + r * head * R.uniform(.85, 1.15)], jitter=.03)

    def box(self, x1, y1, x2, y2):
        self.line(x1, y1, x2, y1); self.line(x2, y1, x2, y2); self.line(x2, y2, x1, y2); self.line(x1, y2, x1, y1)

    def ellipse(self, cx, cy, rx, ry):
        t0 = self.R.uniform(0, 6.28); ts = np.linspace(t0, t0 + 6.28 * 1.08, 60)
        self.stroke([(cx + rx * math.cos(t), cy + ry * math.sin(t)) for t in ts], jitter=.05)

    def frac(self, x, y, num, den, size=1.0, ang=0.0):
        """Bruch, Grundlinie y wie normaler Text. Gibt End-x zurück."""
        wn, wd = self.width(num, size), self.width(den, size); w = max(wn, wd) + 3
        t = math.tan(math.radians(ang)); by = y - 2.6 * size
        self.text(x + (w - wn) / 2, by - 1.6 * size + (w - wn) / 2 * t, num, size, ang)
        self.line(x, by, x + w, by + w * t)
        self.text(x + (w - wd) / 2, by + 7.6 * size + (w - wd) / 2 * t, den, size, ang)
        return x + w + 1.0

    def preview(self, path, scale=0.3):
        img = np.ones(self.ink.shape, np.float32); g = int(5 * RES); m = int(MARGIN * RES)
        img[m::g, :] = .82; img[:, m::g] = .82
        cv2.imwrite(path, cv2.resize(((img * (1 - self.ink)) * 255).astype(np.uint8), None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA))


# =========================================================== 6. Karo-Gitter im Foto finden
def track_grid(img, pitch=None, debug=None):
    """Findet alle Kreuzungen der Karolinien. Rückgabe: dict (i,j)->(x,y) px."""
    R = img[..., 2]; C = img[..., 0] - img[..., 2]
    s = (cv2.GaussianBlur(cv2.dilate(R, np.ones((11, 11), np.uint8)), (0, 0), 5) - R) \
        + 1.5 * (C - cv2.GaussianBlur(cv2.erode(C, np.ones((11, 11), np.uint8)), (0, 0), 5))
    s = np.clip(s, 0, 60)
    if pitch is None:
        reg = s[s.shape[0] // 3: 2 * s.shape[0] // 3, s.shape[1] // 3: 2 * s.shape[1] // 3]
        p = reg.mean(0) - reg.mean(); ac = np.correlate(p, p, 'full')[len(p) - 1:]
        pitch = float(np.argmax(ac[30:200]) + 30)
    L = int(pitch * 0.47) | 1; Wd = int(pitch * 0.36) | 1
    rh = cv2.blur(s, (L, 3)) - cv2.blur(s, (L, Wd))          # waagrechte Linien
    rv = cv2.blur(s, (3, L)) - cv2.blur(s, (Wd, L))          # senkrechte Linien
    H, W = s.shape; r0 = int(pitch * 0.16)

    def refine(p, r=r0):
        x, y = int(round(p[0])), int(round(p[1]))
        if x - r < 30 or y - r < 30 or x + r >= W - 30 or y + r >= H - 30: return None, 0, 0
        for _ in range(2):
            x = x - r + int(np.argmax(rv[y, x - r:x + r + 1]))   # x NUR über senkrechte Linie
            y = y - r + int(np.argmax(rh[y - r:y + r + 1, x]))   # y NUR über waagrechte Linie
        return np.array([x, y], float), rh[y, x], rv[y, x]

    p0, a, b = refine((W // 2, H // 2), int(pitch * .55))
    nodes = {(0, 0): p0}; hs, vs = [a], [b]; q = deque([(0, 0)]); dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    while q:
        i, j = q.popleft()
        for di, dj in dirs:
            key = (i + di, j + dj)
            if key in nodes: continue
            preds = []
            for ei, ej in dirs:                                   # Vorhersage aus ALLEN Nachbarn mitteln
                nb, nb2 = (key[0] - ei, key[1] - ej), (key[0] - 2 * ei, key[1] - 2 * ej)
                if nb in nodes:
                    preds.append(2 * nodes[nb] - nodes[nb2] if nb2 in nodes else nodes[nb] + np.array([pitch * ei, pitch * ej]))
            pred = np.mean(preds, 0)
            pr, a, b = refine(pred)
            if pr is None or a < .35 * np.median(hs[-300:]) or b < .35 * np.median(vs[-300:]): continue
            if np.linalg.norm(pr - pred) > pitch * .14: continue
            nodes[key] = pr; hs.append(a); vs.append(b); q.append(key)
    # Plausibilitätstest: Nachbarn ~1 Kästchen auseinander
    bad = 0
    for (i, j), p in nodes.items():
        for (di, dj), ax in (((1, 0), 0), ((0, 1), 1)):
            qn = nodes.get((i + di, j + dj))
            if qn is not None:
                d = qn - p
                if abs(d[1 - ax]) > .45 * pitch or not (.5 * pitch < d[ax] < 1.45 * pitch): bad += 1
    if debug:
        vis = img.astype(np.uint8).copy(); I = [k[0] for k in nodes]; J = [k[1] for k in nodes]
        for jj in range(min(J), max(J) + 1, 4):
            pts = np.array([p for (i, j), p in sorted(nodes.items()) if j == jj], np.int32)
            if len(pts) > 1: cv2.polylines(vis, [pts], False, (0, 0, 255), 4)
        for ii in range(min(I), max(I) + 1, 4):
            pts = np.array(sorted([p for (i, j), p in nodes.items() if i == ii], key=lambda p: p[1]), np.int32)
            if len(pts) > 1: cv2.polylines(vis, [pts], False, (0, 170, 0), 4)
        cv2.imwrite(debug, cv2.resize(vis, None, fx=.25, fy=.25, interpolation=cv2.INTER_AREA))
    return nodes, pitch, bad


def clean_nodes(nodes, frac=0.6):
    """Ausreißer-Stränge entfernen (z.B. durch die Spirale aufs Nachbarblatt): nur Zeilen/Spalten behalten,
    die mindestens frac * maximale Knotenzahl haben."""
    from collections import Counter
    for _ in range(2):
        cj = Counter(k[1] for k in nodes); mj = max(cj.values())
        nodes = {k: p for k, p in nodes.items() if cj[k[1]] >= frac * mj}
        ci = Counter(k[0] for k in nodes); mi = max(ci.values())
        nodes = {k: p for k, p in nodes.items() if ci[k[0]] >= frac * mi}
    return nodes


# =========================================================== 7./8. Abbildung + Einblenden
def grid_mapping(nodes):
    ij = np.array(list(nodes.keys()), float); xy = np.array(list(nodes.values()), float)
    i0, j0 = ij.min(0)
    mm = np.c_[(ij[:, 0] - i0) * 5, (ij[:, 1] - j0) * 5]
    W, H = (ij[:, 0].max() - i0) * 5, (ij[:, 1].max() - j0) * 5
    inv = RBFInterpolator(xy, mm, neighbors=40, smoothing=2.0, kernel='thin_plate_spline')   # Foto -> mm
    fwd = RBFInterpolator(mm, xy, neighbors=40, smoothing=2.0, kernel='thin_plate_spline')   # mm -> Foto
    return inv, fwd, W, H


def measure_ink(img, x0, y0, x1, y1):
    """Tintenfarbe als Verhältnis Tinte/Papier aus echter Schrift im Bereich (falls vorhanden)."""
    reg = img[y0:y1, x0:x1]; C = reg[..., 0] - reg[..., 2]
    paper = np.median(reg.reshape(-1, 3), 0); ink = reg[C > np.percentile(C, 99.7)]
    return tuple(np.clip(ink.mean(0) / paper, .15, .9))


def composite(img, page, inv, fwd, out_path, ink_ratio=(0.56, 0.28, 0.29), seed=0, gamma=1.6, blur=0.9, gain=1.0,
              aa=0.45, sharpen=None, quality=92):
    """gamma: Strich-Ausdünnung (höher = dünner), blur: Kamera-Unschärfe in Foto-px, gain: Deckkraft,
    aa: Vorfilter beim Verkleinern (Anteil der Abtastweite), sharpen=(Stärke, Radius px): Nachschärfen des ganzen Bildes."""
    rng = np.random.default_rng(seed); Hh, Ww = img.shape[:2]; m = MARGIN
    cor = fwd(np.array([[-m, -m], [page.W + m, -m], [page.W + m, page.H + m], [-m, page.H + m]], float))
    x0, y0 = np.maximum(np.floor(cor.min(0)).astype(int), 0)
    x1, y1 = np.minimum(np.ceil(cor.max(0)).astype(int), [Ww, Hh])
    st = 6; c0 = (st - 1) / 2                     # Stützstellen in Pixelmitte -> kein Versatz durch cv2.resize
    gx, gy = np.meshgrid(np.arange(x0, x1 + st, st) + c0, np.arange(y0, y1 + st, st) + c0)
    q = inv(np.c_[gx.ravel(), gy.ravel()].astype(float))
    w, h = x1 - x0, y1 - y0
    mx = cv2.resize(((q[:, 0] + m) * RES).reshape(gx.shape).astype(np.float32), (gx.shape[1] * st, gx.shape[0] * st))[:h, :w]
    my = cv2.resize(((q[:, 1] + m) * RES).reshape(gx.shape).astype(np.float32), (gx.shape[1] * st, gx.shape[0] * st))[:h, :w]
    # Anti-Aliasing: Canvas vor dem Abtasten passend zur Verkleinerung weichzeichnen
    ppm = st / max(float(np.median(np.abs(np.diff(q[:, 0].reshape(gx.shape), axis=1)))), 1e-6)   # Foto-px pro mm
    sig = max(0.0, aa * RES / max(ppm, 1e-6))
    src = cv2.GaussianBlur(page.ink, (0, 0), sig) if sig > 0.3 else page.ink
    a = cv2.remap(src, mx, my, cv2.INTER_LINEAR, borderValue=0)
    a = np.clip(gain * cv2.GaussianBlur(a, (0, 0), blur), 0, 1) ** gamma
    dens = .9 + .2 * cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 2)
    a = np.clip(a * dens, 0, 1)[..., None]
    out = img.copy(); out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - a * (1 - np.array(ink_ratio, np.float32)))
    if sharpen:                                   # leichte Unschärfemaske wie in der Handykamera
        k, r = sharpen
        out = out + k * (out - cv2.GaussianBlur(out, (0, 0), r))
    out = np.clip(out, 0, 255).astype(np.uint8)
    if out_path: cv2.imwrite(out_path, out, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return out
