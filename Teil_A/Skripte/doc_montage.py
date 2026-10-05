import textwrap, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image

W, H = 297/25.4, 210/25.4
F = dict(family="DejaVu Sans")

def page(pdf, draw):
    fig = plt.figure(figsize=(W, H)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 297); ax.set_ylim(0, 210); ax.axis("off")
    draw(fig, ax); pdf.savefig(fig); plt.close(fig)

def txt(ax, x, y, s, size=10, width=None, **kw):
    if width: s = "\n".join(textwrap.fill(p, width) if p else "" for p in s.split("\n"))
    ax.text(x, y, s, fontsize=size, va="top", **F, **kw)

def img(fig, path, x, y, w, h):
    a = fig.add_axes([x/297, y/210, w/297, h/210]); a.imshow(Image.open(path)); a.axis("off"); a.set_anchor("C")

STEPS = [
 ("Antriebsnabe (1) bereitlegen",
  "Die Antriebsnabe ist das Basisteil der Unterbaugruppe „Nabe“. Alle beweglichen Teile hängen an ihren zwei Armen.",
  "Creo: Komponente einbauen → Abhängigkeit „Standard“ (fixiert).",
  "Arme mit den Bohrungen Ø8H8 zeigen nach oben und unten (Abstand 104 mm)."),
 ("Scheiben (6) an die Arme legen",
  "Je Arm links und rechts eine Scheibe 16 × 9 × 1,5 → 4 Stück.",
  "Creo: Achse Scheibe koinzident Achse Armbohrung, Planfläche Scheibe koinzident Seitenfläche Arm.",
  "Warum? Die Nut im Fliehgewicht ist 20 mm breit, der Arm nur 17 mm: 17 + 2 × 1,5 = 20. Die Scheiben füllen das Spiel und sind Anlaufflächen."),
 ("Fliehgewichte (5) über die Arme schieben",
  "Fliehgewicht = Gewicht 5.1 mit aufgeklebtem Reibbelag 5.2 (vorher zusammengebaut). Gewicht 1 am oberen Arm, Gewicht 2 am unteren Arm (punktsymmetrisch).",
  "Creo: Bohrung Ø8H9 koaxial Armbohrung, Nutfläche koinzident Außenfläche Scheibe, Winkelversatz 68,1° (RIGHT Gewicht ↔ FRONT Nabe).",
  "In Ruhelage hat der Belag ca. 2,7 mm Luft zum späteren Gehäuse."),
 ("Zylinderstifte (9) einstecken",
  "4 Stifte: 2 als Drehpunkt (durch Arm, Scheiben und Gewicht), 2 in den freien Enden der Gewichte (dort werden die Federn eingehängt).",
  "Creo: Achse Stift koaxial Bohrung, Stift mittig: Stiftmitte = Mitte Gewicht (25 mm nach jeder Seite).",
  "Stift Ø8h8 in Bohrung Ø8H8/H9 → Spielpassung, das Gewicht kann schwenken."),
 ("Sicherungsscheiben (8) aufschieben",
  "8 Stück DIN 6799 – 7 in die Nuten Ø7 der Stifte (7 mm vom Stiftende).",
  "Creo: Achse koaxial Stift, Planfläche an Nutflanke bzw. an Gewichtsauge.",
  "Sie verhindern, dass die Stifte axial herauswandern."),
 ("Zugfedern (7) einhängen",
  "4 Federn: je eine vorne und hinten. Feder 1 verbindet den oberen Drehpunkt mit dem freien Ende von Gewicht 2, Feder 2 den unteren Drehpunkt mit dem freien Ende von Gewicht 1.",
  "Creo: Öse koaxial Stiftachse, Ösenebene in den Einstich R0,6 (3 mm vom Stiftende).",
  "Die Federn sind gespannt eingebaut (Ösenabstand 38,8 mm statt 22,9 mm frei) und ziehen die Gewichte nach innen. Erst wenn die Fliehkraft größer ist, legen sich die Beläge an."),
 ("Rillenkugellager (11) aufpressen",
  "2 Lager 6009-2Z auf die Lagersitze Ø45k6 bis zur Wellenschulter.",
  "Creo: Bohrung Lager koaxial Lagersitz, Stirnfläche Innenring koinzident Wellenschulter.",
  "Ø45k6 ist eine Übergangspassung → Lager aufpressen. Die Kraft nur über den Innenring einleiten, sonst werden Kugeln und Laufbahn beschädigt. Damit ist die Unterbaugruppe „Nabe“ fertig."),
 ("Gehäuse (3) mit Abtriebsnabe (2) verschrauben",
  "Zweite Unterbaugruppe: das Gehäuse wird über die Zentrierung Ø136 H7/h6 auf die Abtriebsnabe gesteckt und mit 6 Zylinderschrauben ISO 4762 M8 × 20 (10) verschraubt.",
  "Creo: Achse koaxial, Planfläche Gehäuse koinzident Flansch Abtriebsnabe, Achse Gewindebohrung koaxial Durchgangsbohrung.",
  "Schrauben über Kreuz anziehen. Die Köpfe liegen versenkt in den Senkungen Ø15H13."),
 ("Nabe einschieben",
  "Die vormontierte Nabe wird mit dem rechten Lager in den Lagersitz Ø75H7 der Abtriebsnabe geschoben, bis der Außenring an der Schulter anliegt.",
  "Creo: Außenring koaxial Lagersitz, Stirnfläche Außenring koinzident Schulter.",
  "Viertelschnitt: so sieht man das Innenleben im Gehäuse."),
 ("Filzring (12) in den Deckel (4)",
  "Der Filzring DIN 5419 wird in die trapezförmige Nut Ø58H12 / 4H13 / 14° des Deckels eingelegt.",
  "Creo: Achse koaxial, Ring in der Nut zentriert.",
  "Vor dem Einbau in Öl tränken. Der Filzring dichtet nach außen gegen Staub ab, er dichtet nicht das Lager."),
 ("Deckel aufsetzen und verschrauben",
  "Der Deckel geht gleichzeitig über das linke Lager (Ø75H7) und mit der Zentrierung Ø136h6 ins Gehäuse. Danach 6 Schrauben M8 × 20 anziehen.",
  "Creo: Achse koaxial, Flanschfläche Deckel koinzident Stirnfläche Gehäuse, Bohrungen fluchtend mit den Gewinden.",
  "Der Filzring gleitet dabei über den Lagersitz der Antriebsnabe."),
 ("Fertige Fliehkraftkupplung",
  "Alle 12 Positionen sind eingebaut (43 Einzelteile).",
  "Kontrolle: Antriebsnabe von Hand drehen → sie muss sich leicht drehen lassen, das Gehäuse bleibt stehen (Kupplung offen).",
  "Die Kollisionsprüfung der kompletten Baugruppe ergibt 0 Überschneidungen."),
]

