import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createFormat, addDays, todayIso, defaultQuoteNumber } from '../src/ui/format.js';

const de = createFormat('de', 'EUR');
const en = createFormat('en', 'USD');
const norm = (s) => s.replace(/\s/g, ' '); // Intl nutzt geschützte Leerzeichen

test('Währung und Zahlen folgen der Sprache', () => {
  assert.equal(norm(de.money(1234.5)), '1.234,50 €');
  assert.equal(en.money(1234.5), '$1,234.50');
  assert.equal(de.num(3.14159, 2), '3,14');
  assert.equal(en.num(2, 2, 2), '2.00');
});

test('Länge: unter 1 m in mm, darüber in m', () => {
  assert.equal(de.length(672.3008), '672,3 mm');
  assert.equal(de.length(12345), '12,35 m');
  assert.equal(en.length(999.96), '1,000 mm');
});

test('Fläche in cm², große Flächen in m²; Gewicht mit passender Genauigkeit', () => {
  assert.equal(de.area(9671.39), '96,7 cm²');
  assert.equal(de.area(2_500_000), '2,500 m²');
  assert.equal(de.weight(0.2278), '0,228 kg');
  assert.equal(en.weight(123.456), '123.5 kg');
});

test('Abmessungen und Schneidzeit', () => {
  assert.equal(de.dims(150, 80.04), '150 × 80 mm');
  assert.equal(de.time(36), '0:36 min');
  assert.equal(de.time(125.4), '2:05 min');
  assert.equal(de.time(3599.6), '1 h 00 min');
  assert.equal(de.time(7384), '2 h 03 min');
  assert.equal(de.time(0), '0:00 min');
});

test('Datum wird ohne Zeitzonen-Verschiebung formatiert', () => {
  assert.equal(de.date('2026-11-10'), '10.11.2026');
  assert.equal(en.date('2026-01-01'), 'Jan 1, 2026');
  assert.equal(de.date('kaputt'), '');
});

test('addDays rechnet über Monats- und Jahresgrenzen', () => {
  assert.equal(addDays('2026-11-10', 30), '2026-12-10');
  assert.equal(addDays('2026-12-20', 30), '2027-01-19');
  assert.equal(addDays('2028-02-28', 1), '2028-02-29');
});

test('todayIso liefert das lokale Datum als JJJJ-MM-TT; Angebotsnummer baut darauf auf', () => {
  assert.equal(todayIso(new Date(2026, 10, 5, 23, 30)), '2026-11-05');
  assert.equal(defaultQuoteNumber('A-', '2026-11-05'), 'A-20261105-01');
});
