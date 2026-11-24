# Creo-MCP – Claude steuert PTC Creo Parametric 12

MCP-Server (Model Context Protocol), mit dem Claude (Claude Desktop oder Claude Code) eine laufende
**Creo-Parametric-Sitzung** auf deinem Windows-PC liest und steuert: Modellbaum („Stammbaum“), KEs, Parameter,
Maße, Relationen, Volumen, Baugruppen, Zeichnungen, Export – und über den generischen Aufruf **jede** der
175 Funktionen von CREOSON sowie beliebige Creo-Menübefehle über Mapkeys.

```
Claude ──MCP (stdio)── creo-mcp (Python) ──HTTP/JSON── CREOSON (Port 9056) ──J-Link── Creo 12
                              └─ optional: VB API (COM) für Eltern/Kind-Beziehungen der KEs
```

## Was geht – und was (noch) nicht

| Aufgabe | Status | Werkzeug |
|---|---|---|
| Modellbaum lesen (Baugruppe → Komponenten → KEs, Gruppen, Muster, Status) | ✅ | `creo_get_model_tree` |
| KEs auflisten, unterdrücken, fortsetzen, löschen, umbenennen | ✅ | `creo_list_features`, `creo_suppress_features`, … |
| Parameter, Maße, Relationen lesen/ändern, regenerieren | ✅ | `creo_set_dimension`, `creo_set_parameter`, … |
| Volumen/Masse prüfen (Soll/Ist) | ✅ | `creo_mass_properties` |
| Neues Teil/Baugruppe aus Vorlage | ✅ | `creo_new_model` |
| Komponente einbauen | ⚠️ nur Koordinatensystem→Koordinatensystem oder feste Lage | `creo_assemble_component` |
| Zeichnung anlegen, Ansichten, Blätter, Maßstab, PDF/DXF | ✅ | `creo_create_drawing`, `creo_add_drawing_view`, `creo_export` |
| STEP/IGES importieren und exportieren | ✅ (STL bietet CREOSON nicht – per aufgezeichnetem „Speichern unter“-Mapkey) | `creo_import_geometry`, `creo_export` |
| Jede CREOSON-Funktion (Familientabellen, Layer, Notizen, Windchill …) | ✅ | `creo_call` |
| Jeder Menübefehl (Mapkey) | ✅ technisch, Rezepte müssen in Creo 12 aufgezeichnet werden | `creo_run_mapkey` |
| Skizzen-KEs (Extrudieren/Drehen) **direkt** per API anlegen | ❌ nur mit kostenpflichtiger Toolkit-Lizenz – Ausweg: Mapkeys oder STEP-Import | – |
| Eltern/Kind-Beziehungen der KEs | ✅ mit VB API (Windows) | `creo_feature_relations` |

## Installation (Windows, einmalig)

