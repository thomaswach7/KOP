# Teil A – Gesamtzeichnung Fliehkraftkupplung (Stand: Pos. 1 bis 8)

## Inhalt

| Datei | Beschreibung |
|---|---|
| `Gesamtzeichnung_Fliehkraftkupplung_Pos1-8.pdf` | Gesamtzeichnung A3, M 1:1, Längsschnitt A–A + Vorderansicht ohne Pos. 2, Stückliste Pos. 1–8 |
| `Gesamtzeichnung_Vorschau.png` | Vorschaubild der Zeichnung |
| `CAD/Baugruppe_Fliehkraftkupplung_Pos1-8.step` | Komplette Baugruppe (alle Teile in Einbaulage, kollisionsgeprüft) |
| `CAD/Einzelteile_neu/*.step` | Teile, für die im Datensatz **kein STEP** vorhanden war (Pos. 3, 6, 7 gespannt, 8) |
| `Skripte/` | Python/CadQuery-Skripte, mit denen Baugruppe und Zeichnung erzeugt wurden (STEP-Ordner `../Fliehkraftkupplung/` neben `Skripte` erwartet) |

> **Wichtig:** Die Abgabe verlangt eine Baugruppe **in eurem CAD-System**. Die STEP-Baugruppe
> kannst du direkt importieren oder als Kontrollmodell neben deine eigene Baugruppe legen.
> Die Einbaumaße unten gelten 1:1 für die Abhängigkeiten in Inventor, SolidWorks, Creo usw.

## Koordinatensystem der Baugruppe

- Kupplungsachse = **X-Achse**, X = 0 an der Außenplanfläche des Deckels (Pos. 4)
- Vorderansicht = Blick aus +X (von der Abtriebsseite), rechts = +Y, oben = +Z
- Schnittebene A–A = Ebene Y = 0 (geht durch die Drehpunkt-Bolzen und je 2 Schrauben)

## Einbaulage der Teile (Abhängigkeiten)

| Pos. | Teil | Lage in der Baugruppe | Abhängigkeiten im CAD |
|---|---|---|---|
| 4 | Deckel | X = 0 … 29 (Flansch 0–12, Zentrierbund 12–19) | **Fixieren** (Basisteil); Bohrungen Ø9 auf Teilkreis Ø150 bei 30°, 90°, 150° … |
| 3 | Gehäuse | X = 12 … 82, Ø170/Ø136 | Ø136 koaxial zum Zentrierbund Deckel; Planfläche an Deckel-Flansch (X = 12); Gewinde M8 fluchtend mit Deckelbohrungen |
| 2 | Abtriebsnabe | X = 65 … 137, **gespiegelt** (Zentrierbund zeigt zum Deckel) | Zentrierbund koaxial Ø136; Flanschfläche an Gehäuse (X = 82); Bohrungen fluchtend mit Gehäusegewinde |
| 1 | Antriebsnabe | X = 0 … 81, Arme nach oben/unten (Bohrungen Ø8 bei 90° und 270°, r = 52), Passfedernut nach +Y | koaxial; linker Lagersitz Ø45 bei X = 13…29 (Wellenschulter X = 29), rechter Lagersitz X = 65…81 |
| 5 | Fliehgewicht (2×) | Mitte X = 47 (Breite 54: X = 20…74) | Gewicht A: Bohrung Ø8 koaxial Bohrung **oben** (90°) der Antriebsnabe, Nut (20 mm) symmetrisch zum Arm (17 mm). Gewicht B: dasselbe **unten** (270°). Freie Bohrungen liegen dann bei ≈ 46° bzw. 226°. Belag hat ≈ 2,7 mm Luft zum Gehäuse (Ruhelage). |
| 6 | Scheibe 16 × 9 × 1,5 (4×) | Nur auf den **Drehpunkt-Bolzen**: X = 37…38,5 und 55,5…57 | koaxial zur Bohrung; Planfläche an Nabenarm (füllt Spalt 20 − 17 = 2 × 1,5) |
| 7 | Zugfeder (4×) | Je 2 Federn pro Federpaar: X = 24,85 und 69,15 (Öse im Einstich R0,6 des Bolzens) | Öse koaxial: Feder 1 verbindet Bolzen 90° ↔ freier Bolzen Gewicht B (≈ 46°), Feder 2 verbindet 270° ↔ 226°. **Eingebaute Länge Ösenmitte–Ösenmitte = 38,8 mm** → gespannte Feder verwenden (`Pos07_Zugfeder_gespannt.step`) |
| 8 | Sicherungsscheibe DIN 6799 – 7 (8×) | Auf allen 4 Bolzen, X = 28,89…29,79 und 64,21…65,11 (Nut Ø7 × 0,94 im Bolzen) | koaxial zur Bolzenbohrung; Planfläche 17,21 mm von der Mitte (X = 47) |

