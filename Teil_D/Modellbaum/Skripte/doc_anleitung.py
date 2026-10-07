"""Erzeugt Anleitung_Schritt_fuer_Schritt.pdf (A4 hoch, fliessender Text) und Schritt_fuer_Schritt.md aus anleitung_daten.py."""
import textwrap, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
from PIL import Image, ImageOps
from anleitung_daten import ALLGEMEIN, FREISTICH, TEILE

W, H = 210/25.4, 297/25.4
X0, X1, YTOP, YBOT = 15, 195, 282, 14
FONT = dict(family="DejaVu Sans")
PT = 0.3528

def vt(x): return f"{x:,}".replace(",", ".") + " mm³"

def crop(path, pad=10):
    im = Image.open(path).convert("RGB"); bb = ImageOps.invert(im).getbbox()
    return im.crop((max(0, bb[0]-pad), max(0, bb[1]-pad), min(im.width, bb[2]+pad), min(im.height, bb[3]+pad))) if bb else im

class Flow:
    def __init__(self, pdf): self.pdf = pdf; self.fig = None; self.n = 0; self.kopf = ""
    def neue_seite(self, kopf=None):
        if self.fig: self._fuss(); self.pdf.savefig(self.fig); plt.close(self.fig)
        if kopf is not None: self.kopf = kopf
        self.fig = plt.figure(figsize=(W, H)); self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, 210); self.ax.set_ylim(0, 297); self.ax.axis("off"); self.n += 1; self.y = YTOP
        if self.kopf:
            self.ax.text(X0, 291, self.kopf, fontsize=7.5, color="0.45", va="top", **FONT)
            self.ax.plot([X0, X1], [287.5, 287.5], color="0.75", lw=0.5)
    def _fuss(self):
        self.ax.text(X1, 7, f"Seite {self.n}", fontsize=7, color="0.45", ha="right", **FONT)
    def platz(self, h):
        if self.y - h < YBOT: self.neue_seite()
    def text(self, s, size=9, x=X0, breite=None, bold=False, farbe="k", abstand=1.6, style="normal"):
        breite = breite or (X1 - x)
        n = max(10, int(breite / (size*PT*0.55)))
        zeilen = textwrap.wrap(s, n) or [""]
        lh = size*PT*1.32
        for z in zeilen:
            self.platz(lh)
            self.ax.text(x, self.y, z, fontsize=size, va="top", weight="bold" if bold else "normal", color=farbe, style=style, **FONT)
            self.y -= lh
        self.y -= abstand
    def zeile(self, s):
        if s.startswith("- "): self._mark("•", s[2:])
        elif s.startswith("! "): self._mark("⚠", s[2:], farbe="#b03000", bold=True)
        elif s.startswith("> "): self._mark("➜", s[2:], farbe="#1f4e79")
        else: self._mark("·", s)
    def _mark(self, m, s, farbe="k", bold=False):
        self.platz(5)
        self.ax.text(X0 + 3, self.y, m, fontsize=9, va="top", color=farbe, **FONT)
        self.text(s, 9, x=X0 + 8, farbe=farbe, bold=bold, abstand=1.0)
    def titel(self, s, sub=None):
        self.platz(22)
        self.ax.add_patch(Rectangle((0, self.y - 15), 210, 17, fc="#1f4e79", ec="none"))
        self.ax.text(X0, self.y - 1.5, s, fontsize=16, color="white", weight="bold", va="top", **FONT)
        if sub: self.ax.text(X0, self.y - 9.5, sub, fontsize=8.5, color="white", va="top", **FONT)
        self.y -= 21
    def ueberschrift(self, s, size=11, farbe="#1f4e79"):
        self.platz(14); self.y -= 2
        self.text(s, size, bold=True, farbe=farbe, abstand=1.2)
    def bild(self, path, h, w=None):
        im = crop(path); w = w or (X1 - X0)
        r = im.width / im.height
        hh = min(h, w / r); ww = hh * r
        self.platz(hh + 2)
        a = self.fig.add_axes([X0/210, (self.y - hh)/297, ww/210, hh/297]); a.imshow(im); a.axis("off")
        self.y -= hh + 3
    def volumen(self, v):
        self.platz(8)
        self.ax.add_patch(Rectangle((X0 + 6, self.y - 6), 95, 6.2, fc="#e8f3e8", ec="#4a8a4a", lw=0.5))
        self.ax.text(X0 + 8, self.y - 1.1, f"✔ Volumen nach diesem KE: {vt(v)}", fontsize=8.8, weight="bold", va="top", **FONT)
        self.y -= 9
    def tabelle(self, kopf, rows, cols, size=8):
        lh = size*PT*1.35 + 1.6
        self.platz(lh*(len(rows) + 1) + 2)
        x = X0; yy = self.y
        self.ax.add_patch(Rectangle((X0, yy - lh), sum(cols), lh, fc="#dde6f0", ec="none"))
        for c, w in zip(kopf, cols):
            self.ax.text(x + 1.2, yy - 0.8, c, fontsize=size, weight="bold", va="top", **FONT); x += w
        yy -= lh
        for k, r in enumerate(rows):
            if k % 2: self.ax.add_patch(Rectangle((X0, yy - lh), sum(cols), lh, fc="#f6f8fa", ec="none"))
            x = X0
            for c, w in zip(r, cols):
                self.ax.text(x + 1.2, yy - 0.8, c, fontsize=size, va="top", **FONT); x += w
            yy -= lh
        self.ax.plot([X0, X0 + sum(cols)], [yy, yy], color="0.4", lw=0.6)
        self.y = yy - 3
    def ende(self):
        self._fuss(); self.pdf.savefig(self.fig); plt.close(self.fig)