with PdfPages("Montageablauf_Fliehkraftkupplung.pdf") as pdf:
    def p1(fig, ax):
        txt(ax, 15, 200, "Fliehkraftkupplung – Zusammenbau Schritt für Schritt", 18, weight="bold")
        txt(ax, 15, 189, "So bin ich vorgegangen", 12, weight="bold")
        txt(ax, 15, 182,
            "1. Datensatz gesichtet: STEP-Modelle von Pos. 1, 2, 4, 5 und 7, Zeichnungen 14.2.5.x, Stückliste.\n"
            "2. Einbaulage jedes STEP-Teils bestimmt: Achse = X, Passflächen gesucht (Lagersitze, Zentrierung Ø136, Flansche).\n"
            "3. Fehlende Teile modelliert: aus den Einzelteilzeichnungen (Pos. 3, 6, 9) oder aus den Normen (Pos. 8, 10, 11, 12). Die Zugfeder ist gespannt modelliert.\n"
            "4. Zusammengebaut in der Reihenfolge, in der man die Kupplung auch wirklich montiert (2 Unterbaugruppen, dann Endmontage).\n"
            "5. Kollisionsprüfung jedes Teils gegen jedes andere. 8 kleine Überschneidungen gefunden und behoben (Tabelle rechts unten).\n"
            "6. Jeden Montageschritt gerendert: neue Teile farbig, bereits montierte Teile grau.", 9, width=74)
        txt(ax, 15, 128, "Datengrundlage je Teil", 12, weight="bold")
        rows = [("1", "Antriebsnabe", "STEP-Modell (Datensatz)"), ("2", "Abtriebsnabe", "STEP-Modell (Datensatz)"),
                ("3", "Gehäuse", "aus Zeichnung 14.2.5.4 modelliert"), ("4", "Deckel", "STEP-Modell (Datensatz)"),
                ("5", "Fliehgewicht 5.1 + 5.2", "STEP-Modell (Datensatz)"), ("6", "Scheibe", "aus Zeichnung 14.2.5.7"),
                ("7", "Zugfeder", "Zeichnung 14.2.5.8, gespannt modelliert"), ("8", "Sicherungsscheibe", "DIN 6799 – 7 (Normtabelle), vereinfacht"),
                ("9", "Zylinderstift", "aus Zeichnung 14.2.5.9"), ("10", "Zylinderschraube", "ISO 4762 M8×20 (Normmaße), Gewinde nicht dargestellt"),
                ("11", "Rillenkugellager", "DIN 625 6009-2Z: d45/D75/B16, Kugeln vereinfacht"), ("12", "Filzring", "DIN 5419, Form aus der Deckelnut abgeleitet")]
        y = 121
        for r in rows:
            ax.text(15, y, r[0], fontsize=8.5, **F); ax.text(23, y, r[1], fontsize=8.5, **F); ax.text(62, y, r[2], fontsize=8.5, **F); y -= 5.2
        txt(ax, 15, 55, "Ergebnis: Für jedes Teil gab es genug Informationen (Modell, Zeichnung oder Norm). Kein Teil musste weggelassen werden. "
                       "Vereinfacht sind nur Normteile (Gewinde, Lager-Innenleben, Form der Sicherungsscheibe).", 9, width=70)
        img(fig, "steps/overview.png", 150, 85, 140, 72)
        txt(ax, 152, 80, "Gefundene Überschneidungen und Korrektur", 10, weight="bold")
        fixes = [("Lager ↔ Nabe / Abtriebsnabe", "Lagerringe hatten scharfe Kanten → Fase 0,8 mm (echte Lager: r = 1 mm)"),
                 ("Fliehgewicht ↔ Stift", "Bohrungsmitte war gerundet → exakter Wert aus dem STEP"),
                 ("Filzring ↔ Deckel", "Rechenungenauigkeit an der Nutflanke → 0,02 mm Luft"),
                 ("Lager ↔ Schulter", "0,003 mm Überdeckung = reine Anlage → 0,005 mm Luft"),
                 ("Feder / Sicherungsscheibe", "Lage nach Stiftzeichnung korrigiert (Nut 7 mm, Einstich 3 mm vom Ende)")]
        y = 73
        for a, b in fixes:
            ax.text(152, y, "• " + a, fontsize=8, **F, weight="bold"); ax.text(156, y-3.6, b, fontsize=8, **F); y -= 9
    page(pdf, p1)
    for i, (title, was, creo, hinweis) in enumerate(STEPS, 1):
        def ps(fig, ax, i=i, title=title, was=was, creo=creo, hinweis=hinweis):
            txt(ax, 12, 202, f"Schritt {i}: {title}", 16, weight="bold")
            det = f"steps/schritt_{i:02d}_detail.png"
            import os
            if os.path.exists(det):
                img(fig, f"steps/schritt_{i:02d}.png", 5, 52, 150, 140)
                img(fig, det, 152, 88, 140, 104)
                ax.text(222, 84, "Detail: oberer Drehpunkt", fontsize=8.5, ha="center", style="italic", **F)
                tx, tw = 160, 62
            else:
                img(fig, f"steps/schritt_{i:02d}.png", 5, 30, 190, 165)
                tx, tw = 200, 42
            ty = 77 if os.path.exists(det) else 185
            txt(ax, tx, ty, "Was passiert?", 10.5, weight="bold"); 
            body = was + "\n\n" + creo + "\n\n" + hinweis
            txt(ax, tx, ty-6, body, 9, width=tw)
            ax.text(285, 6, f"{i+1}/{len(STEPS)+1}", fontsize=8, ha="right", **F)
            ax.text(12, 6, "Farben: orange = neu eingebautes Teil, blau = Stifte, Ringe, Schrauben, rot = Federn, grün = Lager, gelb = Filzring, grau = bereits montiert", fontsize=8, **F)
        page(pdf, ps)
print("ok")
