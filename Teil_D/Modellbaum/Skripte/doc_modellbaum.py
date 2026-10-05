"""Erzeugt Modellbaum_Einzelteile.pdf (A4 quer, 1 Seite je Teil) und README.md aus mb_daten.py."""
import pickle, textwrap, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
from PIL import Image
from mb_daten import ALLGEMEIN, PARTS, NORMTEILE, FREISTICH

VOL = pickle.load(open("mb/vol.pkl", "rb"))
W, H = 297/25.4, 210/25.4
F = dict(family="DejaVu Sans")
PT = 0.3528  # mm je pt

def vol_txt(v): return f"{round(v):,}".replace(",", ".") + " mm³"

def wrap(s, n): return textwrap.wrap(s, n) or [""]

def txt(ax, x, y, s, size=9, **kw):
    ax.text(x, y, s, fontsize=size, va="top", **F, **kw)

def crop(path, pad=12):
    from PIL import ImageOps
    im = Image.open(path).convert("RGB")
    bb = ImageOps.invert(im).getbbox()
    if bb: im = im.crop((max(0, bb[0]-pad), max(0, bb[1]-pad), min(im.width, bb[2]+pad), min(im.height, bb[3]+pad)))
    return im

def img(fig, path, x, y, w, h, anchor="C"):
    a = fig.add_axes([x/297, y/210, w/297, h/210]); a.imshow(crop(path)); a.axis("off"); a.set_anchor(anchor)

def table(ax, x0, ytop, cols, rows, size=7.6, head=("Nr", "Creo-KE", "Ebene / Referenz", "Eingaben / Maße")):
    """cols: Spaltenbreiten in mm. Zeichnet Tabelle, gibt untere y-Kante zurueck."""
    cw = [max(3, int(w / (size*PT*0.56))) for w in cols]
    lh = size*PT*1.25
    def row(cells, y, bold=False, fill=None):
        lines = [wrap(c, n) for c, n in zip(cells, cw)]
        h = max(len(l) for l in lines)*lh + 2.0
        if fill: ax.add_patch(Rectangle((x0, y-h), sum(cols), h, fc=fill, ec="none"))
        x = x0
        for l, w in zip(lines, cols):
            txt(ax, x+1.2, y-1.0, "\n".join(l), size, weight="bold" if bold else "normal", linespacing=1.25)
            x += w
        ax.plot([x0, x0+sum(cols)], [y-h, y-h], color="0.6", lw=0.4)
        return y-h
    ax.plot([x0, x0+sum(cols)], [ytop, ytop], color="0.3", lw=0.8)
    y = row(head, ytop, True, "#dde6f0")
    for k, r in enumerate(rows):
        y = row(r, y, fill="#f6f8fa" if k % 2 else None)
    ax.plot([x0, x0+sum(cols)], [y, y], color="0.3", lw=0.8)
    return y

def header(ax, title, sub):
    ax.add_patch(Rectangle((0, 192), 297, 18, fc="#1f4e79", ec="none"))
    txt(ax, 12, 206, title, 16, color="white", weight="bold")
    txt(ax, 12, 197.5, sub, 9, color="white")