with PdfPages("Anleitung_Schritt_fuer_Schritt.pdf") as pdf:
    f = Flow(pdf); f.neue_seite("")
    f.titel("Fliehkraftkupplung – Schritt für Schritt in Creo 12",
            "Jedes Teil KE für KE, mit Klickfolgen und Zwischenvolumen zur Kontrolle")
    f.text("Diese Anleitung ergänzt die Kurzfassung „Modellbaum_Einzelteile.pdf“. Sie nutzt die deutschen Namen aus Creo: "
           "Ebenen VORNE / OBEN / RECHTS, Achse A_X, Bedingung „Zusammenfallend“. x-Maße zählen ab der Ebene RECHTS. "
           "Nach jedem KE steht das Volumen, das du dann haben musst. Stimmt es, ist der Schritt richtig.", 9.2)
    for kopf, zeilen in ALLGEMEIN:
        f.ueberschrift(kopf)
        for z in zeilen: f.zeile(z)
    f.ueberschrift("Freistich DIN 509 – E 0,6 × 0,3 (Pos. 1, 2, 4) – in der Drehskizze")
    for z in FREISTICH: f.zeile(z)
    f.bild("mb/fr_welle.png", 30, 80)
    f.text("Einstichgrund: Pos. 1 Ø44,4 (F1) · Ø136-Bund Ø135,4 (F2) · Lagersitz-Bohrung Ø75 → Ø75,6 (F3). Details: Seite 2 der Kurzfassung.", 8.3, style="italic")
    for t in TEILE:
        f.neue_seite(t["titel"])
        f.titel(t["titel"], f"Dateiname: {t['datei']}   |   Werkstoff: {t['werkstoff']}   |   Vorlage: mmns_part_solid_abs")
        if t["bild"]: f.bild("mb/" + t["bild"], 50)
        if t["kontur"]:
            f.ueberschrift("Kontur für die Drehskizze (Punkt für Punkt, x ab RECHTS)", 10)
            f.tabelle(("Punkt", "x", "Ø", "Hinweis"), t["kontur"], [14, 18, 22, 126])
        for kt, zeilen, bild, vol in t["schritte"]:
            f.ueberschrift(kt, 10.5)
            for z in zeilen: f.zeile(z)
            if bild: f.bild("mb/" + bild, 32, 95)
            if vol: f.volumen(vol)
        letzte = [s[3] for s in t["schritte"] if s[3]][-1]
        f.platz(10); f.y -= 1
        f.text(f"Fertig. Endvolumen {vt(letzte)}. Alle KE im Modellbaum umbenennen und speichern.", 9.5, bold=True, farbe="#2d6a2d")
    f.ende()

# ---------------- Markdown ----------------
L = ["# Fliehkraftkupplung – Schritt für Schritt in Creo 12", "",
     "Ausführliche Fassung zur Kurzanleitung `Modellbaum_Einzelteile.pdf`. Nach jedem KE steht das Volumen, das du haben musst.", ""]
for kopf, zeilen in ALLGEMEIN:
    L += [f"## {kopf}", ""] + [("- " + z.lstrip("-!> ").strip()) for z in zeilen] + [""]
L += ["## Freistich DIN 509 – E 0,6 × 0,3 (in der Drehskizze)", ""] + [f"{i}. {z}" for i, z in enumerate(FREISTICH, 1)] + ["", "![Freistich](Bilder/fr_welle.png)", ""]
for t in TEILE:
    L += [f"## {t['titel']}", "", f"Dateiname `{t['datei']}` · Werkstoff {t['werkstoff']} · Vorlage `mmns_part_solid_abs`", ""]
    if t["bild"]: L += [f"![{t['titel']}](Bilder/{t['bild']})", ""]
    if t["kontur"]:
        L += ["| Punkt | x | Ø | Hinweis |", "|---|---|---|---|"] + [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in t["kontur"]] + [""]
    for kt, zeilen, bild, vol in t["schritte"]:
        L += [f"### {kt}", ""]
        for z in zeilen:
            pre = "⚠ " if z.startswith("! ") else ("➜ " if z.startswith("> ") else "")
            L.append("- " + pre + z.lstrip("-!> ").strip())
        if bild: L += ["", f"![{kt}](Bilder/{bild})"]
        if vol: L += ["", f"✅ **Volumen nach diesem KE: {vt(vol)}**"]
        L.append("")
open("Schritt_fuer_Schritt.md", "w").write("\n".join(L) + "\n")
print("ok")