Voraussetzungen: Creo Parametric 12, Python ≥ 3.10 ([python.org](https://www.python.org/downloads/), „Add python.exe to PATH“ anhaken),
Claude Desktop oder Claude Code.

1. Repo klonen oder herunterladen, dann in PowerShell im Ordner `Creo_MCP`:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\install_windows.ps1
   ```
   Das Skript
   - legt `.venv` an und installiert `creo-mcp`,
   - lädt **CREOSON 3.0.2** und prüft die SHA256-Prüfsumme,
   - legt `C:\Creoson_<Benutzername>` an (ohne Leerzeichen, nur für dich beschreibbar) und schreibt dort `setvars.bat` und `nitro_proe_remote.bat`,
   - setzt `PRO_COMM_MSG_EXE` für deinen Benutzer,
   - trägt `creo` in `%APPDATA%\Claude\claude_desktop_config.json` ein (Sicherung `.bak`).

   Am besten in einer **PowerShell als Administrator** ausführen: Dann setzt das Skript zusätzlich die Firewall-Regel für
   CREOSON und registriert die VB API (für `creo_feature_relations`).
   Optionen: `-WorkDir "D:\Schule\Creo"` (Creo-Arbeitsverzeichnis), `-CreosonDir` (ohne Leerzeichen!), `-SkipCreoson`, `-SkipClaudeConfig`, `-NoUserEnv`.
2. **CREOSON starten:** `C:\Creoson_<Benutzername>\creoson_run.bat` (Fenster offen lassen).
   Alternativ `CreosonSetup.exe` → Creo-Ordner `…\Creo 12.x\Common Files` wählen → „Start CREOSON“.
3. **Creo starten:** `C:\Creoson_<Benutzername>\nitro_proe_remote.bat`. Wichtig: Ein Creo, das ohne `PRO_COMM_MSG_EXE`
   gestartet wurde, ist für CREOSON unsichtbar („Unable to connect to Creo through J-Link“). Nach dem
   Installationsskript reicht nach einer Neuanmeldung auch der normale Creo-Start.
4. **Prüfen:** `.\.venv\Scripts\python.exe -m creo_mcp doctor` – zeigt ✅/❌ für jeden Weg und was zu tun ist.
5. **Claude Desktop** ganz beenden (auch im Infobereich) und neu starten. Frag z. B.:
   *„Zeig mir den Modellbaum des aktiven Modells.“*

**Claude Code** statt Claude Desktop:
```powershell
claude mcp add creo --scope user -e CREOSON_URL=http://localhost:9056/creoson -e CREO_VERSION=12 -- "C:\Pfad\zu\Creo_MCP\.venv\Scripts\python.exe" -m creo_mcp
```

**Optional – VB API** (für `creo_feature_relations`): einmal als Administrator
`C:\Program Files\PTC\Creo 12.x\Parametric\bin\vb_api_register.bat` ausführen; `pywin32` installiert das Skript mit.

Manuelle Konfiguration: siehe [`examples/claude_desktop_config.json`](examples/claude_desktop_config.json).

## Ohne Creo ausprobieren (Demo)

```powershell
.\.venv\Scripts\python.exe -m creo_mcp demo
```
startet den MCP-Server mit einem **simulierten Creo** (Fliehkraftkupplung aus diesem Repo: Baugruppe,
Fliehgewicht-Unterbaugruppe, Abtriebsnabe mit KEs, Muster und Gruppe). In Claude Desktop als eigener Server
`creo-demo` eintragen (Beispiel in `examples/`).

## Werkzeuge

| Bereich | Werkzeuge |
|---|---|
| Sitzung | `creo_status`, `creo_connect`, `creo_working_dir`, `creo_doctor` |
| Dateien/Modelle | `creo_list_models`, `creo_list_files`, `creo_open_model`, `creo_new_model`, `creo_save_model`, `creo_regenerate`, `creo_close_model`, `creo_rename_model`, `creo_get_model_info` |
| Modellbaum | `creo_get_model_tree`, `creo_list_features`, `creo_feature_relations` |
| KEs | `creo_suppress_features`, `creo_resume_features`, `creo_delete_features`, `creo_rename_feature` |
| Daten | `creo_list_parameters`, `creo_set_parameter`, `creo_delete_parameter`, `creo_list_dimensions`, `creo_set_dimension`, `creo_get_relations`, `creo_set_relations`, `creo_mass_properties`, `creo_set_material` |
| Baugruppe | `creo_assemble_component`, `creo_get_bom` |
| Zeichnung | `creo_create_drawing`, `creo_add_drawing_view`, `creo_get_drawing_info`, `creo_edit_drawing` |
| Austausch | `creo_export`, `creo_import_geometry` |
| Volle Kontrolle | `creo_run_mapkey`, `creo_list_functions`, `creo_describe_function`, `creo_call` |

Ressourcen: `creo://session`, `creo://model-tree/{datei}`, `creo://functions`.
Prompts: `pdf_zu_creo_modell` (PDF → Modell → Zeichnung), `modellbaum_pruefen` (Modell gegen Anleitung prüfen).

### Beispiele für Anfragen an Claude

- „Prüfe `abtriebsnabe.prt` gegen `Teil_D/Modellbaum/Anleitung_Abtriebsnabe.md`: KE-Reihenfolge, Namen und Volumen (Soll 350.370 mm³).“
- „Setze in der Abtriebsnabe die Nutbreite auf 14 mm, regeneriere und sag mir das neue Volumen.“
- „Erstelle für `abtriebsnabe.prt` eine A3-Zeichnung 1:1 mit Vorder- und Seitenansicht und exportiere sie als PDF.“
- „Benenne alle KEs der Antriebsnabe nach der Anleitung um.“
- „Welche Funktionen gibt es für Familientabellen? Lies die Tabelle von `schraube.prt`.“

## Sicherheit

| Einstellung | Wirkung |
|---|---|
| `CREO_MCP_READ_ONLY=1` | nur lesen, öffnen und exportieren; nichts am Modell ändern |
| `CREO_MCP_ALLOW_DANGEROUS=1` | erlaubt Dateien/Ordner löschen, Creo beenden, Windchill-Workspace leeren (sonst gesperrt) |
| `CREO_MCP_ALLOW_SYSTEM_MAPKEYS=1` | erlaubt Mapkeys mit `@SYSTEM` (Betriebssystem-Befehle) – sonst gesperrt |

Immer aktiv:
- `creo_connect(start_creo=true)` bzw. `connection.start_creo` startet **nur** `nitro_proe_remote.bat` aus dem in
  `CREO_START_DIR` eingetragenen Ordner – ein anderer Ordner (z. B. aus einer präparierten PDF) wird abgelehnt.
- Mapkey-Definitionen über `creo.set_config` werden genauso auf `@SYSTEM` geprüft wie direkte Mapkeys.
- Im Nur-Lesen-Modus wird auch das Verwerfen nicht angezeigter Modelle (`erase_not_displayed`) gesperrt.
- Das Installationsskript legt den CREOSON-Ordner nur für dich beschreibbar an; einen Ordner, der einem anderen Benutzer
  gehört, verwendet es nicht (Schutz auf Schul-PCs mit mehreren Konten).

Hinweis: Ein Mapkey kann andere, in deiner `config.pro` definierte Mapkeys aufrufen. Deren Inhalt prüft der Server nicht.
Mapkeys können jeden Menübefehl ausführen – gib Werkzeugaufrufe in Claude nur frei, wenn du weißt, was sie tun.

### ⚠️ CREOSON im Netzwerk absichern

CREOSON hat **kein Passwort** und lauscht auf **allen** Netzwerkadressen (Port 9056). Jeder, der diesen Port deines PCs
erreicht (z. B. im Schulnetz), könnte Creo steuern – einschließlich Batch-Dateien starten. Deshalb:

- Fragt Windows beim ersten Start von CREOSON nach Netzwerkzugriff für Java: **nicht zulassen**.
- Besser: Firewall-Regel (das Installationsskript setzt sie automatisch, wenn es als Administrator läuft):
  ```powershell
  New-NetFirewallRule -DisplayName "CREOSON Port 9056 nur lokal" -Direction Inbound -Protocol TCP -LocalPort 9056 -Action Block
  ```
  Der MCP-Server verbindet sich über `localhost` – das blockiert die Regel nicht.
- CREOSON nur laufen lassen, solange du damit arbeitest.

## Konfiguration (Umgebungsvariablen)

| Variable | Standard | Bedeutung |
|---|---|---|
| `CREOSON_URL` | `http://localhost:9056/creoson` | Adresse von CREOSON |
| `CREO_VERSION` | `12` | wird nach jedem Verbinden an CREOSON gemeldet (nötig für Unterdrücken/Löschen/Regenerieren ab Creo 7; `0` = aus) |
| `CREO_MCP_TIMEOUT` | `120` | Sekunden pro Aufruf |
| `CREO_START_DIR` / `CREO_START_COMMAND` | – / `nitro_proe_remote.bat` | für `creo_connect(start_creo=true)` |
| `CREO_TEMPLATE_DIR` | automatisch gesucht | Ordner der Creo-Startvorlagen für `creo_new_model` |
| `CREO_DRAWING_TEMPLATE` | `a3_drawing` | Zeichnungsvorlage für `creo_create_drawing` (Creo-Standard A3) |
| `CREO_MCP_MAX_TREE_NODES` | `400` | Knotenlimit des Modellbaums |
| `CREO_MCP_LOG_LEVEL` | `WARNING` | Log-Ausgabe auf stderr |

## Fehlerbehebung

| Meldung | Ursache / Lösung |
|---|---|
| `Cannot reach CREOSON …` | CREOSON läuft nicht → `creoson_run.bat` starten; Port in `CREOSON_URL` prüfen |
| `Unable to connect to Creo through J-Link` | Creo ohne `PRO_COMM_MSG_EXE` gestartet → über `nitro_proe_remote.bat` starten |
| `more than one instance of Creo is running` | nur eine Creo-Sitzung offen lassen |
| `No session found` | CREOSON wurde neu gestartet – der Server verbindet automatisch neu |
| `XToolkitBadContext` | in Creo ist ein Dialog offen → schließen |
| Unterdrücken/Regenerieren schlägt fehl | `CREO_VERSION=12` gesetzt? (`creo_doctor`) |
| Student Edition | Die Programmierschnittstellen sind dort evtl. gesperrt – `creo_doctor` zeigt es |

## Weitere Doku

- [Verbindungswege zu Creo – Analyse aller Möglichkeiten](docs/VERBINDUNGSWEGE.md)
- Design: `../docs/superpowers/specs/2026-11-23-creo-mcp-design.md`, Plan: `../docs/superpowers/plans/2026-11-23-creo-mcp.md`

## Entwicklung

```bash
pip install -e ".[dev]"
pytest                      # 125 Tests gegen den simulierten CREOSON-Server (prüft jede Anfrage gegen die CREOSON-Spezifikation)
python -m creo_mcp mock     # nur den simulierten CREOSON-Server auf Port 9056 starten
```

Lizenz: MIT. Die mitgelieferten CREOSON-Funktionsbeschreibungen (`src/creo_mcp/specs/`) stammen aus
[CREOSON](https://github.com/SimplifiedLogic/creoson) (MIT, © Simplified Logic, Inc.).
Creo und Creo Parametric sind Marken von PTC Inc.; dieses Projekt ist nicht mit PTC verbunden.
