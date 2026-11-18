import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseDxf } from '../src/dxf/parse.js';
import { flatten } from '../src/dxf/flatten.js';
import { decodeDxfBytes } from '../src/dxf/decode.js';
import { analyze, guessIgnoredLayers } from '../src/geom/analyze.js';
import { previewData } from '../src/ui/preview-data.js';
import { quoteCsv, csvCell } from '../src/ui/csv.js';
import { STRINGS, createI18n } from '../src/i18n.js';
import { e, doc } from './helpers.mjs';

const BOM = String.fromCharCode(0xfeff);
const run = (text, opts) => analyze(flatten(parseDxf(text)).prims, opts);

// --- Datei-Dekodierung ---------------------------------------------------------------------

test('decodeDxfBytes: UTF-8 bleibt UTF-8', () => {
  const bytes = new TextEncoder().encode('0\nSECTION\n8\nBemaßung\n');
  assert.equal(decodeDxfBytes(bytes.buffer), '0\nSECTION\n8\nBemaßung\n');
});

test('decodeDxfBytes: ältere ANSI-Dateien (Windows-1252) werden mit Umlauten gelesen', () => {
  const bytes = Uint8Array.from([0x38, 0x0a, 0x47, 0x72, 0xf6, 0xdf, 0x65, 0x0a]); // "8\nGröße\n"
  assert.equal(decodeDxfBytes(bytes.buffer), '8\nGröße\n');
});

// --- Layer-Vorauswahl ----------------------------------------------------------------------

test('guessIgnoredLayers: Bemaßungs-, Text- und Hilfslayer werden vorab abgewählt', () => {
  const names = ['0', 'KONTUR', 'BEMASSUNG', 'Bemaßung', 'Defpoints', 'DIM', 'Dimensions', 'TEXT', 'HILFSLINIE',
    'Mittellinien', 'CENTER', 'Schriftfeld', 'Rahmen', 'AUSSEN', 'Gravur', 'Biegelinie', 'BEND'];
  assert.deepEqual(guessIgnoredLayers(names).sort(), ['BEMASSUNG', 'BEND', 'Bemaßung', 'Biegelinie', 'CENTER',
    'DIM', 'Defpoints', 'Dimensions', 'Gravur', 'HILFSLINIE', 'Mittellinien', 'Rahmen', 'Schriftfeld', 'TEXT'].sort());
});

// --- SVG-Vorschau ---------------------------------------------------------------------------

test('previewData: Y-Achse wird gespiegelt, geschlossene Kontur endet mit Z', () => {
  const a = run(doc(e('LWPOLYLINE', 90, 3, 70, 1, 10, 0, 20, 0, 10, 10, 20, 0, 10, 10, 20, 5)));
  const p = previewData(a);
  assert.equal(p.outer, 'M0 0L10 0L10 -5L0 0Z');
  assert.equal(p.inner, '');
  assert.equal(p.open, '');
  const [x, y, w, h] = p.viewBox;
  assert.ok(x < 0 && y < -5 && w > 10 && h > 5, 'viewBox mit Rand um das Teil');
});

test('previewData: Vollkreis wird in zwei Halbbögen zerlegt (SVG kann keinen Bogen mit Start = Ende)', () => {
  const a = run(doc(e('CIRCLE', 10, 0, 20, 0, 40, 5)));
  assert.equal(previewData(a).outer, 'M5 0A5 5 0 0 0 -5 0A5 5 0 0 0 5 0Z');
});

test('previewData: Bogenrichtung – CCW in der Zeichnung bleibt auf dem Bildschirm CCW (sweep 0)', () => {
  const a = run(doc(e('ARC', 10, 0, 20, 0, 40, 10, 50, 0, 51, 90)));
  const p = previewData(a);
  assert.equal(p.open, 'M10 0A10 10 0 0 0 0 -10');
  assert.equal(p.gaps.length, 2);
});

test('previewData: großer Bogen (> 180°) setzt das large-arc-Flag', () => {
  const a = run(doc(e('ARC', 10, 0, 20, 0, 40, 10, 50, 0, 51, 270)));
  assert.equal(previewData(a).open, 'M10 0A10 10 0 1 0 0 10');
});

