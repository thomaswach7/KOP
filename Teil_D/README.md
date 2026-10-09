# Einzelteilzeichnungen – Fliehkraftkupplung

Gezeichnet sind **nur Teile, für die im Datensatz eine Bemaßung vorhanden ist**, also eine Einzelteilzeichnung 14.2.5.x.
Die Maße, Passungen, Oberflächen und Toleranzen folgen diesen Vorlagen und der Angabe Teil D.

| Datei | Teil | Vorlage | Blatt / Maßstab |
|---|---|---|---|
| `Pos01_Antriebsnabe.pdf` | Antriebsnabe, Aufbau, Schriftfeld und Schrift (Arial) wie Vorlage; A–A Halbschnitt, Nut links, Freistiche | 14.2.5.2 | A3 / 1:1 |
| `Pos01_Antriebsnabe.dxf` | Antriebsnabe als DXF zum Öffnen in Creo (→ .drw) | 14.2.5.2 | A3 / 1:1 |
| `Pos03_Gehaeuse.pdf` | Gehäuse | 14.2.5.4 | A4 / 1:1 |
| `Pos04_Deckel.pdf` | Deckel | 14.2.5.5 | A3 / 1:1, Einzelheit Z 2:1 |
| `Pos05_Fliehgewicht.pdf` | Fliehgewicht (5.1 + 5.2) | 14.2.5.6 | A3 / 1:1 |
| `Pos06_Scheibe.pdf` | Scheibe | 14.2.5.7 | A4 / 5:1 |
| `Pos07_Zugfeder.pdf` | Zugfeder | 14.2.5.8 | A4 / 2:1 |
| `Pos09_Zylinderstift.pdf` | Zylinderstift | 14.2.5.9 | A4 / 2:1 |
| `Einzelteilzeichnungen_alle.pdf` | alle 7 Blätter in einer Datei | | |
| `Modellbaum/` | **Modellbaum je Teil für Creo**: KE-Reihenfolge, Skizzen mit Maßen, Sollvolumen (PDF + README) | | |

## Antriebsnabe als Creo-Zeichnung (DXF → .drw)

1. In Creo: **Datei → Öffnen → Typ „DXF (*.dxf)“ → `Pos01_Antriebsnabe.dxf`**. Creo legt dabei eine neue Zeichnung an.
2. Im Importdialog Blattgröße **A3** und Einheit **mm** wählen. Die Zeichnung hat Maßstab 1:1, Ursprung links unten.
3. **Datei → Speichern** → es entsteht `pos01_antriebsnabe.drw`.

Wichtig: Die DXF-Zeichnung ist **nicht mit dem 3D-Modell verknüpft**. Maße sind Linien und Text, keine Creo-Bemaßungen.
Ändert sich das Modell, ändert sich die Zeichnung nicht mit. Wird eine aus dem Modell abgeleitete Zeichnung verlangt
(Ansichten aus der `.prt`), dient die DXF/PDF nur als Vorlage.

Layer: KANTEN 0,5 · DUENN 0,25 · MITTELLINIEN (CENTER) · TEXT · RAHMEN 0,7.
Lage von Ansichten und Maßen aus dem Scan der Vorlage 14.2.5.2 übernommen (Überlagerung geprüft).
Erzeugt mit `Skripte/gen_p1.py` (Ansichten aus dem Kontrollmodell mit Freistichen) → `Skripte/d_pos1.py` (PDF + DXF über `dxfout.py`).

## Nicht gezeichnet

- **Pos. 2 Abtriebsnabe:** Im Datensatz gibt es keine Zeichnung (14.2.5.3 fehlt). Laut Angabe Teil D gehört sie aber
  zur Abgabe. Frag bitte deine Lehrkraft nach der Zeichnung oder leite die Maße selbst aus dem STEP-Modell ab.
- **Pos. 8, 10, 11, 12:** Das sind Normteile (DIN 6799, ISO 4762, DIN 625, DIN 5419). Sie brauchen keine Einzelteilzeichnung.

## Form- und Lagetoleranzen (laut Angabe)

| Teil | Toleranz | Bezug |
|---|---|---|
| Pos. 1 | Gesamtrundlauf linker Lagersitz 0,05 | A = Achse Ø30H7 |
| | Koaxialität rechter Lagersitz Ø0,05 | B = Achse linker Lagersitz |
| | Gesamtplanlauf Armflächen 0,05 (beidseitig) | A |
| | Symmetrie Passfedernut 0,02 | A |
| Pos. 3 | Gesamtplanlauf Anlagefläche Abtriebsnabe 0,05 | A = Achse Ø136H7 |
| | Parallelität Anlagefläche Deckel 0,05 | B |
| Pos. 4 | Gesamtrundlauf Ø136h6 0,05 | A = Achse Ø75H7 |
| | Gesamtplanlauf Anlagefläche Gehäuse 0,05 | A |
| Pos. 5 | Rechtwinkligkeit 2× Ø8H9 Ø0,05 | A = Mittelebene Nut 20 |
| | Parallelität Nutflächen 0,05 | B |
| Pos. 6 | Parallelität Planflächen 0,05 | A |

## Fehler in den Buchvorlagen (zum Nachfragen bei der Lehrkraft)

1. **Deckel 14.2.5.5:** Der Gesamtplanlauf zeigt im Buch auf die Stirnfläche des Zentrierbunds. Die Angabe verlangt
   die **Anlagefläche zum Gehäuse**, also die Flanschfläche. In meiner Zeichnung ist er an der Flanschfläche.
2. **Antriebsnabe 14.2.5.2:** Dort steht „Gusstoleranz DIN 1688“. Das ist die Norm für Leichtmetallguss, richtig ist **DIN 1686**.
3. **Fliehgewicht:** Die Buchmaße R52 und 113° weichen vom STEP-Modell ab (R51,5 und 112,5°). Gezeichnet ist nach Buch.
4. **Zugfeder:** Laut Buch hat die Öse Ø8 außen bei Draht Ø1,1, also nur etwa Ø5,8 innen. Der Einstich im Zylinderstift hat aber Ø6,8.
   Die Feder lässt sich so nicht einhängen.
5. **Ergänzte Maße:** Im Buch fehlt am Deckel der Außendurchmesser des Lagerrohrs. Ich habe **Ø84** aus dem Modell ergänzt.
   R60 am Fliehgewicht habe ich ebenfalls ergänzt.