with PdfPages("Modellbaum_Einzelteile.pdf") as pdf:
    # ---------- Seite 1: Allgemein + Uebersicht ----------
    fig = plt.figure(figsize=(W, H)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 297); ax.set_ylim(0, 210); ax.axis("off")
    header(ax, "Fliehkraftkupplung – Modellbaum der Einzelteile (Creo Parametric 12)",
           "So baust du jedes Teil KE für KE auf: Reihenfolge, Skizzierebene, Skizze mit Maßen, Sollvolumen zur Kontrolle")
    txt(ax, 12, 186, "Grundregeln", 11, weight="bold")
    y = 180
    for s in ALLGEMEIN:
        ls = wrap(s, 150)
        txt(ax, 14, y, "•", 8.5); txt(ax, 18, y, "\n".join(ls), 8.5, linespacing=1.3)
        y -= len(ls)*3.9 + 1.6
    y -= 3
    txt(ax, 12, y, "Übersicht", 11, weight="bold"); y -= 6
    rows = [(p["nr"], p["name"], p["werkstoff"], str(len(p["ke"])), vol_txt(VOL[p["key"]]), p["quelle"]) for p in PARTS]
    rows += [(n, t, "Normteil", "–", "–", "nicht modellieren, siehe letzte Seite") for n, t, _ in NORMTEILE]
    table(ax, 12, y, [12, 62, 52, 14, 30, 103], rows, 7.6, head=("Pos.", "Teil", "Werkstoff", "KE", "Sollvolumen", "Grundlage"))
    pdf.savefig(fig); plt.close(fig)


    # ---------- Seite 2: Freistich DIN 509 ----------
    FS = FREISTICH
    fig = plt.figure(figsize=(W, H)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 297); ax.set_ylim(0, 210); ax.axis("off")
    header(ax, FS["titel"], "Laut Zeichnung: „Nicht bemaßte Freistiche DIN 509-E0,6×0,3“ – so baust du sie in Creo ein")
    txt(ax, 10, 187, "Normmaße", 10, weight="bold")
    yb = table(ax, 10, 182, [52, 56], FS["norm"], 8, head=("Größe", "Wert"))
    ls = wrap(FS["quelle"], 72); txt(ax, 10, yb - 2, "\n".join(ls), 7, style="italic", linespacing=1.25)
    y = yb - 4 - len(ls)*3.3
    txt(ax, 10, y, "Wo sitzen die Freistiche?", 10, weight="bold")
    y = table(ax, 10, y - 5, [9, 42, 82, 30], FS["wo"], 7.6, head=("Bild", "Teil", "Stelle", "Maß")) - 5
    txt(ax, 10, y, "So geht es in Creo (in der Drehskizze von KE 1)", 10, weight="bold"); y -= 5.5
    for i, st in enumerate(FS["schritte"], 1):
        ls = wrap(st, 100)
        txt(ax, 11, y, f"{i}.", 8); txt(ax, 16, y, "\n".join(ls), 8, linespacing=1.25)
        y -= len(ls)*3.5 + 1.3
    xr, wr = 186, 104; hb = (188 - 8)/3
    for j, (f, cap) in enumerate(FS["bilder"]):
        yy = 188 - j*hb
        txt(ax, xr, yy, cap, 7.8, weight="bold")
        img(fig, "mb/" + f, xr, yy - hb + 2, wr, hb - 7)
    txt(ax, 287, 4, "Seite 2", 7, ha="right", color="0.4")
    pdf.savefig(fig); plt.close(fig)

    # ---------- je Teil eine Seite ----------
    for p in PARTS:
        fig = plt.figure(figsize=(W, H)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 297); ax.set_ylim(0, 210); ax.axis("off")
        header(ax, f"Pos. {p['nr']} – {p['name']}",
               f"Werkstoff: {p['werkstoff']}   |   Vorlage: mmns_part_solid_abs   |   Grundlage: {p['quelle']}")
        yb = table(ax, 10, 188, [9, 36, 44, 85], p["ke"])
        # Volumen + Hinweise
        y = yb - 5
        ax.add_patch(Rectangle((10, y-8), 174, 8, fc="#e8f3e8", ec="#4a8a4a", lw=0.6))
        txt(ax, 13, y-1.6, f"Kontrolle: Analyse → Masseneigenschaften → Volumen = {vol_txt(VOL[p['key']])}", 9, weight="bold")
        y -= 13
        if p["hinweise"]:
            txt(ax, 10, y, "Hinweise", 9, weight="bold"); y -= 5
            for h in p["hinweise"]:
                ls = wrap(h, 118)
                txt(ax, 12, y, "•", 7.8); txt(ax, 15, y, "\n".join(ls), 7.8, linespacing=1.25)
                y -= len(ls)*3.5 + 1.2
        # rechte Spalte: Skizzen ueber die volle Hoehe, 3D-Bild links unten (wenn Platz)
        xr, wr = 190, 100
        sk = p["skizzen"]
        left_free = y - 10
        put3d_left = left_free >= 38
        top, bot = 188, (8 if put3d_left else 62)
        if len(sk) >= 3:   # erste Skizze (Drehprofil) oben, die anderen nebeneinander darunter
            h1 = (top - bot)*0.40
            txt(ax, xr, top, sk[0][1], 7.8, weight="bold"); img(fig, "mb/" + sk[0][0], xr, top - h1 + 2, wr, h1 - 6)
            n = len(sk) - 1; cw = wr/n
            for j, (f, cap) in enumerate(sk[1:]):
                xx = xr + j*cw
                txt(ax, xx, top - h1, "\n".join(textwrap.wrap(cap.replace(" – ", " – "), int(cw/1.55))), 6.8, weight="bold")
                img(fig, "mb/" + f, xx, bot, cw - 2, top - h1 - bot - 11)
        else:
            hs = (top - bot)/len(sk)
            yy = top
            for f, cap in sk:
                txt(ax, xr, yy, cap, 7.8, weight="bold")
                img(fig, "mb/" + f, xr, yy - hs + 2, wr, hs - 6)
                yy -= hs
        if put3d_left:
            h3 = min(left_free - 6, 70)
            txt(ax, 10, y - 1, "Fertiges Teil", 7.8, weight="bold")
            img(fig, f"mb/{p['key']}_3d.png", 10, y - 6 - h3, 174, h3)
        else:
            txt(ax, xr, 60, "Fertiges Teil", 7.8, weight="bold")
            img(fig, f"mb/{p['key']}_3d.png", xr, 6, wr, 50)
        txt(ax, 287, 4, f"Seite {PARTS.index(p)+3}", 7, ha="right", color="0.4")
        pdf.savefig(fig); plt.close(fig)

    # ---------- Normteile ----------
    fig = plt.figure(figsize=(W, H)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 297); ax.set_ylim(0, 210); ax.axis("off")
    header(ax, "Normteile Pos. 8, 10, 11 – nicht selbst modellieren", "Normteile werden zugekauft. In Creo baut man sie aus einer Bibliothek oder als Herstellermodell ein.")
    table(ax, 12, 186, [14, 70, 189], NORMTEILE, 8.5, head=("Pos.", "Teil", "So kommt es in Creo"))
    pdf.savefig(fig); plt.close(fig)

