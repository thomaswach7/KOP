# Teil D – Einzelteilzeichnungen Pos. 1 bis 5

| Datei | Teil | Blatt | Ansichten |
|---|---|---|---|
| `Pos01_Antriebsnabe.pdf` | Antriebsnabe (Pos. 1) | A3, 1:1 | Ansicht von rechts + Schnitt A–A |
| `Pos02_Abtriebsnabe.pdf` | Abtriebsnabe (Pos. 2) | A3, 1:1 | Ansicht von der Lagerseite + Schnitt A–A |
| `Pos03_Gehaeuse.pdf` | Gehäuse (Pos. 3) | A4, 1:1 | Halbschnitt |
| `Pos04_Deckel.pdf` | Deckel (Pos. 4) | A3, 1:1 | Ansicht von der Lagerseite + Halbschnitt A–A + Einzelheit Z (2:1) |
| `Pos05_Fliehgewicht.pdf` | Fliehgewicht (Pos. 5) | A3, 1:1 | Vorderansicht + Schnitt A–A |
| `Einzelteilzeichnungen_Pos1-5.pdf` | alle 5 Blätter in einer Datei | | |

Die Geometrie ist mit HLR direkt aus den STEP-Modellen abgeleitet, die Maße stammen aus den Modellen.
Die Toleranzen sind nach Angabe Teil D umgesetzt:

- ISO 2768-mK, Einheitsbohrung, Werkstückkanten ISO 13715 (−0,3 / +0,3), Oberflächen DIN EN ISO 1302, Gusstoleranzen DIN 1686 GTB 18 (nur Gussteile)
- Oberflächen: Lagersitze und Zentrierungen z (Rz 4), Bohrungen und Anlageflächen y (Rz 16), sonstige bearbeitete Flächen x (Rz 63). Rohgussflächen über die Sammelangabe.
- Form- und Lagetoleranzen:

| Teil | Toleranz | Bezug |
|---|---|---|
| Pos. 1 | Gesamtrundlauf linker Lagersitz 0,05 | A = Achse Ø30H7 |
| | Koaxialität rechter Lagersitz Ø0,05 | B = Achse linker Lagersitz |
| | Gesamtplanlauf Armflächen 0,05, beidseitig | A |
| | Symmetrie Passfedernut 0,02 | A |
| Pos. 2 | Gesamtrundlauf Ø136h6 0,05 | A = Achse Ø30H7 |
| | Koaxialität Lagersitz Ø75H7 Ø0,05 | A |
| | Gesamtplanlauf Anlagefläche Gehäuse 0,05 | A |
| Pos. 3 | Gesamtplanlauf Anlagefläche Abtriebsnabe 0,05 | A = Achse Ø136H7 |
| | Parallelität Anlagefläche Deckel 0,05 | B = Anlagefläche Abtriebsnabe |
| Pos. 4 | Gesamtrundlauf Ø136h6 0,05 | A = Achse Ø75H7 |
| | Gesamtplanlauf Anlagefläche Gehäuse 0,05 | A |
| Pos. 5 | Rechtwinkligkeit 2× Ø8H9 Ø0,05 | A = Mittelebene Nut 20 |
| | Parallelität Nutflächen 0,05 | B = eine Nutfläche |

## Abtriebsnabe (Pos. 2): neu erstellt

Für dieses Teil gibt es im Datensatz keine Zeichnung (14.2.5.3 fehlt). Alle Maße stammen aus dem
STEP-Modell und passen zu den Gegenstücken:

- Ø136h6 ↔ Gehäuse Ø136H7
- Ø75H7 ↔ Lager 6009
- Lochbild 6× Ø9H13 / Senkung Ø15H13 ↧8,6 auf Ø150 ↔ Gehäusegewinde M8

Die Sachnummer 14.2.5.3 ist angenommen und folgt der Nummerierung im Buch.

## Abweichungen und Fehler, die mir aufgefallen sind

1. **Fliehgewicht R52 / R51,5:** Die Buchzeichnung 14.2.5.6 gibt R52 an, das STEP-Modell hat R51,5.
   Die Augenmitten liegen ebenfalls auf R51,5. Ich habe **R51,5** eingetragen.
2. **Fliehgewicht 113° / 112,5°:** Das Modell ergibt 2 × 56,25° = 112,5°, das Buch rundet auf 113°. Eingetragen ist **112,5°**.
3. **Fliehgewicht, Bohrungen und Augen nicht konzentrisch:** Die Bohrungen Ø8H9 (Abstand 95,77) liegen 0,3 mm neben
   den Augenmitten (R51,5 / 135°). Das steht so in Modell und Buch. Ich habe die Bohrungen mit 95,77 und 19,24 bemaßt.
4. **Belagenden:** Die Einlaufschräge ist nur als Hinweis „1,5 × 5 nach Zeichnung 14.2.5.6“ angegeben.
   Im Modell sind es ≈ 1,7 × 5,3.
5. **Gusstoleranz-Norm:** Die Buchzeichnung der Antriebsnabe nennt „DIN 1688“. Das ist die Norm für **Leichtmetall**guss
   und für EN-GJS falsch. Richtig ist DIN 1686 (wie in der Angabe). Beide Normen sind übrigens zurückgezogen, aktuell gilt
   DIN EN ISO 8062-3. Das wäre ein Verbesserungsvorschlag, wenn die Lehrkraft die aktuelle Norm sehen will.
6. **Ø85,3 (Pos. 2) und Ø84 (Pos. 4):** Das sind Rohgussmaße an den Außendurchmessern der Lagerrohre mit 5° Aushebeschräge.
   Sie sind im Modell nicht rund konstruiert (85,26 / 84,02) und deshalb gerundet eingetragen. Sie unterliegen der Gusstoleranz.

> In Creo werden die Zeichnungen wieder aus deinen Modellen abgeleitet. Die PDFs zeigen dir, welche Maße,
> Passungen, Oberflächen und Toleranzen pro Teil hineingehören und wo sie sinnvoll platziert werden.

Die Python-Skripte in `Skripte/` (CadQuery + matplotlib) erzeugen die PDFs. Erwartet wird der entpackte Datensatz in `../Fliehkraftkupplung/`.
