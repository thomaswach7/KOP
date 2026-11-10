import { test } from 'node:test';
import assert from 'node:assert/strict';
import { priceLine, quantityBreaks, quoteTotals, round2, featureWarnings } from '../src/cost/model.js';
import { DEFAULT_SETTINGS, DEFAULT_MATERIALS, sanitizeSettings } from '../src/cost/defaults.js';
import { close } from './helpers.mjs';

const steel = {
  id: 'st', name: 'Stahl', density: 7.85, pricePerKg: 1.2,
  thicknesses: [{ t: 3, speed: 4200, pierce: 0.6 }, { t: 10, speed: 1800, pierce: 2 }],
};
const settings = { machineRate: 120, setupCost: 30, markupPct: 25, partGap: 10, pricePerBend: 1.5, minOrder: 50, vatPct: 19 };
const metrics = { cutLength: 2100, pierces: 10, rect: { w: 190, h: 90 }, netArea: 15000 };
const line = { thickness: 3, qty: 10, bends: 2, extra: 0.5 };

test('Stückpreis: Material + Schneidzeit + Rüstanteil + Biegen + Zusatz, plus Zuschlag', () => {
  const r = priceLine(metrics, line, steel, settings);
  assert.ok(close(r.chargedWeightKg, 0.471, 1e-9));
  assert.ok(close(r.materialCost, 0.5652, 1e-9));
  assert.ok(close(r.cutTimeSec, 36, 1e-9));
  assert.ok(close(r.cutCost, 1.2, 1e-9));
  assert.ok(close(r.setupPerPart, 3, 1e-9));
  assert.ok(close(r.bendCost, 3, 1e-9));
  assert.ok(close(r.extraCost, 0.5, 1e-9));
  assert.ok(close(r.costPerPart, 8.2652, 1e-9));
  assert.equal(r.unitPrice, 10.33);
  assert.equal(r.total, 103.3);
  assert.ok(close(r.weightKg, 0.35325, 1e-9));
});

test('Rüstkosten verteilen sich auf die Menge: Einzelstück ist deutlich teurer', () => {
  const one = priceLine(metrics, { ...line, qty: 1 }, steel, settings);
  assert.equal(one.unitPrice, 44.08);
  assert.equal(one.total, 44.08);
});

test('Staffelpreise fallen mit der Menge und nähern sich dem Preis ohne Rüstanteil', () => {
  const rows = quantityBreaks(metrics, line, steel, settings, [1, 10, 100, 1000]);
  assert.deepEqual(rows.map((r) => r.qty), [1, 10, 100, 1000]);
  assert.deepEqual(rows.map((r) => r.unitPrice), [44.08, 10.33, 6.96, 6.62]);
  assert.equal(rows[2].total, 696);
});

test('dickeres Blech: langsamerer Vorschub und längere Einstechzeit erhöhen die Schneidzeit', () => {
  const r = priceLine(metrics, { ...line, thickness: 10 }, steel, settings);
  assert.ok(close(r.cutTimeSec, (2100 / 1800) * 60 + 10 * 2, 1e-9));
  assert.ok(close(r.chargedWeightKg, 1.57, 1e-9));
});

test('nicht hinterlegte Dicke oder fehlendes Material → kein Preis (null)', () => {
  assert.equal(priceLine(metrics, { ...line, thickness: 7 }, steel, settings), null);
  assert.equal(priceLine(metrics, line, null, settings), null);
});

test('ungültige Menge wird auf mindestens 1 Stück begrenzt, negative Zusätze auf 0', () => {
  const r = priceLine(metrics, { thickness: 3, qty: 0, bends: -3, extra: -5 }, steel, settings);
  assert.equal(r.qty, 1);
  assert.equal(r.bendCost, 0);
  assert.equal(r.extraCost, 0);
  const frac = priceLine(metrics, { ...line, qty: 2.7 }, steel, settings);
  assert.equal(frac.qty, 2);
});

test('ohne Geometrie (kein Rechteck) entstehen keine Materialkosten, aber auch kein Absturz', () => {
  const r = priceLine({ cutLength: 0, pierces: 0, rect: null, netArea: 0 }, line, steel, settings);
  assert.equal(r.materialCost, 0);
  assert.equal(r.cutCost, 0);
});

test('round2 rundet kaufmännisch auf Cent (auch Problemfälle der Gleitkommazahlen)', () => {
  assert.equal(round2(1.005), 1.01);
  assert.equal(round2(2.675), 2.68);
  assert.equal(round2(10.3315), 10.33);
  assert.equal(round2(0.1 + 0.2), 0.3);
});

