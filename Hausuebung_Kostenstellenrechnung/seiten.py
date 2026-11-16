"""Layout der beiden Heftseiten (Ü 4.26 + Ü 4.28 | Ü 4.27 + Ü 4.29).
Aufruf: python3 seiten.py preview|final [seite]"""
import sys, pickle, random, math
import numpy as np
import heft

LIB = pickle.load(open('lib.pkl', 'rb'))
UP = '/root/.claude/uploads/a12a72ca-1e1f-5f0a-9d9d-c465b27ff07e/'
NODES = '/tmp/claude-0/-home-user-KOP/a12a72ca-1e1f-5f0a-9d9d-c465b27ff07e/scratchpad/w/nodesc_%s.pkl'
XL, XR = 27.0, 179.0                  # Schreibbereich: rechts vom linken Heftrand bis vor den rechten Rand
S_TXT, S_TAB, S_HEAD = 0.68, 0.66, 0.74
LIFT = 0.55     # Grundlinie über der unteren Karolinie: Ziffern (~3,8 mm) stehen mittig im 5-mm-Kästchen


class Writer:
    """Alle y-Werte = untere Karolinie der Kästchenzeile, in der geschrieben wird."""
    def __init__(self, p, seed):
        self.p, self.r = p, random.Random(seed)

    def ang(self, k=1.0):
        return self.r.uniform(-0.45, 0.45) * k

    def t(self, x, y, s, size=S_TXT, ang=None, jit=0.8):
        a = self.ang() if ang is None else ang
        x = x + self.r.uniform(-jit, jit); yb = y - LIFT + self.r.uniform(-0.2, 0.15)
        x1 = self.p.text(x, yb, s, size, a)
        assert XL - 1.5 <= x and x1 <= XR + 1.5, ('außerhalb', s, round(x, 1), round(x1, 1))
        return x, x1, a

    def rt(self, xr, y, s, size=S_TAB, ang=None, jit=0.6):
        a = self.ang(0.6) if ang is None else ang
        xr = xr + self.r.uniform(-jit, jit); yb = y - LIFT + self.r.uniform(-0.2, 0.15)
        x0 = self.p.rtext(xr, yb, s, size, a)
        assert XL - 1.5 <= x0 and xr <= XR + 1.5, ('außerhalb', s)
        return x0, xr, a

    def tb(self, x, yb, s, size=S_TXT, ang=None, jit=0.5):
        """Text mit direkt vorgegebener Grundlinie (für Brüche)."""
        a = self.ang(0.5) if ang is None else ang
        x = x + self.r.uniform(-jit, jit)
        x1 = self.p.text(x, yb + self.r.uniform(-0.15, 0.15), s, size, a)
        assert XL - 1.5 <= x and x1 <= XR + 1.5, ('außerhalb', s)
        return x, x1, a

    def ct(self, xa, xb, y, s, size=S_TAB):
        w = self.p.width(s, size)
        return self.t((xa + xb) / 2 - w / 2, y, s, size, jit=0.6)

    def hline(self, x1, x2, y, **kw):
        self.p.line(x1 + self.r.uniform(-.5, .5), y + self.r.uniform(-.15, .15), x2 + self.r.uniform(-.6, .6), y + self.r.uniform(-.2, .2), **kw)

    def vline(self, x, y1, y2, **kw):
        self.p.line(x + self.r.uniform(-.3, .3), y1 + self.r.uniform(-.4, .4), x + self.r.uniform(-.5, .5), y2 + self.r.uniform(-.4, .4), **kw)

    def dunder(self, x0, x1, yb):
        """Doppelt unterstreichen unter Text mit Grundlinie yb."""
        self.p.line(x0 - .8, yb + 0.8, x1 + 1.0, yb + 0.8 + self.r.uniform(-.3, .3))
        self.p.line(x0 - .3, yb + 1.9, x1 + 1.5, yb + 1.9 + self.r.uniform(-.3, .3))

    def heading(self, y, s):
        x0, x1, a = self.t(XL + 1, y, s, S_HEAD, ang=self.r.uniform(-0.2, 0.3), jit=0.4)
        tl = math.tan(math.radians(a))
        self.p.line(x0 - 0.5, y + 0.15, x1 + 1.0, y + 0.15 + (x1 - x0) * tl + self.r.uniform(-.25, .25))
        return x1

    def frac_line(self, ybar, label, num, den, res, xlab=XL + 3, size=S_TAB):
        """label: Bruch = Ergebnis. Bruchstrich auf der Karolinie ybar, Zähler im Kästchen darüber,
        Nenner im Kästchen darunter, Bezeichnung/Ergebnis mittig auf Höhe des Bruchstrichs."""
        a = self.ang(0.4)
        ymid = ybar + 1.85                                 # Grundlinie von Bezeichnung und Ergebnis (mittig zum Bruchstrich)
        x0, x1, _ = self.tb(xlab, ymid, label, S_TXT, ang=a) if label else (xlab, xlab - 2.5, a)
        xf0 = x1 + 3
        wn, wd = self.p.width(num, size), self.p.width(den, size); wb = max(wn, wd) + 3
        self.tb(xf0 + (wb - wn) / 2, ybar - LIFT, num, size, ang=a, jit=0.3)
        self.p.line(xf0, ybar - 0.1, xf0 + wb, ybar - 0.1 + self.r.uniform(-.3, .3))
        self.tb(xf0 + (wb - wd) / 2, ybar + 5 - LIFT, den, size, ang=a, jit=0.3)
        xf = xf0 + wb + 1.0
        x2, x3, _ = self.tb(xf + 1.5, ymid, '= ' + res, S_TXT, ang=a, jit=0.3)
        xs = x2 + self.p.width('= ', S_TXT) + 0.8
        self.dunder(xs, x3, ymid)
        return x1, xf, x3

    def bab(self, y_head, spans, heads, rows, sum_before, label_w, size=S_TAB):
        """Handgezeichneter BAB. spans: (xa, xb) der Zahlenspalten; rows: (Label, [Werte...])."""
        self.t(XL + 1, y_head, 'Kostenart', size, jit=0.4)
        for (xa, xb), h in zip(spans, heads):
            self.ct(xa, xb, y_head, h, size * 0.92)
        self.hline(XL - 0.5, XR + 0.5, y_head + 0.1)
        y_end = y_head + 5 * len(rows) + 0.6
        for xa in [XL + label_w] + [s[0] for s in spans[1:]]:
            self.vline(xa, y_head - 5.3, y_end)
        for k, (lab, vals) in enumerate(rows):
            y = y_head + 5 * (k + 1)
            if k == sum_before:
                self.hline(XL - 0.5, XR + 0.5, y - 4.9)
            ls = size * (0.92 if len(lab) > 15 else 1.0)
            self.t(XL + 1, y, lab, ls, jit=0.5)
            last = k == len(rows) - 1
            for (xa, xb), v in zip(spans, vals):
                if not v: continue
                x0, x1, a = self.rt(xb - 2.8, y, v, size)
                if last:
                    self.dunder(x0, x1, y - LIFT)
        return y_end

    def schema(self, y0, lines, x_pct, x_amt, size=0.64):
        """Kalkulationsschema. lines: (op, Label, Prozent, Betrag, Strich_davor, Endergebnis)"""
        ys = {}
        for k, (op, lab, pct, amt, bar, final) in enumerate(lines):
            y = y0 + 5 * k
            a = self.ang(0.7)
            if bar:
                self.hline(x_amt - 20, x_amt + 1.5, y - 4.9)
            if op:
                self.t(XL + 1.2, y, op, S_TXT, ang=a, jit=0.3)
            self.t(XL + 6, y, lab, size, ang=a, jit=0.6)
            if pct:
                self.rt(x_pct, y, pct, size, ang=a, jit=0.5)
            x0, x1, _ = self.rt(x_amt, y, amt, size, ang=a, jit=0.4)
            if final:
                self.dunder(x0, x1, y - LIFT)
            ys[lab] = (y, x1)
        return ys

    def add_column(self, xr, y0, nums, res, size=0.66):
        """Untereinander-Addition, rechtsbündig. Gibt (x0, x1, y) des Ergebnisses zurück."""
        wmax = max(self.p.width(n, size) for n in nums + [res])
        for k, n in enumerate(nums):
            y = y0 + 5 * k
            self.rt(xr, y, n, size, jit=0.3)
            if k > 0:
                self.t(xr - wmax - 5.0, y, '+', size, jit=0.3)
        y = y0 + 5 * len(nums)
        self.hline(xr - wmax - 6.0, xr + 1.2, y - 4.9)
        x0, x1, a = self.rt(xr, y, res, size, jit=0.3)
        return x0, x1, y


