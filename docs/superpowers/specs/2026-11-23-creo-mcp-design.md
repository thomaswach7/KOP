# Design: Creo-MCP-Server (Creo Parametric 12, volle Kontrolle inkl. Modellbaum)

Stand: 2026-11-23 · Ordner im Repo: `Creo_MCP/`

## Absicht und Warum

Claude (Claude Desktop / Claude Code) soll PTC Creo Parametric 12 auf dem PC des Nutzers steuern:
Modelle öffnen/ändern/prüfen, den Modellbaum ("Stammbaum") lesen und – Hauptziel des Nutzers –
**ganze Modelle aus einer PDF-Vorlage aufbauen und danach Zeichnungen erstellen**.
Kontext: Schulprojekt (Fliehkraftkupplung), Creo 12 mit Schul-/Uni-Lizenz, deutsche Oberfläche.

## Ziele

1. MCP-Server (stdio), der sich mit einer laufenden Creo-12-Sitzung verbindet.
2. Lesender Vollzugriff: Modellbaum (Baugruppe + KEs + Gruppen/Muster), Parameter, Maße, Relationen,
   Masseneigenschaften (Volumen für Soll/Ist-Vergleich), Stückliste, Zeichnungsinfos.
3. Schreibender Zugriff: Öffnen, Speichern, Regenerieren, Maße/Parameter/Relationen setzen,
   KEs unterdrücken/fortsetzen/umbenennen/löschen, Komponenten einbauen, Zeichnungen anlegen
   (Ansichten, Maßstab, Blätter), Export (PDF, DXF, STEP, STL, Bild), Import (STEP/IGES).
4. "Volle Kontrolle": generischer Aufruf **jeder** der 175 CREOSON-Funktionen (mit Spezifikationsprüfung)
   und Ausführen von Mapkeys (jeder Menübefehl von Creo).
5. Neues Modell anlegen (aus Creo-Vorlage) und – experimentell – KEs per Mapkey-Rezepten erzeugen.
6. Diagnosewerkzeug, das auf dem PC prüft, welche Verbindungswege funktionieren.
7. Ohne Creo testbar: simulierter CREOSON-Server (Mock) + Demo-Modus.

## Nicht-Ziele

- Eigene C/C++-Toolkit-Anwendung (Toolkit-Lizenz fehlt in Schullizenzen).
- Windchill-Spezialwerkzeuge (bleiben über den generischen Aufruf erreichbar).
- Lesen von PDFs im Server – das macht das Sprachmodell selbst.

## Anti-Ziele (wäre ein Fehlschlag, selbst wenn es technisch läuft)

- Der Server führt unbemerkt Betriebssystem-Befehle aus (Mapkeys mit `@SYSTEM`) – standardmäßig gesperrt.
- Werkzeuge fluten den Kontext (riesige Bäume/Listen) – Begrenzung + Zusammenfassung.
- Stille Fehler: jede CREOSON-Fehlermeldung wird mit Lösungshinweis zurückgegeben.

## Randbedingungen

- Creo läuft nur unter Windows; Entwicklung/Tests hier unter Linux gegen den Mock.
- CREOSON 3.0.x (Creo 12: Java 21). Nach jedem Verbinden `creo.set_creo_version(12)`, sonst schlagen
  suppress/resume/delete/regenerate/assemble fehl (CREOSON-Quellcode: Versionsprüfung `>=9`).
- J-Link (frei) kann keine Extrude/Revolve-KEs direkt anlegen → nur über Mapkeys (UI-Ebene) oder UDFs.
- Python ≥ 3.10, MCP-SDK `mcp` 2.3 (`MCPServer`, nicht mehr `FastMCP`).

## Ansätze (betrachtet)

| Ansatz | Bewertung |
|---|---|
| A. CREOSON-basiert + Mapkeys + spezifikationsgetriebener Generik-Aufruf (gewählt) | frei, Creo 12 unterstützt, 175 Funktionen, gut testbar über JSON; Feature-Erzeugung nur via Mapkeys |
| B. Eigene Java-Brücke (OTK Java/J-Link async) | gleiche Grenzen wie CREOSON, aber viel mehr Eigenbau; nur sinnvoll für Eltern/Kind-Daten |
| C. VB-API (COM) als einziger Weg | nur Windows, schwer zu testen, kein Vorteil bei Feature-Erzeugung |
| D. Toolkit (C) mit Element-Trees | einziger "echter" Weg für KE-Erzeugung, aber Lizenz fehlt |
| E. Nur STEP-Import (Geometrie extern bauen) | voll automatisch, aber kein parametrischer KE-Baum |

