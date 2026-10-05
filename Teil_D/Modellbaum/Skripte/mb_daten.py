"""Modellbaum je Einzelteil (Creo Parametric 12) - Daten fuer PDF und README.
Jede KE-Zeile: (Nr, Creo-KE, Ebene / Referenz, Eingaben / Maße)."""

ALLGEMEIN = [
    "Neues Teil: Datei → Neu → Teil / Volumenkörper, Haken bei „Standardvorlage verwenden“ weg → Vorlage mmns_part_solid_abs (mm, N, s).",
    "Drehteile (Pos. 1, 2, 3, 4, 9, 12): Skizze auf FRONT. Zuerst eine Geometrie-Mittellinie auf die waagrechte Referenz legen (= Drehachse). "
    "Gezeichnet wird nur der halbe Querschnitt über der Achse. Durchmesser bemaßen: Linie → Mittellinie → nochmal Linie anklicken → mittlere Maustaste.",
    "Die x-Maße in den Skizzen zählen von der linken Stirnfläche (= Ebene RIGHT) aus.",
    "Jedes KE im Modellbaum umbenennen (Rechtsklick → Umbenennen, z. B. „Grundkörper“, „Arme“, „Passfedernut“). So kann die Lehrkraft den Aufbau sofort lesen.",
    "Freistiche DIN 509-E0,6×0,3 (Pos. 1, 2, 4) gehören in die Drehskizze – Maße und Schritte auf Seite 2.",
    "Kontrolle am Ende: Analyse → Masseneigenschaften → Volumen. Weicht dein Wert um weniger als 0,5 % vom Sollvolumen ab, stimmt das Teil (Feder: 3 %).",
    "Klappt eine Rundung nicht („Rundung konnte nicht erzeugt werden“), ist meist der Radius so groß wie die Fläche daneben. Dann den Bogen gleich in die Skizze zeichnen, wie hier bei allen R2 an den Lagerschultern.",
]