test('previewData: Innenkonturen getrennt, Füllpfad enthält alle geschlossenen Konturen', () => {
  const a = run(doc(e('CIRCLE', 10, 0, 20, 0, 40, 10) + e('CIRCLE', 10, 0, 20, 0, 40, 2)));
  const p = previewData(a);
  assert.ok(p.outer.startsWith('M10 0'));
  assert.ok(p.inner.startsWith('M2 0'));
  assert.equal(p.fill, p.outer + p.inner);
});

test('previewData: ohne Geometrie gibt es keine Vorschau', () => {
  assert.equal(previewData(run(doc(e('TEXT', 10, 0, 20, 0)))), null);
});

// --- CSV -----------------------------------------------------------------------------------

test('csvCell: Trennzeichen, Anführungszeichen und Zeilenumbrüche werden maskiert', () => {
  assert.equal(csvCell('einfach', ';'), 'einfach');
  assert.equal(csvCell('a;b', ';'), '"a;b"');
  assert.equal(csvCell('sagt "hallo"', ';'), '"sagt ""hallo"""');
  assert.equal(csvCell('zwei\nZeilen', ','), '"zwei\nZeilen"');
});

test('csvCell: Formel-Injektion aus Dateinamen wird entschärft', () => {
  assert.equal(csvCell('=HYPERLINK("http://boese")', ';'), '"\'=HYPERLINK(""http://boese"")"');
  assert.equal(csvCell('+1', ';'), "'+1");
  assert.equal(csvCell('@SUM(A1)', ';'), "'@SUM(A1)");
  assert.equal(csvCell('-teil', ';'), "'-teil");
});

test('quoteCsv: deutsche Ausgabe mit Semikolon und Dezimalkomma, Zahlen bleiben Zahlen', () => {
  const csv = quoteCsv([{
    name: 'Flansch;A', material: 'S235', thickness: 3, qty: 10, cutLength: 672.3, pierces: 8,
    weightKg: 0.2278, unitPrice: 4.5, total: 45,
  }], { lang: 'de', header: ['Pos', 'Bezeichnung', 'Material', 'Dicke', 'Menge', 'Schnitt', 'Einstiche', 'Gewicht', 'EP', 'GP'] });
  const lines = csv.replace(BOM, '').trim().split('\r\n');
  assert.equal(lines[0], 'Pos;Bezeichnung;Material;Dicke;Menge;Schnitt;Einstiche;Gewicht;EP;GP');
  assert.equal(lines[1], '1;"Flansch;A";S235;3;10;672,3;8;0,228;4,50;45,00');
  assert.ok(csv.startsWith(BOM), 'BOM für Excel');
});

test('quoteCsv: englische Ausgabe mit Komma und Dezimalpunkt', () => {
  const csv = quoteCsv([{
    name: 'Bracket', material: 'Steel', thickness: 1.5, qty: 2, cutLength: 100, pierces: 1,
    weightKg: 1.2345, unitPrice: 12.3, total: 24.6,
  }], { lang: 'en', header: ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'] });
  assert.equal(csv.replace(BOM, '').trim().split('\r\n')[1], '1,Bracket,Steel,1.5,2,100,1,1.235,12.30,24.60');
});

// --- Übersetzungen -------------------------------------------------------------------------

test('i18n: Deutsch und Englisch haben exakt dieselben Schlüssel, keine leeren Texte', () => {
  const de = Object.keys(STRINGS.de).sort();
  const en = Object.keys(STRINGS.en).sort();
  assert.deepEqual(de, en);
  for (const lang of ['de', 'en']) {
    for (const [k, v] of Object.entries(STRINGS[lang])) assert.ok(typeof v === 'string' && v.length > 0, `${lang}.${k}`);
  }
});

test('i18n: Platzhalter werden in beiden Sprachen gleich verwendet', () => {
  const vars = (s) => (s.match(/\{\w+\}/g) ?? []).sort().join();
  for (const k of Object.keys(STRINGS.de)) assert.equal(vars(STRINGS.de[k]), vars(STRINGS.en[k]), k);
});

test('i18n: t() ersetzt Platzhalter, unbekannte Schlüssel fallen auf den Schlüssel zurück', () => {
  const t = createI18n('de');
  assert.equal(t('warn.duplicates', { n: 3 }), STRINGS.de['warn.duplicates'].replace('{n}', '3'));
  assert.equal(t('gibt.es.nicht'), 'gibt.es.nicht');
  assert.equal(createI18n('fr')('app.title'), STRINGS.en['app.title'], 'unbekannte Sprache → Englisch');
});
