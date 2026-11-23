# Verbindungswege zu Creo Parametric – alle Möglichkeiten im Überblick

Stand: November 2026, Creo Parametric 12 (Schul-/Uni-Lizenz). Bewertet nach: Lizenz, Zugriff auf die laufende Sitzung,
Modellbaum, Grad der Kontrolle, Aufwand. **Fett** = in diesem MCP umgesetzt.

| # | Weg | Lizenz | Laufende Sitzung | Modellbaum | Kontrolle | Bewertung |
|---|---|---|---|---|---|---|
| 1 | **CREOSON** (JSON über HTTP → J-Link; ab Creo 9 teils OTK C++) | frei (MIT; J-Link ist bei Creo dabei) | ja | KE-Liste, Gruppen, Muster, Baugruppenstruktur | 175 Funktionen + Mapkeys | **Hauptweg** – Creo 12 ab CREOSON 3.0.0 unterstützt |
| 2 | **Mapkeys** (über CREOSON `interface.mapkey` oder VB API `RunMacro`) | frei | ja | – | jeder Menübefehl, auch KE-Erzeugung | **umgesetzt** (`creo_run_mapkey`); Rezepte müssen in Creo 12 aufgezeichnet werden, keine Rückmeldung bei Fehlern |
| 3 | **VB API** (COM `pfcls.pfcAsyncConnection`) | frei | ja | voll, inkl. Eltern/Kind (`ListParents/ListChildren`) | wie J-Link | **optional umgesetzt** (`creo_feature_relations`); einmal `vb_api_register.bat` als Admin |
| 4 | J-Link / OTK Java, eigene Java-App | J-Link frei; OTK-Pakete `wfc`/`uifc` lizenzpflichtig | ja | voll | wie VB API; Element-Trees nur mit Lizenz | nicht nötig – CREOSON ist genau so eine App |
| 5 | Creo TOOLKIT (C) / OTK C++ mit Element-Trees | **kostenpflichtig**, nicht in Schullizenzen | ja (DLL/async) | voll | maximal, inkl. Skizzen-KEs per Programm | einziger „echter“ Weg für KE-Erzeugung – Lizenz fehlt |
| 6 | Web.Link / Creo.JS (JavaScript im eingebetteten Creo-Browser) | frei | ja | teilweise | ähnlich J-Link | möglich als Brücke (Seite im Creo-Browser ↔ WebSocket), bringt aber nichts über 1–3 hinaus |
| 7 | Trail-Dateien (Aufzeichnung abspielen, auch Batch mit `-g:no_graphics`) | frei | nein (Batch) / Abspielen in Sitzung | über Info-Exporte | alles, was die Oberfläche kann | robust für feste Abläufe, aber koordinatenabhängig bei Skizzen-Klicks |
| 8 | Creo Distributed Batch | frei | nein | – | Massen-Export/Plot | nur für Serienausgaben interessant |
| 9 | Oberflächen-Automatisierung (pywinauto/AutoHotkey) | frei | ja | Bildschirm lesen | fragil | letzter Ausweg |
| 10 | Windchill REST (OData) | Windchill | – | Produktstruktur im PDM | PDM-Daten | nur mit Windchill (Schule meist nicht) |
| 11 | Neutralformate (STEP AP242 lesen/schreiben) | frei | nein | Baugruppenstruktur aus STEP | Geometrie | **umgesetzt** als Import/Export; Ausweg für „Modell aus PDF“ |

## Warum Skizzen-KEs nicht direkt per API?

Die freien Schnittstellen (J-Link, VB API, Web.Link, CREOSON) können KEs unterdrücken, fortsetzen, löschen,
umordnen, umbenennen, Maße/Parameter/Relationen ändern, UDFs und Komponenten platzieren – aber **keine
Extrusion/Drehung mit Skizze anlegen**. Das geht nur über Element-Trees (Toolkit bzw. lizenzpflichtiges OTK).
Für das Ziel „ganze Modelle aus einer PDF“ bleiben deshalb:

1. **Mapkey-Rezepte** (nativ, mit KE-Verlauf): Befehlsfolgen werden in Creo 12 einmal aufgezeichnet
   (Datei → Optionen → Mapkeys), dann parametrisiert und über `creo_run_mapkey` abgespielt. Danach prüft
   `creo_get_model_tree`, ob das KE entstanden ist; Maße werden über `creo_set_dimension` exakt gesetzt.
   Diese Rezepte entwickle ich live auf deinem PC, weil Dialognamen versionsabhängig sind.
2. **STEP-Import** (voll automatisch, ohne KE-Verlauf): Geometrie außerhalb von Creo erzeugen
   (z. B. mit CadQuery wie in `Teil_A/Skripte`), mit `creo_import_geometry` importieren, danach Zeichnung in Creo.
3. **Vorlagen mit Parametern**: ein einmal von Hand gebautes, parametrisches Teil wird über Maße/Parameter/
   Familientabellen variiert.

## Bestehende Creo-MCP-Projekte (Stand Nov. 2026)

- [adamclark64/creo-mcp](https://github.com/adamclark64/creo-mcp) – 169 Werkzeuge 1:1 über creopyson, kein Modellbaum-Werkzeug.
- [anandtanuku/creo-mcp-bridge](https://github.com/anandtanuku/creo-mcp-bridge) – eigene Java-Brücke (J-Link), 17 Werkzeuge.
- [EdwardNguyen2854/dnk-mcp-creo](https://glama.ai/mcp/servers/EdwardNguyen2854/dnk-mcp-creo) – TypeScript + C++ (Object TOOLKIT), Lizenz nötig.
- weitere: JaikenWong/creo_mcp_server (OTK Java), yujiajunn/creo-mcp, rweisssieker-xp/GBL-CREO-WINDCHILL-MCP.

Unterschied dieses Projekts: echter Modellbaum (Komponenten + KEs + Gruppen/Muster), spezifikationsgeprüfter
Zugriff auf alle 175 CREOSON-Funktionen, Sicherheitsschicht, Diagnose, VB-API-Ergänzung, simuliertes Creo für Tests
und Demo, deutsche Doku und Windows-Installationsskript.

## Quellen

- CREOSON Releases (3.0.0: Creo 12 / Java 21; 3.0.2: Creo 13 / Java 25): https://github.com/SimplifiedLogic/creoson/releases
- CREOSON-Quellcode (Fehlertexte, `set_creo_version`, Feature-Listen): https://github.com/SimplifiedLogic/creoson
- PTC VB API Hilfe (IpfcAsyncConnection, IpfcFeature, IpfcBaseSession): https://support.ptc.com/help/creo_toolkit/vbapi_pma/r11.0/usascii/creo_toolkit.html
- OTK-Java-Lizenzierung (wfc/uifc lizenzpflichtig): https://www.ptc.com/en/support/article/CS190307
