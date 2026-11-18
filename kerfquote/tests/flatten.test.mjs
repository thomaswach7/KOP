import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseDxf } from '../src/dxf/parse.js';
import { flatten, primLength, resolveUnits } from '../src/dxf/flatten.js';
import { e, doc, close } from './helpers.mjs';

const flat = (entities, opts, extra) => flatten(parseDxf(doc(entities, extra)), opts);
const total = (prims) => prims.reduce((s, p) => s + primLength(p), 0);
const PI = Math.PI;

test('LINE wird zu einem Liniensegment mit korrekter Länge', () => {
  const { prims } = flat(e('LINE', 8, 'K', 10, 0, 20, 0, 11, 3, 21, 4));
  assert.equal(prims.length, 1);
  assert.equal(prims[0].k, 'L');
  assert.equal(prims[0].layer, 'K');
  assert.ok(close(primLength(prims[0]), 5));
});

test('CIRCLE wird zum Vollkreis: Länge 2πr, Start = Ende', () => {
  const { prims } = flat(e('CIRCLE', 10, 10, 20, 20, 40, 5));
  assert.equal(prims[0].k, 'A');
  assert.ok(close(primLength(prims[0]), 2 * PI * 5));
  assert.ok(close(prims[0].x0, prims[0].x1) && close(prims[0].y0, prims[0].y1));
});

test('ARC läuft gegen den Uhrzeigersinn, auch über 0° hinweg (350° → 10° = 20°)', () => {
  const { prims } = flat(e('ARC', 10, 0, 20, 0, 40, 10, 50, 350, 51, 10));
  assert.ok(close(primLength(prims[0]), 10 * (20 * PI / 180)));
  assert.ok(close(prims[0].x1, 10 * Math.cos(10 * PI / 180)));
  assert.ok(close(prims[0].y1, 10 * Math.sin(10 * PI / 180)));
});

test('LWPOLYLINE mit Bulge 1 ergibt einen Halbkreis über der Sehne', () => {
  const { prims } = flat(e('LWPOLYLINE', 90, 2, 70, 0, 10, 0, 20, 0, 42, 1, 10, 10, 20, 0));
  assert.equal(prims.length, 1);
  assert.ok(close(primLength(prims[0]), PI * 5));
  assert.ok(close(prims[0].cx, 5) && close(prims[0].cy, 0) && close(prims[0].r, 5));
  assert.ok(prims[0].sw > 0, 'positiver Bulge = gegen den Uhrzeigersinn');
});

test('negativer Bulge läuft im Uhrzeigersinn, geschlossene Polylinie schließt zum Start', () => {
  const { prims } = flat(e('LWPOLYLINE', 90, 2, 70, 1, 10, 0, 20, 0, 42, -1, 10, 10, 20, 0));
  assert.equal(prims.length, 2);
  assert.ok(prims[0].sw < 0);
  assert.equal(prims[1].k, 'L');
  assert.ok(close(total(prims), PI * 5 + 10));
});

test('Einheiten: Zoll aus $INSUNITS wird nach mm skaliert', () => {
  const header = '9\n$INSUNITS\n70\n1\n';
  const r = flat(e('LINE', 10, 0, 20, 0, 11, 2, 21, 0), {}, { header });
  assert.ok(close(primLength(r.prims[0]), 50.8));
  assert.deepEqual(r.unit, { name: 'in', scale: 25.4, source: 'header' });
});

test('Einheiten: ohne Angabe gilt die Standardeinheit, manuelle Wahl hat Vorrang', () => {
  assert.deepEqual(resolveUnits({ insunits: 0 }, 'auto', 'mm'), { name: 'mm', scale: 1, source: 'assumed' });
  assert.deepEqual(resolveUnits({ insunits: null }, 'auto', 'in'), { name: 'in', scale: 25.4, source: 'assumed' });
  assert.deepEqual(resolveUnits({ insunits: 4 }, 'cm', 'mm'), { name: 'cm', scale: 10, source: 'manual' });
  assert.deepEqual(resolveUnits({ insunits: 6 }, 'auto', 'mm'), { name: 'm', scale: 1000, source: 'header' });
});

test('INSERT: Verschiebung, Drehung und Skalierung des Blockinhalts', () => {
  const blocks = e('BLOCK', 2, 'B', 10, 0, 20, 0) + e('LINE', 8, '0', 10, 0, 20, 0, 11, 10, 21, 0) + e('ENDBLK');
  const { prims } = flat(e('INSERT', 8, 'TEILE', 2, 'B', 10, 100, 20, 50, 41, 2, 42, 2, 50, 90), {}, { blocks });
  const p = prims[0];
  assert.ok(close(p.x0, 100) && close(p.y0, 50));
  assert.ok(close(p.x1, 100) && close(p.y1, 70), `Endpunkt ${p.x1},${p.y1}`);
  assert.equal(p.layer, 'TEILE', 'Layer 0 im Block erbt den Layer des INSERT');
});

