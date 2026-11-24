# Abtriebsnabe – Mapkeys aufnehmen (für den Creo-MCP)

Ziel: für jedes der 8 KEs aus [Anleitung_Abtriebsnabe.md](Anleitung_Abtriebsnabe.md) einen Mapkey `ke1` … `ke8`.
Danach baut Claude mit diesen Mapkeys ein **neues** Teil und prüft nach jedem KE das Volumen.

**Warum Mapkeys?** Die kostenlose Creo-Schnittstelle (CREOSON/J-Link) kann keine Skizzen-KEs anlegen.
Ein Mapkey spielt deine Klicks und Eingaben in Creo einfach noch einmal ab.

## Vorbereitung (einmal)

1. **Im laufenden Creo aufnehmen** – dem, das über `C:\Creoson_User\nitro_proe_remote.bat` gestartet wurde
   (Arbeitsverzeichnis `Dokumente\Creo`). Nicht über das HTL-Desktopsymbol neu starten.
   Ist Creo zu: erst `C:\Creoson_User\creoson_run.bat`, dann `nitro_proe_remote.bat`.
2. **Neues Teil mit der HTL-Vorlage:** Datei → Neu → Teil → Name `nabe_aufnahme` → Haken
   „Standardvorlage verwenden“ weg → OK → **Durchsuchen** →
   `C:\PTC\admCreo12HTL\bibliothek\Vorlagen\standard_part.prt` → OK.
   - ⚠ Nicht `mmns_part_solid_abs`: Der fehlen die Achse A_X und die Ebenen RECHTS/OBEN/VORNE.
   - Kontrolle im Modellbaum: BASIS, RECHTS, OBEN, VORNE, A_X, A_Y, A_Z.
3. Creo-Fenster **maximiert** lassen.

## Pro KE einen Mapkey (8 ×)

1. **Strg + D** (Standardausrichtung) – vor jeder Aufnahme.
2. Mapkey-Dialog öffnen: Datei → Optionen → **Mapkeys-Einstellungen** → **Neu**
   (oder oben in der Befehlssuche „Mapkey“ eingeben).
3. Tastenfolge **`ke1`** (dann `ke2` … `ke8`), Name z. B. „KE1 Drehen“ → **Aufzeichnen**.
4. Das KE genau nach der Anleitung modellieren, bis zum ✔.
5. **Stopp** → OK.
6. Erst jetzt prüfen: Analyse → Masseneigenschaften → Volumen = Wert aus der Tabelle (nicht mit aufnehmen).

| Mapkey | KE | Volumen danach |
|---|---|---|
| ke1 | Drehen (mit Freistichen F2/F3) | 356.379 mm³ |
| ke2 | Rundung R10 | 360.051 mm³ |
| ke3 | Rundung 2 × R5 | 363.355 mm³ |
| ke4 | Rundung 2 × R2 | 362.766 mm³ |
| ke5 | Kantenfase 1,5 × 45° | 362.289 mm³ |
| ke6 | Profil Passfedernut | 360.786 mm³ |
| ke7 | Bohrung Ø9 mit Stirnsenkung | 359.050 mm³ |
| ke8 | Muster 6 × 60° | 350.370 mm³ |

## Regeln, damit das Abspielen klappt

- **Ebenen, Achsen und KEs im Modellbaum anklicken**, nicht im Grafikfenster: VORNE, RECHTS, OBEN, A_X,
  die Bohrung für das Muster.
- **Alle Maße eintippen** (Doppelklick aufs Maß → Wert → Enter). Nicht ziehen.
- **Während der Aufnahme nicht drehen, zoomen oder verschieben.** Kanten für Rundungen und Fase im
  Grafikfenster anklicken – aus der Standardausrichtung (Strg + D vorher).
- **Vertippt?** Stopp → das KE löschen → den Mapkey neu aufnehmen (gleiche Tastenfolge, alten ersetzen).
  Fehler und Rückgängig werden sonst mit abgespielt.
- Nicht speichern (Strg + S) und nichts umbenennen, solange aufgenommen wird.

## Zum Schluss

1. Im Mapkey-Dialog **Speichern** → in `C:\Users\User\Documents\Creo\config.pro`.
2. Claude sagen: **„Mapkeys sind aufgenommen.“** Claude startet dann:

   ```powershell
   Creo_MCP\.venv\Scripts\python.exe Teil_D\Modellbaum\Skripte\abtriebsnabe_mapkeys.py
   ```

   Das Skript legt `pos02_abtriebsnabe.prt` aus der HTL-Vorlage an, spielt `ke1` … `ke8` ab und bricht beim ersten
   KE ab, dessen Volumen mehr als 0,1 % von der Tabelle abweicht. Weiter ab diesem KE: `--ab N`.

## Merken

- Vorlage: **standard_part.prt** (HTL), nicht mmns_part_solid_abs.
- Vor jeder Aufnahme **Strg + D**, während der Aufnahme **nicht drehen**.
- Bezüge **im Modellbaum** anklicken, Maße **eintippen**.
