# KerfQuote

Angebotskalkulation für Laser-, Plasma- und Wasserstrahlzuschnitte direkt aus der DXF-Datei.
Die App läuft vollständig im Browser: kein Server, keine Datenbank, keine laufenden Kosten außer dem Hosting statischer Dateien.

- **Zielkunde:** Lohnfertiger (Blechbearbeitung, Zuschnitt), die Anfragen heute von Hand kalkulieren.
- **Nutzen:** DXF hineinziehen → Schnittlänge, Einstiche, Fläche, Gewicht und Preis mit eigenen Maschinensätzen → Angebot als PDF.
- **Geschäftsmodell:** kostenlose Version als Einstieg, Pro-Jahreslizenz per Lizenzschlüssel.

## Ehrliche Einordnung: der Weg zu 1 Mio. US-Dollar

Keine Software garantiert Umsatz. Dieses Repository ist ein fertiges, getestetes Produkt – das Geld entsteht erst durch Vertrieb. Die Rechnung:

| Annahme | Wert |
|---|---|
| Pro-Lizenz | 468 € bzw. 540 $ pro Jahr (39 € / 45 $ pro Monat) |
| Nötig für 1 Mio. $ Gesamtumsatz | rund 1.900 Lizenzjahre |
| Beispiel A | 380 zahlende Betriebe über 5 Jahre |
| Beispiel B | 630 zahlende Betriebe über 3 Jahre |
| Mit zweiter Preisstufe (z. B. 149 $/Monat, siehe Roadmap) | rund 560 Lizenzjahre |

Einordnung der Chancen und Risiken:

- **Der Markt existiert und zahlt bereits.** Es gibt etablierte Wettbewerber (z. B. CutQuote, SecturaFAB, Tempus Tools, SheetDXF, das WooCommerce-Plugin „Quote & Cut“ sowie deutschsprachige Kalkulationsprogramme). Das beweist Zahlungsbereitschaft, heißt aber auch: KerfQuote muss sich abgrenzen.
- **Abgrenzung:** keine Installation, kein Upload vertraulicher Kundenzeichnungen, sofort nutzbar, niedriger Preis, Deutsch und Englisch.
- **Größtes Risiko:** Reichweite. Ohne aktive Kundengewinnung (siehe 90-Tage-Plan) passiert nichts.
- **Annahmen, die Sie selbst prüfen müssen:** Preis, Marktgröße im DACH-Raum und Umwandlungsquote von Free zu Pro. Alle drei sind Schätzungen, keine Messwerte.

## Schnellstart

```bash
cd kerfquote
node tools/serve.mjs          # http://localhost:8080/  (App unter /app/)
node --test                   # Logik-Tests, keine Abhängigkeiten
```

Die App nutzt ES-Module und lässt sich deshalb nicht per Doppelklick (`file://`) öffnen – immer über einen Webserver.

## Pflichtschritte vor der Veröffentlichung

Diese Punkte kann nur der Betreiber erledigen. Ohne sie darf bzw. kann die Seite nicht verkaufen:

1. **Impressum und Datenschutz ausfüllen.** `impressum.html` und `datenschutz.html` sind Vorlagen mit rot markierten Platzhaltern. Im DACH-Raum besteht Impressumspflicht; die Texte vor dem Start rechtlich prüfen lassen. Für englischsprachige Märkte zusätzlich englische Fassungen ergänzen.
2. **Gewerbe und Steuern klären** (Gewerbeanmeldung, Umsatzsteuer bei Verkäufen ins Ausland). Am einfachsten über einen Zahlungsanbieter, der als „Merchant of Record“ die Umsatzsteuer abführt (z. B. Lemon Squeezy oder Paddle).
3. **Privaten Lizenzschlüssel sichern.** Er liegt bewusst außerhalb des Website-Ordners unter `~/.kerfquote/license-private-key.json` (anderer Ort: Umgebungsvariable `KERFQUOTE_PRIVATE_KEY`), damit er nie versehentlich mit hochgeladen wird. Wer ihn besitzt, kann Lizenzen ausstellen – also nie ins Repository oder auf die Website legen und ein Backup anlegen. Auf einem neuen Rechner die gesicherte Datei an diesen Ort kopieren. Geht der Schlüssel verloren, erzeugt `node tools/license.mjs keygen --force` ein neues Paar; das macht alle bisher verkauften Lizenzen ungültig, also nur vor dem ersten Verkauf.
4. **Zahlungslink eintragen:** `checkoutUrl` in `src/config.js` (muss mit `https://` beginnen), danach `node tools/build-landing.mjs`.
5. **Domain eintragen:** `SITE_URL` in `tools/build-landing.mjs` setzen und neu erzeugen. Erst dann entstehen `canonical`-/`hreflang`-Angaben, Vorschaubild-Tags und `sitemap.xml`.
6. **Namen prüfen.** Eine Websuche fand kein Produkt namens „KerfQuote“; das ersetzt keine Markenrecherche (DPMA, EUIPO, USPTO) und keine Domainprüfung.
7. **Materialwerte prüfen.** Die mitgelieferten Vorschübe, Einstechzeiten und Preise sind plausible Startwerte für einen 4-kW-Faserlaser, keine Herstellerangaben.

## Veröffentlichen

Der Ordner `kerfquote/` ist die fertige Website (kein Build-Schritt nötig). Empfehlung: in ein eigenes Repository verschieben, damit Produkt und Studienunterlagen getrennt sind.

- **Netlify / Cloudflare Pages:** Repository verbinden, als Basis- bzw. Ausgabeverzeichnis `kerfquote` angeben, Build-Befehl leer lassen.
- **GitHub Pages:** eigenes Repository mit dem Inhalt von `kerfquote/` im Wurzelverzeichnis, Pages auf den Hauptzweig stellen.

Alle Pfade sind relativ, die Seite funktioniert auch in einem Unterverzeichnis. Nicht ausliefern müssen Sie `tests/`, `tools/` und `package.json`; sie schaden aber nicht.

## Lizenzen verkaufen

```bash
node tools/license.mjs issue --name "Blechwerk Muster GmbH" --months 12
node tools/license.mjs verify <Lizenzschlüssel>
```

Ablauf am Anfang von Hand: Kunde bezahlt über den Zahlungslink → Schlüssel ausstellen → per E-Mail senden → Kunde fügt ihn in der App unter „Lizenz“ ein. Die App prüft die Signatur mit dem öffentlichen Schlüssel aus `src/license-public-key.js`; ein Server ist nicht nötig. Ab etwa 20 Kunden lohnt sich die Automatisierung (Webhook des Zahlungsanbieters ruft `issueLicense` in einer kleinen Serverfunktion auf).

**Grenze dieses Verfahrens:** Die Prüfung läuft im Browser des Kunden. Wer den Quelltext verändert, kann sie umgehen. Für Firmenkunden ist das in der Praxis ausreichend, technisch dicht ist es nicht.

| | Free | Pro |
|---|---|---|
| DXF-Analyse, Kalkulation mit eigenen Sätzen | ✓ | ✓ |
| Positionen je Angebot | 2 | unbegrenzt |
| Angebot | mit KerfQuote-Hinweis | eigenes Logo, ohne Hinweis |
| CSV-Export | – | ✓ |

Preise und Texte der Startseite stehen in `tools/build-landing.mjs` (`PRICING`, `TEXT`), die Free-Grenze in `src/license.js` (`FREE_LIMITS`).

## Rechenmodell

```
Material   = (kleinstes umschließendes Rechteck + Stegzugabe) × Dicke × Dichte × Preis je kg
Schneiden  = (Schnittlänge ÷ Vorschub + Einstiche × Einstechzeit) × Maschinenstundensatz
Rüsten     = Rüstkosten je Position ÷ Menge
Stückpreis = (Material + Schneiden + Rüsten + Biegen + Zusatz) × (1 + Zuschlag)
Angebot    = Summe der Positionen, ggf. Mindermengenzuschlag bis zum Mindestauftragswert, + MwSt.
```

Bekannte Grenzen:

- Keine Schachtelung (Nesting) mehrerer Teile; der Materialansatz über das Rechteck ist vorsichtig gerechnet.
- Nur ASCII-DXF. Binäres DXF und DWG werden mit einer klaren Meldung abgelehnt.
- Splines, die nur über Stützpunkte definiert sind, werden als Polygonzug angenähert (mit Hinweis in der App).
- Überlappende, aber nicht deckungsgleiche Linien werden nicht als Duplikat erkannt.
- Enthält eine Datei mehrere Teile, gilt der Preis für alle zusammen als ein Stück (mit Hinweis).
- Das Angebot lebt im geöffneten Tab; nach dem Neuladen sind die Positionen weg. Einstellungen und Lizenz bleiben gespeichert.

## Tests

```bash
node --test                          # Logik: Parser, Geometrie, Kalkulation, Lizenz, Formate
node --test tests/e2e/app.e2e.mjs    # App im echten Browser (benötigt Playwright)
node --test tests/e2e/site.e2e.mjs   # Startseiten, Links, Barrierefreiheit (axe-core optional)
```

Die Geometrie wird gegen eine zweite, unabhängige Implementierung geprüft: `tools/make-samples.py` erzeugt die Beispiel-Dateien mit der Python-Bibliothek ezdxf und schreibt deren Referenzwerte nach `tests/reference.json`. Zusätzlich sind die einfachen Teile analytisch nachgerechnet. Die Browser-Tests vergleichen jeden angezeigten Preis mit dem Rechenmodell.

## Aufbau

```
index.html, en/index.html   Startseiten (erzeugt von tools/build-landing.mjs)
app/index.html              die Anwendung
src/dxf/                    DXF lesen (parse), in Linien/Bögen umwandeln (flatten), dekodieren
src/geom/analyze.js         Konturen verketten, Fläche, Einstiche, Abmessungen
src/cost/                   Rechenmodell, Standardwerte, Prüfung der Einstellungen
src/license.js              Lizenzprüfung (ECDSA P-256, Web Crypto)
src/ui/                     Oberfläche: App, Einstellungen, Angebotsdokument, CSV
tools/                      Lizenzwerkzeug, Entwicklungsserver, Startseiten-Generator
samples/                    Beispiel- und Testdateien
```

## 90-Tage-Plan

1. **Woche 1–2 – prüfen, bevor Sie investieren:** 20 Lohnfertiger anrufen oder besuchen, die App mit einer echten Anfrage des Betriebs vorführen. Ziel: fünf Betriebe, die sagen, wofür sie zahlen würden. Erst danach Domain, Gewerbe und Zahlungsanbieter einrichten.
2. **Woche 3–4 – Start:** Pflichtschritte oben erledigen, Seite veröffentlichen, die Materialtabellen mit zwei Pilotbetrieben kalibrieren.
3. **Woche 5–8 – erste zahlende Kunden:** Direktansprache (Telefon, E-Mail, LinkedIn) von Betrieben im Umkreis; Einträge in Branchenverzeichnissen und Softwarelisten; ein Fachartikel „Laserschneiden kalkulieren“ mit Rechenbeispiel als Suchmaschinen-Einstieg.
4. **Woche 9–12 – auswerten:** Wie viele Free-Nutzer, wie viele Käufe, welcher Einwand kommt am häufigsten? Preis und Free-Grenze danach anpassen.

## Roadmap mit dem größten Umsatzhebel

1. **Kundenportal** (zweite Preisstufe): Der Betrieb bindet einen Rechner auf seiner Website ein, Endkunden laden DXF hoch und erhalten sofort einen Preis. Braucht einen Server, damit die Kalkulationssätze geheim bleiben.
2. **Automatische Lizenzvergabe** per Webhook des Zahlungsanbieters.
3. **Angebote speichern** und wieder öffnen; Positionen in mehreren Mengen anbieten.
4. **Gravur-/Markierlayer** mit eigenem Vorschub; Zuschläge für Eilaufträge.
5. **DWG- und STEP-Import** (STEP mit Abwicklung ist deutlich aufwendiger).
