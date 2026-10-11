# Fliehkraftkupplung in Creo 12 zusammenbauen – Klick für Klick

Diese Anleitung ist für **deine eigenen Creo-Teile**. Die Ebenen (FRONT, RIGHT, TOP, DTM1) sind so benannt wie in der
Modellbaum-Anleitung (`Teil_D/Modellbaum/README.md`). Hast du anders modelliert, nimm die passende Fläche oder Achse.
Die Bilder zu jedem Schritt findest du in `README.md` in diesem Ordner, mit derselben Reihenfolge.

**Koordinaten zum Kontrollieren:** Kupplungsachse = X. X = 0 ist die Außenfläche des Deckels, und die Antriebsnabe ist dort bündig.

---

## 0. Vorbereitung

### 0.1 Fehler in deinen Dateien beheben

| Datei | Problem | Behebung |
|---|---|---|
| Antriebsnabe | Der interne allgemeine Name ist **„asd“**. So erscheint das Teil in Modellbaum und Stückliste. | Teil öffnen → **Datei → Verwalten → Umbenennen** → *Neuer allgemeiner Name*: `ANTRIEBSNABE` |
| Scheibe | Der allgemeine Name ist **„PRT0001“** (Creo-Vorgabe). | genauso: `SCHEIBE` |
| Gehäuse | Der Name enthält ein **Ä** („GEHÄUSE“). Umlaute machen beim Austausch und bei PDM oft Probleme. | `GEHAEUSE` |
| alle | Die Dateien heißen bei dir „…Finalle…“. Das ist ein Tippfehler, und so ist es keine `.prt`-Endung. | Die Dateien müssen `name.prt` bzw. `name.prt.1` heißen, sonst öffnet Creo sie nicht. Am besten `antriebsnabe.prt`, `gehaeuse.prt`, `fliehgewicht.prt`, `scheibe.prt`, `zylinderstift.prt`. |

**Wichtig:** Benenne die Teile **vor** dem Zusammenbau um. Später nur noch über *Datei → Verwalten → Umbenennen* mit
geöffneter Baugruppe, sonst findet die Baugruppe ihre Teile nicht mehr.

### 0.2 Fehlende Teile

Diese Teile hast du mir nicht geschickt. Sie müssen vor dem Zusammenbau vorhanden sein:

| Pos. | Teil | Herkunft |
|---|---|---|
| 2 | Abtriebsnabe | selbst modellieren (Modellbaum-Anleitung) |
| 4 | Deckel | selbst modellieren |
| 7 | Zugfeder (4×) | selbst modellieren |
| 8 | Sicherungsscheibe DIN 6799 – 7 (8×) | **Normteil** |
| 10 | Zylinderschraube ISO 4762 – M8 × 20 – 8.8 (12×) | **Normteil** |
| 11 | Rillenkugellager DIN 625 – 6009-2Z (2×) | **Normteil** |
| 12 | Filzring DIN 5419 – 45 (1×), in der Buch-Stückliste steht „M5 × 45“ | **Normteil** |

**So findest du die Normteile:**

- **Schrauben (10):** Register **Modell → Intelligent Fastener → Schraube**. Dort ISO 4762, M8, Länge 20 wählen. Siehe Schritt 13.
- **Lager, Sicherungsscheibe, Filzring:** aus eurer Creo-Normteilbibliothek, also dem Bibliotheksordner, den die Schule eingerichtet hat.
- **Wenn ein Normteil fehlt:**
  - Die STEP-Dateien liegen in `Teil_A/CAD/Einzelteile_alle/`.
  - Hersteller-CAD gibt es zum Beispiel bei SKF/Schaeffler für das Lager oder bei CADENAS PARTcommunity, auch als Creo-Format.

### 0.3 Baugruppe anlegen