test('Angebotssumme: Mindestauftragswert wird als Zuschlag aufgefüllt, dann MwSt.', () => {
  const t = quoteTotals([20, 15.5], settings);
  assert.deepEqual(t, { net: 35.5, surcharge: 14.5, subtotal: 50, vat: 9.5, gross: 59.5 });
});

test('Angebotssumme über dem Mindestwert: kein Zuschlag; leeres Angebot bleibt bei 0', () => {
  assert.deepEqual(quoteTotals([103.3, 44.08], settings),
    { net: 147.38, surcharge: 0, subtotal: 147.38, vat: 28, gross: 175.38 });
  assert.deepEqual(quoteTotals([], settings), { net: 0, surcharge: 0, subtotal: 0, vat: 0, gross: 0 });
});

test('Fertigungshinweis: Innenkontur kleiner als die Blechdicke', () => {
  assert.deepEqual(featureWarnings({ minInnerSize: 2, openCount: 0 }, 3), ['smallFeature']);
  assert.deepEqual(featureWarnings({ minInnerSize: 3, openCount: 0 }, 3), []);
  assert.deepEqual(featureWarnings({ minInnerSize: null, openCount: 2 }, 3), ['openContours']);
});

test('Standardwerte: jedes Material hat gültige Dichte, Preis und aufsteigende Dicken', () => {
  assert.ok(DEFAULT_MATERIALS.length >= 3);
  for (const m of DEFAULT_MATERIALS) {
    assert.ok(m.id && m.name && m.density > 0 && m.pricePerKg > 0);
    assert.ok(m.thicknesses.length >= 5);
    m.thicknesses.forEach((row, i) => {
      assert.ok(row.t > 0 && row.speed > 0 && row.pierce > 0);
      if (i > 0) {
        assert.ok(row.t > m.thicknesses[i - 1].t, 'Dicken aufsteigend');
        assert.ok(row.speed < m.thicknesses[i - 1].speed, 'dicker = langsamer');
      }
    });
  }
});

test('sanitizeSettings: übernimmt gültige Werte, ersetzt Unsinn durch Standardwerte', () => {
  const s = sanitizeSettings({
    machineRate: 95, markupPct: 'abc', vatPct: -5, currency: 'XXL', setupCost: 1e12,
    company: { name: 'Blech GmbH', address: 42, logo: 'javascript:alert(1)' },
    materials: [{ id: 'm1', name: 'Messing', density: 8.5, pricePerKg: 9, thicknesses: [{ t: 2, speed: 3000, pierce: 0.4 }, { t: -1, speed: 5, pierce: 1 }] }, { name: 'kaputt' }],
    quantities: [50, 1, 'x', 10, 10, -4],
    unbekannt: 'weg',
  });
  assert.equal(s.machineRate, 95);
  assert.equal(s.markupPct, DEFAULT_SETTINGS.markupPct);
  assert.equal(s.vatPct, DEFAULT_SETTINGS.vatPct);
  assert.equal(s.currency, DEFAULT_SETTINGS.currency);
  assert.equal(s.setupCost, DEFAULT_SETTINGS.setupCost);
  assert.equal(s.company.name, 'Blech GmbH');
  assert.equal(s.company.address, '');
  assert.equal(s.company.logo, '');
  assert.equal(s.materials.length, 1);
  assert.deepEqual(s.materials[0].thicknesses, [{ t: 2, speed: 3000, pierce: 0.4 }]);
  assert.deepEqual(s.quantities, [1, 10, 50]);
  assert.equal('unbekannt' in s, false);
});

test('sanitizeSettings: ohne Eingabe kommen vollständige Standardwerte (tiefe Kopie)', () => {
  const s = sanitizeSettings(undefined);
  assert.deepEqual(s, DEFAULT_SETTINGS);
  s.materials[0].name = 'geändert';
  assert.notEqual(DEFAULT_SETTINGS.materials[0].name, 'geändert');
});

test('sanitizeSettings: Logo nur als Bild-Data-URL, leere Materialliste fällt auf Standard zurück', () => {
  const png = 'data:image/png;base64,iVBORw0KGgo=';
  assert.equal(sanitizeSettings({ company: { logo: png } }).company.logo, png);
  assert.equal(sanitizeSettings({ company: { logo: 'data:text/html;base64,PGI+' } }).company.logo, '');
  assert.equal(sanitizeSettings({ materials: [] }).materials.length, DEFAULT_MATERIALS.length);
});