# ===================================================================== Seite 1
def seite1(p):
    w = Writer(p, 11)
    w.heading(15, 'Ü 4.26 Betriebsabrechnungsbogen')
    w.t(XL + 1, 25, 'Lohnnebenkosten:')
    w.t(XL + 6, 30, 'Fertigung 1: 28.500 · 85 % = 24.225')
    w.t(XL + 6, 35, 'Fertigung 2: 11.000 · 85 % = 9.350')
    w.t(XL + 1, 40, 'Gehaltsnebenkosten:')
    w.t(XL + 6, 45, 'Material: 6.500 · 45 % = 2.925', ang=0.1)
    w.t(XL + 6, 50, 'Verwaltung: 12.000 · 45 % = 5.400', ang=-0.1)

    lw = 44
    cw = (XR - XL - lw) / 4
    spans = [(XL + lw + i * cw, XL + lw + (i + 1) * cw) for i in range(4)]
    rows = [('Hilfslöhne', ['', '', '11.000', '']),
            ('Lohnnebenkosten', ['', '24.225', '9.350', '']),
            ('Gehälter', ['6.500', '', '', '12.000']),
            ('Gehaltsnebenkosten', ['2.925', '', '', '5.400']),
            ('Energie', ['1.000', '3.500', '3.300', '700']),
            ('Reinigung', ['800', '500', '900', '800']),
            ('diverse Kosten', ['16.000', '63.000', '32.000', '9.000']),
            ('Summe Gemeinkosten', ['27.225', '91.225', '56.550', '27.900']),
            ('Zuschlagsbasis', ['72.000', '28.500', '1.300', '275.500']),
            ('Zuschlagssatz', ['37,81 %', '320,09 %', '43,50 €', '10,13 %'])]
    w.bab(60, spans, ['Material', 'Fertigung 1', 'Fertigung 2', 'Verwaltung'], rows, 7, lw, size=0.64)

    w.t(XL + 1, 120, 'Zuschlagssätze:')
    w.t(141, 120, 'Herstellkosten:', S_TAB * 0.95, jit=0.3)
    hx0, hx1, hy = w.add_column(176, 125, ['72.000', '27.225', '28.500', '91.225', '56.550'], '275.500')
    w.frac_line(130, 'Material:', '27.225 · 100', '72.000', '37,81 %')
    w.frac_line(145, 'Fertigung 1:', '91.225 · 100', '28.500', '320,09 %')
    w.t(XL + 3, 155, 'Maschinenstundensatz Fertigung 2:')
    _, _, x3 = w.frac_line(165, '', '56.550', '1.300', '43,50 €', xlab=XL + 9)
    w.tb(x3 + 5, 166.85, 'je Maschinenstunde', jit=0.3)
    xl, xf, xe = w.frac_line(180, 'Verwaltung:', '27.900 · 100', '275.500', '10,13 %')
    p.arrow((hx0 + 6, hy + 0.6), (xf - 1.0, 183.4), via=[(hx1 + 1, hy + 8), (hx0 + 4, 183.5), (xf + 12, 187.8)])

    w.hline(XL - 1, XR + 1, 190.1)
    w.heading(200, 'Ü 4.28 Zuschlagskalkulation')
    _, xe, _ = w.t(XL + 1, 210, 'Fertigungslöhne je Stück: 13,30 · 195 : 60 = 43,225')
    lines = [('', 'Materialeinzelkosten', '', '25,00', False, False),
             ('+', 'Materialgemeinkosten', '38 %', '9,50', False, False),
             ('=', 'Materialkosten', '', '34,50', True, False),
             ('', 'Fertigungslöhne', '', '43,23', False, False),
             ('+', 'Fertigungsgemeinkosten', '320 %', '138,32', False, False),
             ('=', 'Fertigungskosten', '', '181,55', True, False),
             ('=', 'Herstellkosten', '', '216,05', False, False),
             ('+', 'Verwaltungsgemeinkosten', '7 %', '15,12', False, False),
             ('+', 'Vertriebsgemeinkosten', '5 %', '10,80', False, False),
             ('=', 'Selbstkosten', '', '241,97', True, True)]
    ys = w.schema(220, lines, 104, 138)
    yf, xa = ys['Fertigungslöhne']
    p.arrow((xe - 3, 210.8), (xa + 1.5, yf - LIFT - 1.7), via=[(xe + 0.5, 216.5), (xa + 12, yf - 3.6)])
    return p