1. Lege **alle Teile in einen Ordner**. Dann **Datei → Arbeitsverzeichnis festlegen** auf diesen Ordner.
2. **Datei → Neu → Baugruppe**, Untertyp **Konstruktion**. Name: `FLIEHKRAFTKUPPLUNG`.
   Den Haken bei *Standardvorlage verwenden* entfernen und **`mmns_asm_design_abs`** wählen (mm, N, s).
3. Lege zuerst die **Unterbaugruppe Fliehgewicht** an. In der Stückliste ist Pos. 5 „Fliehgewicht (komplett)“, das besteht aus 5.1 und 5.2:
   - **Neu → Baugruppe** `FLIEHGEWICHT` anlegen.
   - Gewicht 5.1 mit **Standard** einbauen.
   - Belag 5.2 so einbauen:
     - Achse der Bögen **koinzident** Achse der Bögen
     - FRONT ↔ FRONT **koinzident**
     - RIGHT ↔ RIGHT **koinzident**
   - Speichern.

   *Ist bei dir der Belag schon im Teil fliehgewicht.prt enthalten, entfällt das. Dann fehlt aber Pos. 5.2 als eigene Position in der Stückliste.*

**Bedienung beim Einbauen:**

- **Teil holen:** *Modell → Komponente → Zusammenbauen* → Teil wählen. Es öffnet sich das Register **Komponentenplatzierung**.
- **Abhängigkeit setzen:** Abhängigkeitstyp aus der Liste wählen, dann zuerst die Referenz am **neuen Teil** und danach die Referenz an der **Baugruppe** anklicken.
- **Weitere Abhängigkeit:** Im Unterregister *Platzierung* → **Neue Abhängigkeit**.
- **Falsche Richtung:** Liegt das Teil verkehrt herum, auf **Umkehren** klicken.
- **Fertig:** Erst wenn unten **„Vollständig platziert“** steht, mit ✓ bestätigen.
- **Keine Achse vorhanden:** Hat ein Teil keine Achse, klick die Zylinderfläche an. Creo macht daraus automatisch „koaxial“.
- **Gleiches Teil noch einmal:** Im Modellbaum Rechtsklick auf das eingebaute Teil → **Wiederholen**. Dann musst du nur die geänderten Referenzen neu anklicken.

---

## 1. Antriebsnabe (Pos. 1) – Basisteil

**Zusammenbauen** → `antriebsnabe.prt` → Abhängigkeit **Standard** → ✓.

Damit liegen die Ebenen der Nabe auf den Ebenen der Baugruppe:
- Die Arme liegen in **FRONT**.
- **DTM1** ist die Mitte der Arme (47 mm von der Stirnfläche).
- Die Kupplungsachse ist die Achse des Drehkörpers.

## 2. Scheiben (Pos. 6) – 4 Stück

Je Arm kommt eine Scheibe links und eine rechts an die Armseite.

| Nr | Abhängigkeit | Scheibe | Baugruppe |
|---|---|---|---|
| 1 | Koinzident | Achse der Scheibe | Achse der Armbohrung Ø8 (oben) |
| 2 | Koinzident | Planfläche der Scheibe | linke Seitenfläche des oberen Arms |

Danach dreimal **Wiederholen**: rechte Armseite oben, dann linke und rechte Armseite unten.
**Kontrolle:** Arm 17 + 2 × 1,5 = 20 = Nutbreite des Fliehgewichts.

## 3. Fliehgewichte (Pos. 5) – 2 Stück

`fliehgewicht.asm` (bzw. `.prt`) einbauen:

| Nr | Abhängigkeit | Fliehgewicht | Baugruppe |
|---|---|---|---|
| 1 | Koinzident | Achse der Drehpunkt-Bohrung Ø8H9 | Achse der oberen Armbohrung |
| 2 | Koinzident | FRONT des Gewichts (Nut-Mittelebene) | DTM1 der Antriebsnabe (Armmitte) |
| 3 | Winkelversatz | RIGHT des Gewichts (Symmetrieebene) | FRONT der Antriebsnabe (Ebene der Arme) |