PARTS = [
 dict(key="pos1", nr="1", name="Antriebsnabe", werkstoff="EN-GJS-700-2", quelle="Zeichnung 14.2.5.2",
  ke=[
   ("1", "Drehen (Grundkörper)", "Skizze auf FRONT, Achse = Mittellinie", "Skizze 1: Bohrung Ø30, Lagersitze Ø45 (links 29 lang, rechts 16 lang), Schultern Ø51 mit Bogen R2 (in der Skizze!), Mittelteil Ø77 von 31 bis 63, Länge 81. An beiden Lagersitzen Freistich DIN 509-E0,6×0,3 (Bild F1, Seite 2): Grund Ø44,4, 2,5 lang, 15°, R0,6. Winkel 360°."),
   ("2", "Rundung", "2 Außenkanten am Ø77 (x = 31 und x = 63)", "R2"),
   ("3", "Ebene DTM1", "parallel zu RIGHT", "Versatz 47 = Mitte der Arme"),
   ("4", "Extrudieren (Arme)", "Skizze auf DTM1", "Skizze 2: zwei Arme, je 18 breit, Halbkreis R9 außen, Augenmitten 104 auseinander (je 52 von der Achse). Rechteck innen bis R30 in den Körper ziehen. Tiefe symmetrisch 17."),
   ("5", "Rundung", "4 gerade Kanten, wo die Armseiten auf den Ø77 treffen", "R9. Erst jetzt, vor dem Fuß, sonst schlägt die Rundung fehl."),
   ("6", "Extrudieren (Fuß)", "Skizze auf DTM1", "Skizze 3: je Arm Rechteck 18 breit von R30 bis Ø79 (1 mm über Ø77). Tiefe symmetrisch 20."),
   ("7", "Bohrung", "koaxial zur Achse des R9-Bogens, Platzierung auf der Armseite", "Ø8H8, Tiefe „Durch alle“. Zweiten Arm gleich (oder Spiegeln an TOP)."),
   ("8", "Extrudieren, Material entfernen (Passfedernut)", "Skizze auf RIGHT (Stirnfläche x = 0)", "Rechteck 8 breit, symmetrisch zu TOP, von der Bohrung bis 18,3 von der Achse (= Maß 33,3, t2 = 3,3). Um 90° zu den Armen versetzt. Tiefe „Durch alle“."),
  ],
  skizzen=[("pos1_s1.png", "Skizze 1 – Drehen (KE 1)"), ("pos1_s4.png", "Skizze 2 – Arme auf DTM1 (KE 4)"), ("pos1_s6.png", "Skizze 3 – Fuß auf DTM1 (KE 6)")],
  hinweise=["Reihenfolge Arme → Rundung R9 → Fuß einhalten. Wer den Fuß vorher macht, bekommt bei R9 einen Fehler.",
            "Freistiche DIN 509-E0,6×0,3 laut Zeichnung („Nicht bemaßte Freistiche“) an beiden Lagersitzen Ø45k6 – Maße und Creo-Schritte auf Seite 2 (Bild F1). Rechts gleich, nur gespiegelt.",
            "Buchfehler: „Gusstoleranz DIN 1688“ → richtig DIN 1686."]),

 dict(key="pos2", nr="2", name="Abtriebsnabe", werkstoff="EN-GJS-700-2", quelle="keine Zeichnung im Datensatz – Maße aus dem STEP-Modell",
  ke=[
   ("1", "Drehen (Grundkörper)", "Skizze auf FRONT, Achse = Mittellinie", "Skizze 1: Bohrung Ø30 (Länge 54), Nabe Ø50 (Länge 43), Flansch Ø170 (43 bis 55), Zentrierring Ø136 / Ø125 bis 62, Lagerrohr außen mit 5° Aushebeschräge bis Ø85,3 bei 72, Lagersitz Ø75 (56 bis 72), Schulter Ø70 mit Bogen R2 (in der Skizze). Freistiche DIN 509-E0,6×0,3 am Zentrierring Ø136 (Bild F2, Grund Ø135,4) und im Lagersitz Ø75 (Bild F3, Grund Ø75,6), siehe Seite 2. Winkel 360°."),
   ("2", "Rundung", "Innenecke Nabe / Flansch (x = 43, Ø50)", "R10"),
   ("3", "Rundung", "2 Innenkanten am Flansch bei x = 55 (am Ø125 und am Lagerrohr)", "R5"),
   ("4", "Rundung", "Nabe außen bei x = 0 und Flansch Ø170 bei x = 43", "R2"),
   ("5", "Fase", "Kante Ø136 bei x = 62", "1,5 × 45°"),
   ("6", "Extrudieren, Material entfernen (Passfedernut)", "Skizze auf RIGHT (Stirnfläche x = 0)", "Rechteck 8 breit, symmetrisch zu TOP, bis 18,3 von der Achse (Maß 33,3). Tiefe „Durch alle“."),
   ("7", "Bohrung (Senkung)", "Flanschfläche x = 43, Lochkreis Ø150, 0° zu FRONT", "Ø9 durchgehend, Senkung Ø15 × 8,6 tief (für ISO 4762 M8)"),
   ("8", "Muster", "Typ Achse, Kupplungsachse", "6 Stück, 60°"),
  ],
  skizzen=[("pos2_s1.png", "Skizze 1 – Drehen (KE 1)")],
  hinweise=["Für Pos. 2 gibt es im Datensatz keine Zeichnung. Die Maße habe ich aus dem STEP-Modell abgelesen. Bitte mit der Lehrkraft abklären.",
            "Freistiche: Annahme wie beim Deckel (gleiche Passflächen Ø136h6 und Ø75H7). Bilder F2/F3 (Seite 2) zeigen die Maße am Deckel – hier sitzt die Planfläche bei x = 55 bzw. x = 56.",
            "Freistich zeichnen: siehe Seite 2."]),

 dict(key="pos3", nr="3", name="Gehäuse", werkstoff="E295", quelle="Zeichnung 14.2.5.4",
  ke=[
   ("1", "Drehen (Grundkörper)", "Skizze auf FRONT, Achse = Mittellinie", "Skizze 1: Rechteck Länge 70, innen Ø136, außen Ø170. Winkel 360°. (Extrudieren eines Rings geht genauso.)"),
   ("2", "Fase", "beide Innenkanten Ø136", "1 × 45°"),
   ("3", "Bohrung (Standard, Gewinde)", "Stirnfläche x = 0, Lochkreis Ø150, 30° zu FRONT", "ISO M8 × 1,25, Gewindetiefe 20, Bohrtiefe 26 (Kernloch Ø6,8), Spitze 118°, kosmetisches Gewinde an"),
   ("4", "Muster", "Typ Achse, Gehäuseachse", "6 Stück, 60°"),
   ("5", "Ebene DTM1", "parallel zu RIGHT", "Versatz 35 = Gehäusemitte"),
   ("6", "Spiegeln", "Muster aus KE 4 an DTM1", "ergibt 6 × M8 auf der anderen Seite"),
  ],
  skizzen=[("pos3_s1.png", "Skizze 1 – Drehen (KE 1)")],
  hinweise=["Die Lage 30° zu FRONT ist frei gewählt. In der Baugruppe richtest du die Gewinde über eine Abhängigkeit „fluchtend“ auf die Bohrungen von Deckel und Abtriebsnabe aus."]),

 dict(key="pos4", nr="4", name="Deckel", werkstoff="EN-GJS-700-2", quelle="Zeichnung 14.2.5.5",
  ke=[
   ("1", "Drehen (Grundkörper)", "Skizze auf FRONT, Achse = Mittellinie", "Skizze 1: Flansch Ø170 × 12, Zentrierring Ø136 / Ø125 bis 19, Lagerrohr außen mit 5° Aushebeschräge (Ø84 bei 29), Lagersitz Ø75 (13 bis 29), Schulter Ø70 mit Bogen R2 (in der Skizze), Bohrung Ø46, Filzringnut Ø58 (Maße in Skizze 1a: 3,5 / 4 / 7,5, Flanken je 7°). Freistiche DIN 509-E0,6×0,3 am Zentrierring Ø136 (Bild F2, Grund Ø135,4) und im Lagersitz Ø75 (Bild F3, Grund Ø75,6), siehe Seite 2. Winkel 360°."),
   ("2", "Rundung", "2 Innenkanten bei x = 12 (am Ø125 und am Lagerrohr)", "R5"),
   ("3", "Rundung", "Außenkante Ø170 bei x = 0", "R2"),
   ("4", "Fase", "Kante Ø136 bei x = 19", "1,5 × 45°"),
   ("5", "Bohrung (Senkung)", "Flanschfläche x = 0, Lochkreis Ø150, 0° zu FRONT", "Ø9 durchgehend, Senkung Ø15 × 8,6 tief"),
   ("6", "Muster", "Typ Achse, Deckelachse", "6 Stück, 60°"),
  ],
  skizzen=[("pos4_s1.png", "Skizze 1 – Drehen (KE 1)"), ("pos4_s1z.png", "Skizze 1a – Einzelheit Filzringnut (gehört zu Skizze 1)")],
  hinweise=["Die Filzringnut, der Bogen R2 und die beiden Freistiche gehören in die Drehskizze. Eine eigene Rundung R2 schlägt dort fehl.",
            "Freistiche DIN 509-E0,6×0,3 laut Zeichnung am Ø136h6 und im Lagersitz Ø75H7 – Maße und Creo-Schritte auf Seite 2 (Bilder F2, F3).",
            "Gegenstücke: Gehäuse hat Fase 1 am Ø136, Lager-Außenring r = 1 → beide ≥ 0,4, liegen also plan an.",
            "Ø84 am Lagerrohr fehlt im Buch. Ich habe es aus dem Modell ergänzt."]),

 dict(key="pos51", nr="5.1", name="Gewicht (Teil des Fliehgewichts)", werkstoff="EN-GJS-700-2", quelle="Zeichnung 14.2.5.6 + STEP-Modell",
  ke=[
   ("1", "Extrudieren (Schuh)", "Skizze auf FRONT (= Mittelebene der Nut), Ursprung = Kupplungsachse", "Skizze 1: Schuh innen R51,5, außen R60, Enden R4,25 (Mittelpunkte auf R55,75 bei ±52,13° zur Senkrechten), Belagsitz R62 über 102° (±51°). Tiefe symmetrisch 54."),
   ("2", "Ebene DTM1", "parallel zu FRONT", "Versatz 9"),
   ("3", "Extrudieren (Arm)", "Skizze auf DTM1", "Skizze 2: Bogenstück innen R43, außen R60, Enden R8,5 (Mittelpunkte auf R51,5 bei ±67,5°, zusammen 135°). Tiefe 9 (von FRONT weg, bis 18)."),
   ("4", "Extrudieren, Material entfernen (Planfläche außen)", "Armfläche bei 18", "2 Kreise R9, konzentrisch zu den R8,5-Bögen, Tiefe 1"),
   ("5", "Extrudieren, Material entfernen (Planfläche innen)", "Armfläche bei 9", "2 Kreise R9, Tiefe 1. So entstehen Nutbreite 20 und Breite außen 34."),
   ("6", "Spiegeln", "KE 3 bis 5 an FRONT", "zweiter Arm"),
   ("7", "Bohrung", "koaxial zur Achse der R8,5-Bögen", "Ø8H9, Tiefe „Durch alle“, beide Augen"),
  ],
  skizzen=[("pos51_s1.png", "Skizze 1 – Schuh auf FRONT (KE 1)"), ("pos51_s3.png", "Skizze 2 – Arm auf DTM1 (KE 3)")],
  hinweise=["Die Bohrungen sitzen konzentrisch zu den Augen, damit sind sie 95,16 auseinander. Im Buch steht 95,77, das passt nicht zu R51,5 und 135°.",
            "Buch R52 / 113° ↔ STEP R51,5 / 112,5°: gebaut ist nach dem STEP-Modell."]),

 dict(key="pos52", nr="5.2", name="Belag (Teil des Fliehgewichts)", werkstoff="Reibbelag", quelle="Zeichnung 14.2.5.6 + STEP-Modell",
  ke=[
   ("1", "Extrudieren", "Skizze auf FRONT, Ursprung = Kupplungsachse", "Skizze 1: Ringsektor innen R62, außen R65, Winkel 92°, symmetrisch zur Senkrechten. Tiefe symmetrisch 54."),
   ("2", "Fase (Einlaufschräge)", "2 äußere Endkanten (R65)", "Typ D1 × D2: 1,5 radial × 5 am Umfang"),
  ],
  skizzen=[("pos52_s1.png", "Skizze 1 – Belag (KE 1)")],
  hinweise=["Pos. 5 ist eine Unterbaugruppe: Datei → Neu → Baugruppe (mmns_asm_design_abs). 5.1 mit „Standard“ einbauen, 5.2 mit Achse ↔ Achse der Bögen, FRONT ↔ FRONT und RIGHT ↔ RIGHT.",
            "In der Kupplung wird Pos. 5 zweimal eingebaut."]),

 dict(key="pos6", nr="6", name="Scheibe", werkstoff="S235JR", quelle="Zeichnung 14.2.5.7",
  ke=[
   ("1", "Extrudieren", "Skizze auf FRONT", "Skizze 1: Kreis Ø16 und Kreis Ø9 (beide im Ursprung). Tiefe 1,5."),
  ],
  skizzen=[("pos6_s1.png", "Skizze 1 – Ring (KE 1)")],
  hinweise=["Das einfachste Teil. Gut geeignet, um den Ablauf mit Vorlage, Skizze und Volumen einmal zu üben."]),

 dict(key="pos7", nr="7", name="Zugfeder", werkstoff="Federstahl (46Si7 laut Zeichnung)", quelle="Zeichnung 14.2.5.8",
  ke=[
   ("1", "Schraubenförmiges Zug-KE (Federkörper)", "Profilskizze auf FRONT: Mittellinie = Federachse", "Skizze 1: Profillinie parallel zur Achse im Abstand 3,45 (mittlerer Ø6,9), Länge 14,3. Steigung 1,1, rechtsgängig. Querschnitt: Kreis Ø1,1 am Profilanfang. Ergibt 13 anliegende Windungen."),
   ("2", "Zug-KE (Öse 1)", "Leitkurve skizziert auf FRONT", "Skizze 2: Kreisbogen R3,45, Mittelpunkt auf der Achse 3 mm vor dem Drahtende, Öffnung 2 mm. Querschnitt Kreis Ø1,1."),
   ("3", "Ebene DTM1", "parallel zu RIGHT", "genau in der Mitte des Federkörpers"),
   ("4", "Spiegeln", "Öse aus KE 2 an DTM1", "Öse 2"),
  ],
  skizzen=[("pos7_s1.png", "Skizze 1 – Profil Zug-KE (KE 1)"), ("pos7_s2.png", "Skizze 2 – Öse (KE 2)")],
  hinweise=["Gebaut ist die Feder ungespannt nach Zeichnung. In der Baugruppe ist sie gespannt (Ösenabstand 38,8). Dafür die gespannte STEP-Datei nehmen oder die Steigung als flexibles Maß freigeben.",
            "Buchfehler: Die Öse hat außen Ø8, innen also nur Ø5,8. Der Einstich im Stift hat aber Ø6,8, deshalb passt die Feder nicht. Bei der Lehrkraft nachfragen.",
            "Der Übergang von der Windung zur Öse ist hier nur angenähert. Für Zeichnung und Baugruppe reicht das."]),

 dict(key="pos9", nr="9", name="Zylinderstift", werkstoff="C45E", quelle="Zeichnung 14.2.5.9",
  ke=[
   ("1", "Drehen (Grundkörper)", "Skizze auf FRONT, Achse = Mittellinie", "Skizze 1: Rechteck Ø8 × 50. Winkel 360°."),
   ("2", "Drehen, Material entfernen (Nut)", "Skizze auf FRONT", "Skizze 2: Rechteck 0,94 breit, 7 vom linken Ende, bis Ø7 (für die Sicherungsscheibe)"),
   ("3", "Drehen, Material entfernen (Einstich)", "Skizze auf FRONT", "Skizze 3: Halbkreis R0,6, Mittelpunkt auf der Mantellinie, 3 vom Ende (für die Federöse)"),
   ("4", "Ebene DTM1", "parallel zu RIGHT", "Versatz 25 = Stiftmitte"),
   ("5", "Spiegeln", "KE 2 und 3 an DTM1", "ergibt Nut und Einstich auf der anderen Seite (Nutabstand 36)"),
  ],
  skizzen=[("pos9_s1.png", "Skizze 1 – Drehen (KE 1)"), ("pos9_s2.png", "Skizze 2 – Nut (KE 2)"), ("pos9_s4.png", "Skizze 3 – Einstich (KE 3)")],
  hinweise=["Durch das Spiegeln bleibt der Nutabstand 36 +0,3 automatisch symmetrisch."]),

 dict(key="pos12", nr="12", name="Filzring DIN 5419 – 45", werkstoff="Filz", quelle="Norm DIN 5419 / Nut im Deckel",
  ke=[
   ("1", "Drehen", "Skizze auf FRONT, Achse = Mittellinie", "Skizze 1: innen Ø45, Absatz Ø46, Trapez bis Ø58, außen 4 breit, Flanken je 7° (genau wie die Nut im Deckel). Winkel 360°."),
  ],
  skizzen=[("pos12_s1.png", "Skizze 1 – Drehen (KE 1)")],
  hinweise=["Der Filzring ist ein Normteil. Im Querschnitt entspricht er genau der Deckelnut, deshalb kannst du die Maße aus Pos. 4 übernehmen."]),
]