# ===================================================================== Seite 2
def seite2(p):
    w = Writer(p, 23)
    w.heading(15, 'Ü 4.27 Betriebsabrechnungsbogen')
    w.t(XL + 1, 25, 'Lohnnebenkosten Fertigung: 790.000 · 87 % = 687.300')
    w.t(XL + 1, 30, 'Gehaltsnebenkosten:')
    w.t(XL + 6, 35, 'Material: 95.300 · 55 % = 52.415')
    w.t(XL + 6, 40, 'Fertigung: 157.800 · 55 % = 86.790')
    w.t(XL + 6, 45, 'Verwaltung: 265.500 · 55 % = 146.025')

    lw = 44
    cw = (XR - XL - lw) / 3
    spans = [(XL + lw + i * cw, XL + lw + (i + 1) * cw) for i in range(3)]
    rows = [('Lohnnebenkosten', ['', '687.300', '']),
            ('Gehälter', ['95.300', '157.800', '265.500']),
            ('Gehaltsnebenkosten', ['52.415', '86.790', '146.025']),
            ('Energiekosten', ['120.500', '190.000', '75.600']),
            ('Raumkosten', ['76.100', '200.500', '55.400']),
            ('Abschreibungen', ['35.000', '480.700', '115.500']),
            ('sonstige Kosten', ['85.100', '260.000', '115.000']),
            ('Summe Gemeinkosten', ['464.415', '2.063.090', '773.025']),
            ('Zuschlagsbasis', ['980.000', '790.000', '4.297.505']),
            ('Zuschlagssatz', ['47,39 %', '261,15 %', '17,99 %'])]
    w.bab(55, spans, ['Material', 'Fertigung', 'Verwaltung'], rows, 7, lw)

    w.t(XL + 1, 115, 'Zuschlagssätze:')
    w.t(141, 115, 'Herstellkosten:', S_TAB * 0.95, jit=0.3)
    hx0, hx1, hy = w.add_column(176, 120, ['980.000', '464.415', '790.000', '2.063.090'], '4.297.505')
    w.frac_line(125, 'Material:', '464.415 · 100', '980.000', '47,39 %')
    w.frac_line(140, 'Fertigung:', '2.063.090 · 100', '790.000', '261,15 %')
    xl, xf, xe = w.frac_line(155, 'Verwaltung:', '773.025 · 100', '4.297.505', '17,99 %')
    p.arrow((hx0 + 2, hy + 0.6), (xf - 1.0, 158.4), via=[(hx0 - 2, hy + 11), (xf + 14, 162.6)])

    w.hline(XL - 1, XR + 1, 165.1)
    w.heading(175, 'Ü 4.29 Zuschlagskalkulation')
    lines = [('', 'Materialeinzelkosten', '', '31,00', False, False),
             ('+', 'Materialgemeinkosten', '25 %', '7,75', False, False),
             ('=', 'Materialkosten', '', '38,75', True, False),
             ('', 'Fertigungslöhne 1', '', '23,83', False, False),
             ('+', 'Fertigungsgemeinkosten 1', '340 %', '81,03', False, False),
             ('', 'Fertigungslöhne 2', '', '14,25', False, False),
             ('+', 'Fertigungsgemeinkosten 2', '424 %', '60,42', False, False),
             ('=', 'Herstellkosten', '', '218,29', True, False),
             ('+', 'Verwaltungsgemeinkosten', '6 %', '13,10', False, False),
             ('+', 'Vertriebsgemeinkosten', '7 %', '15,28', False, False),
             ('=', 'Selbstkosten', '', '246,66', True, False),
             ('+', 'Gewinnaufschlag', '20 %', '49,33', False, False),
             ('=', 'Nettoverkaufspreis', '', '296,00', True, False),
             ('+', 'Umsatzsteuer', '20 %', '59,20', False, False),
             ('=', 'Bruttoverkaufspreis', '', '355,20', True, True)]
    ys = w.schema(185, lines, 106, 139)
    # Nebenrechnungen rechts neben dem Schema, Ergebnis auf Höhe der Zeile, kurzer Pfeil hinein
    for lab, nr, res in (('Fertigungslöhne 1', '13,00·110:60', '23,83'), ('Fertigungslöhne 2', '11,40·75:60', '14,25')):
        y, xa = ys[lab]
        w.t(145, y - 5, nr, 0.6, jit=0.4)
        x0, x1, _ = w.t(150, y, '= ' + res, 0.6, jit=0.4)
        p.arrow((x0 - 1.0, y - LIFT - 1.5), (xa + 1.3, y - LIFT - 1.6), bend=0.25)
    return p