**Winkel bei Nr. 3:**
- **67,5°**, wenn die Bohrungen wie in der Modellbaum-Anleitung bei ±67,5° liegen.
- **68,1°**, wenn du nach dem Buch bzw. STEP gebaut hast (Bohrungsabstand 95,77).

Das ist die Ruhelage, in der die Feder das Gewicht nach innen zieht.

- **Lage prüfen:** Das Gewicht muss **um die Achse herum** liegen, mit dem Belag außen und dem freien Auge auf der anderen Seite der Achse. Liegt es nach außen weg, bei Nr. 3 **Umkehren** klicken oder den Winkel negativ eingeben.
- **Zweites Gewicht:** am **unteren** Arm genauso einbauen. Die beiden Gewichte müssen **punktsymmetrisch** liegen, also um 180° um die Achse gedreht.
- **Kontrolle:** Analyse → Messen → Abstand Belag ↔ Gehäuse-Innenfläche ergibt **ca. 2,5–3,5 mm** Luft. Das kannst du erst nach Schritt 10 messen.

*Optional für Bewegung (Mechanismus):* Statt Nr. 1 bis 3 kannst du den Verbindungstyp **Stift** verwenden. Dann lässt sich das Gewicht später mit der Maus schwenken.

## 4. Zylinderstifte (Pos. 9) – 4 Stück

Es gibt zwei Stifte als Drehpunkt (durch Gewicht, Scheiben und Arm) und zwei Stifte im freien Auge der Gewichte.

| Nr | Abhängigkeit | Stift | Baugruppe |
|---|---|---|---|
| 1 | Koinzident | Achse des Stifts | Achse der Bohrung |
| 2 | Koinzident | DTM1 des Stifts (Stiftmitte, 25 mm) | DTM1 der Antriebsnabe |

**Wiederholen** für die anderen drei Bohrungen.
**Kontrolle:** Der Stift ist 50 mm lang und ragt auf jeder Seite **8 mm** aus dem Auge (Auge 34 breit).

## 5. Sicherungsscheiben (Pos. 8) – 8 Stück

| Nr | Abhängigkeit | Sicherungsscheibe | Baugruppe |
|---|---|---|---|
| 1 | Koinzident | Achse | Achse des Stifts |
| 2 | Koinzident | Planfläche | **innere** Nutflanke (die Flanke zum Gewicht hin, 7,94 mm vom Stiftende) |

Für die richtige Seite gegebenenfalls **Umkehren** klicken. Die Scheibe muss in der Nut liegen und darf nicht in den Stift ragen.
Danach 7× **Wiederholen**, also 2 je Stift.

*Optional:* Mit einer dritten Abhängigkeit (Winkel) die Öffnung radial nach außen drehen.

## 6. Zugfedern (Pos. 7) – 4 Stück

- **Feder 1** verbindet den **oberen Drehpunkt-Stift** mit dem **freien Stift des unteren Gewichts**.
- **Feder 2** verbindet den **unteren Drehpunkt-Stift** mit dem **freien Stift des oberen Gewichts**.
- Je eine Feder vorne und eine hinten, also 4 Stück.

| Nr | Abhängigkeit | Feder | Baugruppe |
|---|---|---|---|
| 1 | Koinzident | Achse von Öse 1 | Achse des Drehpunkt-Stifts |
| 2 | Abstand **3** | Mittelebene der Öse (FRONT der Feder) | Stirnfläche des Stifts (Öse sitzt im Einstich R0,6) |
| 3 | Koinzident | Achse von Öse 2 | Achse des freien Stifts |

**Problem:** Deine Feder ist **ungespannt** gezeichnet, mit 22,9 mm Ösenabstand. Eingebaut sind es **38,8 mm**.
Nr. 3 geht deshalb erst auf, wenn die Feder länger wird. Dafür gibt es zwei Wege:

- **Flexible Feder (empfohlen):** Im Modellbaum Rechtsklick auf die Feder → **Flexibel machen** → das Längenmaß bzw. die Steigung wählen → *Messung*: Abstand zwischen den zwei Stiftachsen.
- **Zweites Modell:** ein eigenes Federmodell `zugfeder_gespannt.prt` mit 38,8 mm Ösenabstand (Steigung entsprechend größer).

**Bekannter Buchfehler:** Die Öse ist innen nur Ø5,8, der Einstich im Stift hat aber Ø6,8. Die globale Interferenz meldet hier deshalb eine Überschneidung.
Frag bei der Lehrkraft nach. In unserem Kontrollmodell ist die Öse innen Ø6,8.

## 7. Rillenkugellager (Pos. 11) – 2 Stück

| Nr | Abhängigkeit | Lager | Baugruppe |
|---|---|---|---|
| 1 | Koinzident | Achse der Bohrung | Kupplungsachse (Antriebsnabe) |
| 2 | Koinzident | Stirnfläche des Innenrings | Wellenschulter (Ø51) links bzw. rechts |

- **Linkes Lager:** X **13 … 29**.
- **Rechtes Lager:** X **65 … 81**. Dafür **Wiederholen** und die andere Schulter anklicken.
- Die Lagerstirnfläche muss **bündig mit der Nabenstirnfläche** bei X = 81 sein. So kannst du es kontrollieren.

## 8. Abtriebsnabe (Pos. 2)

| Nr | Abhängigkeit | Abtriebsnabe | Baugruppe |
|---|---|---|---|
| 1 | Koinzident | Achse | Kupplungsachse |
| 2 | Koinzident | Schulter des Lagersitzes Ø75H7 | Außenring-Stirnfläche des rechten Lagers (X = 81) |
| 3 | Winkelversatz 0 | FRONT der Abtriebsnabe | FRONT der Baugruppe (nur damit sie sich nicht mehr dreht) |

**Kontrolle:**
- Die Abtriebsnabe liegt bei **X 65 … 137**.
- Die Flanschfläche zum Gehäuse liegt bei **X = 82**.

## 9. Schrauben Abtriebsseite – folgt in Schritt 13

## 10. Gehäuse (Pos. 3)

| Nr | Abhängigkeit | Gehäuse | Baugruppe |
|---|---|---|---|
| 1 | Koinzident | Innenfläche Ø136 (Achse) | Achse der Abtriebsnabe |
| 2 | Koinzident | rechte Stirnfläche | Flanschfläche der Abtriebsnabe (X = 82) |
| 3 | Koinzident | Achse einer Gewindebohrung M8 | Achse einer Senkbohrung der Abtriebsnabe |

Das Gehäuse liegt dann bei **X 12 … 82**. Die Zentrierung Ø136H7/h6 steckt über dem Zentrierring der Abtriebsnabe.

## 11. Filzring (Pos. 12)

| Nr | Abhängigkeit | Filzring | Baugruppe |
|---|---|---|---|
| 1 | Koinzident | Achse | Kupplungsachse |
| 2 | Koinzident | Seitenfläche | Nutflanke im Deckel (alternativ: Abstand 2,78 zur Außenfläche X = 0) |

Wenn du zuerst den Deckel einbaust (Schritt 12), kannst du direkt die Nutflanke anklicken. Das ist einfacher.

## 12. Deckel (Pos. 4)

| Nr | Abhängigkeit | Deckel | Baugruppe |
|---|---|---|---|
| 1 | Koinzident | Achse | Kupplungsachse |
| 2 | Koinzident | Flanschfläche (Innenseite, X = 12) | linke Stirnfläche des Gehäuses |
| 3 | Koinzident | Achse einer Senkbohrung | Achse einer Gewindebohrung des Gehäuses |

**Kontrolle:**
- Die Deckel-Außenfläche ist **bündig mit der Stirnfläche der Antriebsnabe** (X = 0).
- Die Lagersitzschulter im Deckel (X = 13) **berührt den Außenring des linken Lagers**. Analyse → Messen → Abstand = 0.

