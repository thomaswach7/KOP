import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createPart, refreshGeometry, pricePart, normalizePart, cleanName } from '../src/ui/part.js';
import { sanitizeSettings } from '../src/cost/defaults.js';
import { e, doc, sample } from './helpers.mjs';

const settings = sanitizeSettings();
const keys = (r) => r.warnings.map((w) => w.key);

test('cleanName: Dateiendung und Pfad entfallen, Länge begrenzt', () => {
  assert.equal(cleanName('Flansch_DN50.DXF'), 'Flansch_DN50');
  assert.equal(cleanName('  teil.v2.dxf '), 'teil.v2');
  assert.equal(cleanName('.dxf'), 'Teil');
  assert.equal(cleanName('x'.repeat(300) + '.dxf').length, 120);
});

test('createPart: Hilfslayer wird vorab abgewählt, Kontur ist geschlossen, Preis > 0', () => {
  const part = createPart('halteblech.dxf', sample('halteblech'), settings);
  assert.equal(part.name, 'halteblech');
  assert.deepEqual(part.ignoreLayers, ['HILFSLINIE']);
  assert.equal(part.analysis.openCount, 0);
  assert.equal(part.materialId, settings.materials[0].id);
  assert.equal(part.thickness, 3);
  const r = pricePart(part, settings);
  assert.ok(r.price.unitPrice > 0);
  assert.equal(r.breaks.length, settings.quantities.length);
  assert.ok(keys(r).includes('warn.ok'));
  assert.ok(keys(r).includes('warn.ignored'));
});

test('createPart: jede Position bekommt eine eigene ID', () => {
  const a = createPart('a.dxf', sample('flansch'), settings);
  const b = createPart('b.dxf', sample('flansch'), settings);
  assert.notEqual(a.id, b.id);
});

test('createPart übernimmt zuletzt verwendetes Material und Dicke als Vorgabe', () => {
  const part = createPart('a.dxf', sample('flansch'), settings, { materialId: 'almg3', thickness: 5 });
  assert.equal(part.materialId, 'almg3');
  assert.equal(part.thickness, 5);
});

test('würde die Vorauswahl alle Layer abwählen, bleibt alles aktiv', () => {
  const part = createPart('t.dxf', doc(e('LINE', 8, 'TEXT', 10, 0, 20, 0, 11, 5, 21, 0)), settings);
  assert.deepEqual(part.ignoreLayers, []);
  assert.equal(part.analysis.pierces, 1);
});

test('Hinweise: offene Kontur, Duplikate und Null-Längen werden gemeldet, kein "alles in Ordnung"', () => {
  const r = pricePart(createPart('o.dxf', sample('offene-kontur'), settings), settings);
  assert.ok(keys(r).includes('warn.open'));
  assert.ok(keys(r).includes('warn.duplicates'));
  assert.ok(keys(r).includes('warn.zero'));
  assert.equal(keys(r).includes('warn.ok'), false);
  assert.equal(r.warnings.find((w) => w.key === 'warn.open').level, 'warn');
});

test('Hinweis bei angenommener Einheit (R12 ohne $INSUNITS) und bei kleinem Loch', () => {
  const part = createPart('r12.dxf', sample('r12-polyline'), settings);
  assert.ok(keys(pricePart(part, settings)).includes('warn.unitAssumed'));
  part.thickness = 12; // Loch Ø10 < 12 mm Blech
  const r = pricePart(part, settings);
  const small = r.warnings.find((w) => w.key === 'warn.small');
  assert.equal(small.vars.t, 12);
});

test('Einheit umstellen skaliert die Geometrie neu (mm → Zoll)', () => {
  const part = createPart('f.dxf', sample('flansch'), settings);
  const mm = part.analysis.cutLength;
  part.units = 'in';
  refreshGeometry(part, settings);
  assert.ok(Math.abs(part.analysis.cutLength - mm * 25.4) < 1e-6);
});

test('Toleranz erhöhen schließt die Lücke: Hinweis verschwindet', () => {
  const part = createPart('o.dxf', sample('offene-kontur'), settings);
  part.tol = 1;
  refreshGeometry(part, settings);
  assert.equal(part.analysis.openCount, 0);
  assert.equal(keys(pricePart(part, settings)).includes('warn.open'), false);
});

test('normalizePart: gelöschtes Material → erstes Material; fehlende Dicke → nächstliegende', () => {
  const part = createPart('f.dxf', sample('flansch'), settings, { materialId: 'almg3', thickness: 10 });
  const fewer = sanitizeSettings({ ...settings, materials: settings.materials.filter((m) => m.id !== 'almg3') });
  normalizePart(part, fewer);
  assert.equal(part.materialId, fewer.materials[0].id);
  assert.equal(part.thickness, 10);
  const thin = sanitizeSettings({
    materials: [{ id: 'x', name: 'X', density: 8, pricePerKg: 2, thicknesses: [{ t: 2, speed: 100, pierce: 1 }, { t: 6, speed: 50, pierce: 2 }] }],
  });
  normalizePart(part, thin);
  assert.equal(part.materialId, 'x');
  assert.equal(part.thickness, 6);
});

test('Datei ohne Schnittgeometrie: Hinweis "keine Geometrie", kein Absturz bei der Preisbildung', () => {
  const part = createPart('leer.dxf', doc(e('TEXT', 10, 0, 20, 0, 1, 'x')), settings);
  const r = pricePart(part, settings);
  assert.ok(keys(r).includes('warn.none'));
  assert.equal(part.analysis.pierces, 0);
});