# ---------- README ----------
def md_esc(s): return s.replace("|", "\\|")
L = ["# Modellbaum der Einzelteile – Creo Parametric 12", "",
     "Für jedes Teil steht hier, wie man es in Creo **KE für KE** aufbaut: Reihenfolge, Skizzierebene, Skizze mit Maßen und das Sollvolumen zur Kontrolle.",
     "Die gleiche Anleitung gibt es als PDF: `Modellbaum_Einzelteile.pdf` (eine Seite pro Teil).", "",
     "Ich habe jede Anleitung mit einem Skript Schritt für Schritt nachgebaut (`Skripte/replay.py`). Die Sollvolumen stammen aus diesem Nachbau.", "",
     "## Grundregeln", ""] + [f"- {s}" for s in ALLGEMEIN] + ["", f"## {FREISTICH['titel']}", "",
     "| Größe | Wert |", "|---|---|"] + [f"| {a} | {b} |" for a, b in FREISTICH["norm"]] + ["", f"*{FREISTICH['quelle']}*", "",
     "| Bild | Teil | Stelle | Maß |", "|---|---|---|---|"] + [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in FREISTICH["wo"]] + ["",
     "**So geht es in Creo:**", ""] + [f"{i}. {t}" for i, t in enumerate(FREISTICH["schritte"], 1)] + [""] + \
     sum([[f"*{c}*", "", f"![{c}](Bilder/{f})", ""] for f, c in FREISTICH["bilder"]], []) + ["## Übersicht", "",
     "| Pos. | Teil | Werkstoff | KE | Sollvolumen |", "|---|---|---|---|---|"]
for p in PARTS:
    L.append(f"| {p['nr']} | [{p['name']}](#pos-{p['nr'].replace('.', '')}) | {p['werkstoff']} | {len(p['ke'])} | {vol_txt(VOL[p['key']])} |")
for n, t, _ in NORMTEILE:
    L.append(f"| {n} | {t} | Normteil | – | – |")
for p in PARTS:
    L += ["", f'<a id="pos-{p["nr"].replace(".", "")}"></a>', f"## Pos. {p['nr']} – {p['name']}", "",
          f"Werkstoff: **{p['werkstoff']}** · Vorlage: `mmns_part_solid_abs` · Grundlage: {p['quelle']}", "",
          "| Nr | Creo-KE | Ebene / Referenz | Eingaben / Maße |", "|---|---|---|---|"]
    L += [f"| {' | '.join(md_esc(c) for c in r)} |" for r in p["ke"]]
    L += ["", f"**Kontrolle:** Analyse → Masseneigenschaften → Volumen = **{vol_txt(VOL[p['key']])}**", ""]
    for f, cap in p["skizzen"]:
        L += [f"*{cap}*", "", f"![{cap}](Bilder/{f})", ""]
    L += [f"![Pos. {p['nr']} fertig](Bilder/{p['key']}_3d.png)", ""]
    if p["hinweise"]:
        L += ["**Hinweise**", ""] + [f"- {h}" for h in p["hinweise"]]
L += ["", "## Normteile (nicht selbst modellieren)", "", "| Pos. | Teil | So kommt es in Creo |", "|---|---|---|"]
L += [f"| {n} | {t} | {md_esc(s)} |" for n, t, s in NORMTEILE]
open("README_modellbaum.md", "w").write("\n".join(L) + "\n")
print("ok")