Ist dort ein Spalt oder eine Überschneidung, stimmt ein Längenmaß in Nabe, Deckel, Gehäuse oder Abtriebsnabe nicht.

## 13. Zylinderschrauben (Pos. 10) – 12 Stück

**Mit Intelligent Fastener:**

1. Register *Modell* → **Intelligent Fastener → Schraube** wählen.
2. Als Referenz die **Senkbohrung im Deckel** anklicken. Die Bohrung muss ein Bohrungs-KE sein.
3. Norm **ISO 4762**, **M8**, Länge **20**. Keine Scheibe und keine Mutter.
4. Ist die Bohrung gemustert, fragt Creo nach dem **Muster** → **Ja**. Dann werden alle 6 Schrauben gesetzt.
5. Dasselbe an der **Abtriebsnabe** wiederholen.

**Ohne Intelligent Fastener** (Schraube aus der Bibliothek oder als STEP):

| Nr | Abhängigkeit | Schraube | Baugruppe |
|---|---|---|---|
| 1 | Koinzident | Achse | Achse der Senkbohrung |
| 2 | Koinzident | Kopfauflage (Unterseite des Kopfs) | Senkungsgrund (8,6 tief) |

Danach die Schraube anklicken → **Muster** → Typ **Referenz** → ✓. Die Schraube folgt dann dem Bohrungsmuster und es sind 6 Stück.

## 14. Prüfen

1. **Analyse → Globale Interferenz** → *Vorschau*. Erwartet sind nur diese Überschneidungen:
   - **12 × Schraube ↔ Gewindebohrung:** Das ist gewollt. Das Gewinde ist kosmetisch, deshalb überschneiden sich Kernloch Ø6,8 und Schraube Ø8.
   - **Feder ↔ Stift:** nur wenn die Öse nach Buch Ø5,8 innen hat (siehe Schritt 6).

   Alles andere ist ein Fehler in Maßen oder Abhängigkeiten.
2. **Stückliste kontrollieren:** *Werkzeuge → Stückliste* (bzw. *Info → Stückliste*). Soll:

   | Pos. | Teil | Anzahl |
   |---|---|---|
   | 1 | Antriebsnabe | 1 |
   | 2 | Abtriebsnabe | 1 |
   | 3 | Gehäuse | 1 |
   | 4 | Deckel | 1 |
   | 5 | Fliehgewicht | 2 (je 1 Gewicht 5.1 und 1 Belag 5.2) |
   | 6 | Scheibe | 4 |
   | 7 | Zugfeder | 4 |
   | 8 | Sicherungsscheibe | 8 |
   | 9 | Zylinderstift | 4 |
   | 10 | Zylinderschraube | 12 |
   | 11 | Rillenkugellager | 2 |
   | 12 | Filzring | 1 |
   | | **gesamt** | **43 Einzelteile** |
3. **Speichern:** *Datei → Speichern*. Gib die ganze Ordner-Struktur (asm + alle prt) ab, nicht nur die .asm.

## Typische Fehler

| Meldung / Problem | Ursache | Lösung |
|---|---|---|
| „Teilweise platziert“ | Ein Freiheitsgrad ist offen, meist die Drehung um die Achse. | Eine Winkel- oder Ebenen-Abhängigkeit ergänzen (z. B. FRONT ↔ FRONT). |
| Teil springt auf die falsche Seite | Die Flächenrichtung ist entgegengesetzt. | Bei der Abhängigkeit **Umkehren** klicken. |
| Baugruppe findet Teile nicht | Dateien wurden außerhalb von Creo umbenannt oder verschoben. | Arbeitsverzeichnis prüfen, nur in Creo umbenennen. |
| Fliehgewicht steht nach außen | Der Winkel wurde in die falsche Richtung gemessen. | Winkel negativ eingeben oder Umkehren. |
| Feder lässt sich nicht einhängen | Die Feder ist ungespannt. | Schritt 6, „Flexibel machen“. |