test('INSERT berücksichtigt den Basispunkt des Blocks', () => {
  const blocks = e('BLOCK', 2, 'B', 10, 5, 20, 5) + e('CIRCLE', 8, 'X', 10, 5, 20, 5, 40, 1) + e('ENDBLK');
  const { prims } = flat(e('INSERT', 2, 'B', 10, 20, 20, 30), {}, { blocks });
  assert.ok(close(prims[0].cx, 20) && close(prims[0].cy, 30));
  assert.equal(prims[0].layer, 'X');
});

test('gespiegelter INSERT (X-Faktor -1) kehrt die Bogenrichtung um, Länge bleibt', () => {
  const blocks = e('BLOCK', 2, 'B', 10, 0, 20, 0) + e('ARC', 10, 0, 20, 0, 40, 10, 50, 0, 51, 90) + e('ENDBLK');
  const { prims } = flat(e('INSERT', 2, 'B', 10, 0, 20, 0, 41, -1), {}, { blocks });
  const p = prims[0];
  assert.ok(close(primLength(p), 10 * PI / 2));
  assert.ok(close(p.x0, -10) && close(p.y0, 0));
  assert.ok(close(p.x1, 0) && close(p.y1, 10));
  assert.ok(p.sw < 0);
});

test('ungleichmäßig skalierter Kreis wird zur Ellipse (Umfang passt zur Näherung)', () => {
  const blocks = e('BLOCK', 2, 'B', 10, 0, 20, 0) + e('CIRCLE', 10, 0, 20, 0, 40, 10) + e('ENDBLK');
  const { prims } = flat(e('INSERT', 2, 'B', 10, 0, 20, 0, 41, 2, 42, 1), {}, { blocks });
  // Ramanujan-Näherung für a = 20, b = 10
  const a = 20; const b = 10; const h = ((a - b) / (a + b)) ** 2;
  const expected = PI * (a + b) * (1 + (3 * h) / (10 + Math.sqrt(4 - 3 * h)));
  assert.ok(Math.abs(total(prims) - expected) < 0.01, `${total(prims)} vs ${expected}`);
});

test('verschachtelte Blöcke werden aufgelöst, fehlende Blöcke gezählt', () => {
  const blocks = e('BLOCK', 2, 'INNEN', 10, 0, 20, 0) + e('CIRCLE', 10, 0, 20, 0, 40, 1) + e('ENDBLK')
    + e('BLOCK', 2, 'AUSSEN', 10, 0, 20, 0) + e('INSERT', 2, 'INNEN', 10, 5, 20, 0) + e('ENDBLK');
  const r = flat(e('INSERT', 2, 'AUSSEN', 10, 10, 20, 10) + e('INSERT', 2, 'GIBTSNICHT', 10, 0, 20, 0), {}, { blocks });
  assert.equal(r.prims.length, 1);
  assert.ok(close(r.prims[0].cx, 15) && close(r.prims[0].cy, 10));
  assert.equal(r.notes.missingBlocks, 1);
});

test('ein Block, der sich selbst enthält, führt nicht zur Endlosschleife', () => {
  const blocks = e('BLOCK', 2, 'A', 10, 0, 20, 0) + e('LINE', 10, 0, 20, 0, 11, 1, 21, 0)
    + e('INSERT', 2, 'A', 10, 1, 20, 0) + e('ENDBLK');
  const r = flat(e('INSERT', 2, 'A', 10, 0, 20, 0), {}, { blocks });
  assert.ok(r.prims.length >= 1 && r.prims.length < 100);
});

test('Extrusion (0,0,-1): Bogen wird an der Y-Achse gespiegelt (OCS → WCS)', () => {
  const { prims } = flat(e('ARC', 10, -20, 20, 40, 40, 20, 50, 0, 51, 90, 210, 0, 220, 0, 230, -1));
  const p = prims[0];
  assert.ok(close(p.cx, 20) && close(p.cy, 40));
  const ends = [[p.x0, p.y0], [p.x1, p.y1]].sort((u, v) => u[0] - v[0]);
  assert.ok(close(ends[0][0], 0) && close(ends[0][1], 40));
  assert.ok(close(ends[1][0], 20) && close(ends[1][1], 60));
  assert.ok(close(primLength(p), 20 * PI / 2));
});

