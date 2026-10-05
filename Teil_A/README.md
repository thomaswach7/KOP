# Teil A – Baugruppe und Gesamtzeichnung Fliehkraftkupplung (komplett, Pos. 1 bis 12)

## Inhalt

| Datei | Beschreibung |
|---|---|
| `Montageablauf/Montageablauf_Fliehkraftkupplung.pdf` | **Zusammenbau Schritt für Schritt** (12 Schritte mit 3D-Bildern und Erklärung) |
| `Montageablauf/README.md` | derselbe Ablauf zum Lesen direkt auf GitHub |
| `Gesamtzeichnung_Fliehkraftkupplung.pdf` | Gesamtzeichnung A3, M 1:1: Längsschnitt A–A, Vorderansicht ohne Pos. 2 und 10, Stückliste Pos. 1–12 |
| `Gesamtzeichnung_Vorschau.png` | Vorschaubild der Gesamtzeichnung |
| `CAD/Baugruppe_Fliehkraftkupplung_komplett.step` | komplette Baugruppe, 43 Einzelteile, kollisionsfrei |
| `CAD/Einzelteile_neu/*.step` | Teile ohne STEP im Datensatz: Pos. 3, 6, 7 (gespannt), 8, 9, 10, 11, 12 |
| `Skripte/` | Python/CadQuery-Skripte (Aufbau, Kollisionsprüfung, Renderbilder, Zeichnung) |

> Die Abgabe verlangt die Baugruppe in **eurem CAD-System (Creo)**. Die STEP-Baugruppe und die Bilder sind
> eine Vorlage zum Nachbauen und Kontrollieren.

## Koordinatensystem der Baugruppe

- Kupplungsachse = **X-Achse**, X = 0 an der Außenfläche des Deckels (Pos. 4)
- Vorderansicht = Blick aus +X, rechts = +Y, oben = +Z
- Schnittebene A–A = Ebene Y = 0 (durch die Drehpunkt-Stifte und je 2 Schrauben)

## Einbaulage aller Teile

| Pos. | Teil | Lage in der Baugruppe | Abhängigkeiten in Creo |
|---|---|---|---|
| 4 | Deckel | X 0 … 29 | Standard (Basisteil) |
| 3 | Gehäuse | X 12 … 82 | Ø136 koaxial, Planfläche an Deckelflansch (X = 12), Gewinde fluchtend mit Bohrungen |
| 2 | Abtriebsnabe | X 65 … 137, Zentrierbund zum Deckel | Ø136 koaxial, Flansch an Gehäuse (X = 82), Bohrungen fluchtend |
| 1 | Antriebsnabe | X 0 … 81, Arme oben/unten | koaxial, Stirnfläche bündig mit Deckel-Außenfläche, FRONT ↔ FRONT Deckel |
| 11 | Rillenkugellager 6009-2Z (2×) | X 13 … 29 und 65 … 81 | Innenring auf Ø45k6 an Wellenschulter, Außenring in Ø75H7 |
| 12 | Filzring | X 2,8 … 8,2, in der Nut des Deckels | koaxial, in der Nut zentriert |
| 6 | Scheibe (4×) | X 37 … 38,5 und 55,5 … 57 auf den Drehpunkten | koaxial Armbohrung, an Armseite |
| 5 | Fliehgewicht (2×) | Mitte X = 47 | Bohrung koaxial Arm, Nut an Scheibe, Winkelversatz 68,1° |
| 9 | Zylinderstift (4×) | X 22 … 72 (mittig) | koaxial Bohrung, mittig |
| 8 | Sicherungsscheibe (8×) | in der Stiftnut 7 mm vom Ende: X 29,04 … 29,94 und 64,06 … 64,96 | koaxial Stift, an Nutflanke |
| 7 | Zugfeder (4×) | Öse im Einstich R0,6, 3 mm vom Stiftende: X = 25 und 69 | Ösen koaxial zu zwei Stiften; eingebaut 38,8 mm Ösenabstand |
| 10 | Zylinderschraube M8 × 20 (12×) | Kopf auf Senkungsgrund: Deckelseite X 0,6 … 28,6, Abtriebsseite X 65,4 … 93,4 | koaxial Bohrung, Kopfauflage an Senkungsgrund |

## Zeichnungsregeln, die umgesetzt sind

- Schnitt A–A durch die Stiftachsen und Schrauben.
- **Nicht geschnitten:** Wellen-ähnliche Normteile und Verbindungselemente, also Stifte (9), Schrauben (10), Sicherungsscheiben (8), Federn (7) und Lagerkugeln.
- Lagerringe sind geschnitten, die Kugeln nicht. Filzring und Belag sind kreuzschraffiert.
- Gewinde: Die Schraube ist eingeschraubt (Kern-Ø schmal), im Gehäuse bleibt ein freier Gewinderest mit Gewindeende.
- Positionsnummern im Uhrzeigersinn wie in der Buchvorlage: rechts 1–3, unten 5–10, links 4, 11, 12. Pos. 7 steht in der Vorderansicht.
- Stückliste nach DIN EN ISO 7200 links unten. Projektionsmethode 1.

## Unstimmigkeiten in den Unterlagen

1. **Zugfeder:** Laut Zeichnung ist die Öse innen nur etwa Ø5,8 groß, der Stifteinstich hat aber Ø6,8. Modelliert ist die Öse mit Ø6,8 innen.
2. **Feder nur ungespannt im Datensatz:** Frei liegen die Ösen 22,9 mm auseinander, eingebaut sind es 38,8 mm.
3. **STEP fehlt** für Pos. 3, 6 und 9. Die Teile sind nach den Zeichnungen 14.2.5.4, 14.2.5.7 und 14.2.5.9 modelliert.
4. **Positionsnummern im Buch:** Die Zeichnung der Zugfeder heißt „…Pos_14“, im Fliehgewicht-Text steht „Zylinderstift Pos. 11“. Richtig sind Pos. 7 und Pos. 9.