PAGES = {1: ('bec61ce8', seite1, 101), 2: ('bd38cdaa', seite2, 202)}

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'preview'
    which = [int(a) for a in sys.argv[2:]] or [1, 2]
    for n in which:
        photo, fn, seed = PAGES[n]
        nodes = pickle.load(open(NODES % photo, 'rb'))['nodes']
        inv, fwd, Wm, Hm = heft.grid_mapping(nodes)
        p = heft.Page(LIB['lib'], LIB['pxmm'], Wm, Hm, seed=seed)
        fn(p)
        pickle.dump(p.ink, open('/tmp/claude-0/-home-user-KOP/a12a72ca-1e1f-5f0a-9d9d-c465b27ff07e/scratchpad/w/ink_%d.pkl' % n, 'wb'))
        if mode == 'preview':
            p.preview('/tmp/claude-0/-home-user-KOP/a12a72ca-1e1f-5f0a-9d9d-c465b27ff07e/scratchpad/w/flat_%d.png' % n, 0.25)
        else:
            img = heft.load(UP + photo + '-image.jpg')
            heft.composite(img, p, inv, fwd, 'Seite_%d.jpg' % n, ink_ratio=(0.52, 0.31, 0.32), gamma=1.0, blur=0.4, aa=0.3,
                           sharpen=(0.25, 1.0), quality=92, seed=n)
        print('Seite', n, 'fertig')