test('ELLIPSE: voller Umfang und Teilbogen-Endpunkte', () => {
  const full = flat(e('ELLIPSE', 10, 0, 20, 0, 11, 20, 21, 0, 40, 0.5, 41, 0, 42, 2 * PI));
  const a = 20; const b = 10; const h = ((a - b) / (a + b)) ** 2;
  const ram = PI * (a + b) * (1 + (3 * h) / (10 + Math.sqrt(4 - 3 * h)));
  assert.ok(Math.abs(total(full.prims) - ram) < 0.01);
  const half = flat(e('ELLIPSE', 10, 0, 20, 0, 11, 20, 21, 0, 40, 0.5, 41, 0, 42, PI));
  const first = half.prims[0]; const last = half.prims.at(-1);
  assert.ok(close(first.x0, 20) && close(first.y0, 0));
  assert.ok(close(last.x1, -20, 1e-9) && close(last.y1, 0, 1e-9));
  assert.ok(half.prims.every((p) => p.y0 >= -1e-9), 'Halbellipse verläuft über die obere Seite (CCW)');
});

test('SPLINE (geklemmt): beginnt und endet an den Randkontrollpunkten, Bézier-Länge stimmt', () => {
  // Quadratische Bézierkurve (0,0)-(5,10)-(10,0): Länge numerisch 2·∫…
  const { prims } = flat(e('SPLINE', 70, 8, 71, 2, 40, 0, 40, 0, 40, 0, 40, 1, 40, 1, 40, 1,
    10, 0, 20, 0, 10, 5, 20, 10, 10, 10, 20, 0));
  assert.ok(close(prims[0].x0, 0) && close(prims[0].y0, 0));
  assert.ok(close(prims.at(-1).x1, 10) && close(prims.at(-1).y1, 0));
  let ref = 0; let px = 0; let py = 0;
  for (let i = 1; i <= 200000; i++) {
    const t = i / 200000;
    const x = 2 * (1 - t) * t * 5 + t * t * 10; const y = 2 * (1 - t) * t * 10;
    ref += Math.hypot(x - px, y - py); px = x; py = y;
  }
  assert.ok(Math.abs(total(prims) - ref) < 0.005, `${total(prims)} vs ${ref}`);
});

test('rationaler SPLINE: Viertelkreis als NURBS hat Länge πr/2', () => {
  const w = Math.SQRT1_2;
  const { prims } = flat(e('SPLINE', 70, 12, 71, 2, 40, 0, 40, 0, 40, 0, 40, 1, 40, 1, 40, 1,
    10, 10, 20, 0, 10, 10, 20, 10, 10, 0, 20, 10, 41, 1, 41, w, 41, 1));
  assert.ok(Math.abs(total(prims) - 10 * PI / 2) < 0.002, String(total(prims)));
});

test('SPLINE nur mit Stützpunkten wird als Polygonzug angenähert und vermerkt', () => {
  const r = flat(e('SPLINE', 70, 8, 71, 3, 11, 0, 21, 0, 11, 10, 21, 0, 11, 10, 21, 10));
  assert.ok(close(total(r.prims), 20));
  assert.equal(r.notes.fitSplines, 1);
});

test('Texte, Bemaßungen usw. werden ignoriert und je Typ gezählt', () => {
  const r = flat(e('TEXT', 10, 0, 20, 0, 1, 'A') + e('TEXT', 10, 0, 20, 0, 1, 'B')
    + e('DIMENSION', 8, 'M') + e('LINE', 10, 0, 20, 0, 11, 1, 21, 0));
  assert.equal(r.prims.length, 1);
  assert.deepEqual(r.ignored, { TEXT: 2, DIMENSION: 1 });
});

test('Entitäten im Papierbereich und 3D-Netze zählen nicht zur Schnittgeometrie', () => {
  const r = flat(e('LINE', 67, 1, 10, 0, 20, 0, 11, 100, 21, 0)
    + e('POLYLINE', 70, 64) + e('VERTEX', 10, 0, 20, 0) + e('VERTEX', 10, 1, 20, 0) + e('SEQEND')
    + e('LINE', 10, 0, 20, 0, 11, 1, 21, 0));
  assert.equal(r.prims.length, 1);
  assert.equal(r.notes.paperSpace, 1);
});

test('doppelte Scheitelpunkte in Polylinien erzeugen keine Null-Segmente', () => {
  const { prims } = flat(e('LWPOLYLINE', 90, 3, 70, 0, 10, 0, 20, 0, 10, 0, 20, 0, 10, 5, 20, 0));
  assert.equal(prims.length, 1);
});