Daten zu Pos. 8 (DIN 6799, Größe 7): Nut-Ø 7, Wellenbereich 8–11 mm, s = 0,9 mm, Nutbreite m = 0,94 mm,
Außen-Ø ≈ 14,3 mm, Öffnung 5,84 mm. Die Kontur ist vereinfacht als C-Form modelliert. In deinem
CAD-System das Teil aus der **Normteilbibliothek** nehmen.

## Zeichnungsregeln, die umgesetzt sind

- Schnittverlauf A–A durch Zylinderstift-Achsen (Drehpunkte 90°/270°) und Schrauben-/Gewindebohrungen
- **Nicht geschnitten:** Normteil Pos. 8 und die Federn Pos. 7. Pos. 9 und 10 (Stifte, Schrauben) folgen in der nächsten Stufe.
- Angrenzende Teile mit unterschiedlicher Schraffurrichtung/-abstand, Belag (5.2) kreuzschraffiert
- Gewinde M8 im Gehäuse: Kernloch breit, Nenndurchmesser schmal, Gewindeende breit
- Positionsnummern im Uhrzeigersinn (4 → 5 → 6 → 7 → 8 → 1 → 2 → 3), Hinweislinien mit Punkt in der Fläche
- Stückliste über dem Schriftfeld (DIN EN ISO 7200), Projektionsmethode 1 (Symbol im Schriftfeld)

## Fehler / Unstimmigkeiten in den Unterlagen (bitte beachten)

1. **Zugfeder passt laut Zeichnung nicht auf den Bolzen:** Die Zeichnung (14.2.5.8) gibt einen Außen-Ø von 8 bei
   Draht-Ø 1,1 an. Die Öse hat damit innen nur ≈ 5,8 mm, der Bolzen-Einstich hat aber Ø 6,8. Das STEP-Modell der
   Feder hat dagegen ≈ Ø 9,2 außen. Die Öse ist deshalb mit Innen-Ø 6,8 modelliert, damit sie im Einstich sitzt.
2. **Feder nur ungespannt vorhanden:** Die Ösen liegen im STEP-Modell ≈ 22,9 mm auseinander, eingebaut sind es aber 38,8 mm.
   Im CAD die Feder deshalb gespannt modellieren, sonst entsteht keine Verbindung zum Bolzen.
3. **STEP-Dateien fehlen** für das Gehäuse (Pos. 3), die Scheibe (Pos. 6) und den Zylinderstift (Pos. 9).
   Pos. 3 und Pos. 6 sind nach den Einzelteilzeichnungen 14.2.5.4 und 14.2.5.7 nachmodelliert. Der Ordner 14.2.7 (Keilwelle) fehlt ebenfalls.
4. **Falsche Positionsnummern in den Buchunterlagen:**
   - Die Zeichnung der Zugfeder heißt „…_Pos_14“, richtig ist Pos. 7.
   - Die Form- und Lagetoleranzen sprechen beim Fliehgewicht vom „Zylinderstift (Pos. 11)“, richtig ist Pos. 9.
5. **Pos. 5 auf der Zeichnung:** Das Fliehgewicht ist als Baugruppe mit „5“ gekennzeichnet, wie im Original.
   5.1 und 5.2 stehen nur in der Stückliste. Falls deine Lehrkraft 5.1 und 5.2 einzeln sehen will, zwei Hinweislinien ergänzen.