NORMTEILE = [
 ("8", "Sicherungsscheibe DIN 6799 – 7", "Normteil. STEP aus Teil_A/CAD/Einzelteile_alle/ einbauen oder vom Hersteller bzw. aus TraceParts laden. Selbst modellieren ist nicht verlangt."),
 ("10", "Zylinderschraube ISO 4762 – M8 × 20", "In der Baugruppe: Register „Intelligent Fastener“ → Schraube ISO 4762 M8 × 20 auf die Senkbohrung setzen. Creo setzt sie dann auf alle Musterbohrungen. Ohne Lizenz die STEP-Datei verwenden."),
 ("11", "Rillenkugellager 6009-2Z", "Herstellermodell laden (z. B. SKF oder Schaeffler, STEP) oder die STEP-Datei aus dem Repo. Für die Baugruppe reichen die Hauptmaße d 45 / D 75 / B 16."),
]

FREISTICH = dict(
 titel="Freistich DIN 509 – E 0,6 × 0,3 (Pos. 1, 2, 4)",
 norm=[("r (Radius)", "0,6 ±0,1"), ("t1 (Tiefe)", "0,3 +0,1"), ("f (Breite)", "2,5 +0,2"), ("Auslaufwinkel", "15°"),
       ("gilt für d", "über 18 bis 80 (übliche Beanspruchung)"), ("Mindestfase Gegenstück a", "0,4")],
 quelle="DIN 509 / DIN EN ISO 18388, Tabelle 1 (im Roloff/Matek-Tabellenbuch: „Freistiche nach DIN 509“). Bitte die Werte in deinem RM nachschlagen und vergleichen.",
 wo=[("F1", "Pos. 1 Antriebsnabe", "Lagersitz Ø45k6 an der Schulter x = 29 (rechts gespiegelt an x = 65)", "Grund Ø44,4"),
     ("F2", "Pos. 4 Deckel / Pos. 2 Abtriebsnabe", "Zentrierring Ø136h6 an der Flanschfläche (x = 12 bzw. 55)", "Grund Ø135,4"),
     ("F3", "Pos. 4 Deckel / Pos. 2 Abtriebsnabe", "Lagersitz Ø75H7 an der Schulter (x = 13 bzw. 56)", "Grund Ø75,6")],
 schritte=[
  "Den Freistich zeichnest du in die Drehskizze (KE 1). Ein eigenes Drehen-KE „Material entfernen“ geht nicht sauber, weil der Radius R0,6 laut Norm etwas über den Durchmesser hinausragt.",
  "Die Zylinderlinie (z. B. Ø45) 2,5 mm vor der Planfläche enden lassen (Maß 2,5 von der Planfläche).",
  "Eine schräge Linie bis zum Einstichgrund zeichnen, Winkel 15° zur Achse bemaßen.",
  "Den Einstichgrund waagrecht bis an die Planfläche zeichnen und als Durchmesser bemaßen (Ø44,4 / Ø135,4 / Ø75,6).",
  "Register Skizze → Verrundung → „Kreisförmig getrimmt“ → Einstichgrund anklicken → Planfläche anklicken → Radius R0,6 eintragen.",
  "Prüfen: keine roten Endpunkte, alle Maße stark. Die Tiefe 0,3 ergibt sich aus den Durchmessern (45 − 44,4 = 0,6 → 0,3 je Seite).",
  "In der Zeichnung reicht der Hinweis „Nicht bemaßte Freistiche DIN 509-E0,6×0,3“ (vereinfachte Angabe nach Norm).",
 ],
 bilder=[("fr_welle.png", "Bild F1 – Welle Ø45k6 (Pos. 1), M 12:1"), ("fr_bund.png", "Bild F2 – Zentrierring Ø136h6 (Pos. 4/2), M 12:1"),
         ("fr_bohrung.png", "Bild F3 – Lagersitz-Bohrung Ø75H7 (Pos. 4/2), M 12:1")],
)