Entscheidung: **A** als Kern, **VB-API** als optionale Ergänzung (Eltern/Kind, Makros), **E** als Ausweichweg
für "Modell aus PDF". Die Wahl der Technik hat der Nutzer an mich delegiert ("arbeite bis positives Ergebnis").

## Architektur

```
Claude ──stdio── creo_mcp.server (MCPServer) ──HTTP/JSON── CREOSON (Port 9056) ──J-Link── Creo 12
                       │                                    (Mock im Test/Demo)
                       ├── tree.py      Modellbaum (bom.get_paths + feature.list + Gruppen/Muster)
                       ├── catalog.py   175 Funktionsspezifikationen (aus CREOSON, MIT) → Prüfung/Hilfe
                       ├── safety.py    Read-only-Modus, Gefahrenliste, @SYSTEM-Sperre
                       ├── mapkeys.py   Mapkey-Bausteine/Rezepte
                       ├── vbapi.py     optional: COM pfcls (Windows)
                       └── doctor.py    Diagnose aller Wege
```

- Client: async (`httpx`), Sitzungs-ID, automatisches Neuverbinden bei ungültiger Sitzung,
  Serialisierung aller Aufrufe (Creo ist single-threaded), Timeout konfigurierbar.
- Modellbaum: Wurzel = angegebenes oder aktives Modell. Baugruppe: Komponenten-KEs werden über die
  Feature-ID (`path[-1]` aus `bom.get_paths`) mit den Unterkomponenten verknüpft. KE-Listen je Datei
  zwischengespeichert. Gruppen/Muster: Kopf-KE erkennen, Mitglieder über `list_group_features` /
  `list_pattern_features` einhängen; bei Fehler flach lassen + Warnung. Ausgabe Markdown-Baum oder JSON,
  Tiefen- und Knotenlimit.
- Konfiguration über Umgebungsvariablen (`CREOSON_URL`, `CREO_VERSION`=12, `CREO_MCP_TIMEOUT`,
  `CREO_MCP_READ_ONLY`, `CREO_MCP_ALLOW_DANGEROUS`, `CREO_MCP_ALLOW_SYSTEM_MAPKEYS`, Startskript-Pfad).
- Neues Modell: Vorlage öffnen → im Speicher umbenennen → `file.backup` ins Arbeitsverzeichnis →
  aus Speicher löschen → neu öffnen (reiner CREOSON-Weg, keine Schreibrechte in Program Files nötig).

## Werkzeuge (Auswahl, Präfix `creo_`)

Sitzung: status, connect, doctor · Dateien: list_files, open_model, new_model, save, regenerate,
close/erase, set_working_dir · **Modellbaum: get_model_tree**, list_features · KEs: suppress, resume,
delete, rename, feature_params · Parameter/Maße/Relationen: list/set · mass_properties, materials, units ·
Baugruppe: assemble_component, get_bom · Zeichnung: create_drawing, add_view, drawing_info,
scale/move/sheets, show_dimensions, notes · export, import_geometry · run_mapkey · generisch:
list_functions, describe_function, call.
Ressourcen: `creo://session`, `creo://model-tree/{file}`, `creo://functions`.
Prompts: "PDF → Creo-Modell + Zeichnung", "Modellbaum gegen Anleitung prüfen".

## Tests

Pytest gegen Mock-CREOSON (stdlib-HTTP-Server mit simuliertem Zustand: Baugruppe Fliehkraftkupplung,
Abtriebsnabe mit KEs/Gruppe/Muster). In-Memory-MCP-Client für Werkzeugtests, stdio-End-to-End-Test.
Live-Test auf dem PC des Nutzers über Remote Control, sobald freigegeben.

## Dem Umsetzer überlassen (meine Entscheidungen, korrigierbar)

- Werkzeugbeschreibungen englisch (für das Modell präziser), Doku/README deutsch.
- Paket `creo_mcp`, Ordner `Creo_MCP/`, Einstieg `python -m creo_mcp` bzw. `creo-mcp`.
- Mapkey-Rezepte für KE-Erzeugung werden erst live mit Creo 12 entwickelt (Dialognamen sind versionsabhängig).
- Standardvorlage für neue Teile `mmns_part_solid_abs`, für Baugruppen `mmns_asm_design_abs` (wie in den
  Anleitungen im Repo); Zeichnungsvorlage wird als Parameter übergeben (schul-/installationsabhängig).
- Größenlimits: Modellbaum standardmäßig max. 400 Knoten, Listen paginiert (Standard 100).

## Builder-Selbstprüfung (ohne Subagent)

Offene Punkte, die nur live klärbar sind: genaue KE-Typnamen von Gruppen-/Musterköpfen in Creo 12,
Dialognamen für Mapkeys, ob die Schullizenz J-Link/VB-API freigibt (das prüft `creo_doctor`).
