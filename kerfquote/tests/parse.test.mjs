import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseDxf, DxfError } from '../src/dxf/parse.js';
import { e, doc } from './helpers.mjs';

test('liest eine LINE mit Layer und Koordinaten', () => {
  const d = parseDxf(doc(e('LINE', 8, 'KONTUR', 10, 1.5, 20, 2, 11, 30, 21, -4)));
  assert.equal(d.entities.length, 1);
  assert.deepEqual(d.entities[0], {
    type: 'LINE', layer: 'KONTUR', paperSpace: false, extZ: 1, x1: 1.5, y1: 2, x2: 30, y2: -4,
  });
});

test('verträgt CRLF-Zeilenenden und eingerückte Gruppencodes', () => {
  const text = doc(e('CIRCLE', 8, '0', 10, 5, 20, 6, 40, 2.5))
    .replace(/\n/g, '\r\n')
    .replace(/^(\d+)\r$/gm, '  $1\r');
  const d = parseDxf(text);
  assert.equal(d.entities[0].type, 'CIRCLE');
  assert.equal(d.entities[0].r, 2.5);
  assert.equal(d.entities[0].cx, 5);
});

test('liest $INSUNITS und $MEASUREMENT aus dem HEADER', () => {
  const header = '9\n$INSUNITS\n70\n1\n9\n$MEASUREMENT\n70\n0\n9\n$ACADVER\n1\nAC1024\n';
  const d = parseDxf(doc(e('LINE', 10, 0, 20, 0, 11, 1, 21, 0), { header }));
  assert.equal(d.header.insunits, 1);
  assert.equal(d.header.measurement, 0);
  assert.equal(d.header.acadver, 'AC1024');
});

test('Layer fehlt → Standard-Layer "0"', () => {
  const d = parseDxf(doc(e('LINE', 10, 0, 20, 0, 11, 1, 21, 0)));
  assert.equal(d.entities[0].layer, '0');
});

test('LWPOLYLINE: Scheitelpunkte, Bulge und Geschlossen-Flag', () => {
  const d = parseDxf(doc(e('LWPOLYLINE', 8, '0', 90, 3, 70, 1,
    10, 0, 20, 0, 42, 1, 10, 10, 20, 0, 10, 10, 20, 5)));
  const p = d.entities[0];
  assert.equal(p.closed, true);
  assert.deepEqual(p.vertices, [
    { x: 0, y: 0, bulge: 1 }, { x: 10, y: 0, bulge: 0 }, { x: 10, y: 5, bulge: 0 },
  ]);
});

test('alte POLYLINE mit VERTEX … SEQEND wird zu einer Entität', () => {
  const text = doc(
    e('POLYLINE', 8, 'A', 66, 1, 70, 1)
    + e('VERTEX', 8, 'A', 10, 0, 20, 0, 42, 0.5)
    + e('VERTEX', 8, 'A', 10, 4, 20, 0)
    + e('VERTEX', 8, 'A', 10, 4, 20, 3)
    + e('SEQEND', 8, 'A')
    + e('LINE', 10, 0, 20, 0, 11, 1, 21, 0));
  const d = parseDxf(text);
  assert.equal(d.entities.length, 2);
  assert.equal(d.entities[0].type, 'POLYLINE');
  assert.equal(d.entities[0].closed, true);
  assert.equal(d.entities[0].vertices.length, 3);
  assert.equal(d.entities[0].vertices[0].bulge, 0.5);
  assert.equal(d.entities[1].type, 'LINE');
});

test('3D-Netze (POLYLINE-Flag 16/64) werden nicht als Kontur übernommen', () => {
  const text = doc(e('POLYLINE', 70, 64) + e('VERTEX', 10, 0, 20, 0) + e('VERTEX', 10, 1, 20, 0) + e('SEQEND'));
  const d = parseDxf(text);
  assert.equal(d.entities[0].mesh, true);
});

test('BLOCKS: Basispunkt und Entitäten; INSERT mit Skalierung und Drehung', () => {
  const blocks = e('BLOCK', 8, '0', 2, 'LOCH', 70, 0, 10, 1, 20, 2)
    + e('CIRCLE', 8, '0', 10, 0, 20, 0, 40, 4) + e('ENDBLK', 8, '0');
  const d = parseDxf(doc(e('INSERT', 8, 'B', 2, 'LOCH', 10, 50, 20, 60, 41, 2, 42, -2, 50, 30), { blocks }));
  const b = d.blocks.get('LOCH');
  assert.deepEqual(b.base, { x: 1, y: 2 });
  assert.equal(b.entities.length, 1);
  assert.deepEqual(d.entities[0], {
    type: 'INSERT', layer: 'B', paperSpace: false, extZ: 1,
    name: 'LOCH', x: 50, y: 60, sx: 2, sy: -2, rot: 30, cols: 1, rows: 1, dx: 0, dy: 0,
  });
});

test('Papierbereich (Gruppe 67 = 1) und Extrusion (230 = -1) werden markiert', () => {
  const d = parseDxf(doc(
    e('LINE', 67, 1, 10, 0, 20, 0, 11, 1, 21, 0) + e('ARC', 10, 0, 20, 0, 40, 5, 50, 0, 51, 90, 210, 0, 220, 0, 230, -1)));
  assert.equal(d.entities[0].paperSpace, true);
  assert.equal(d.entities[1].extZ, -1);
  assert.equal(d.entities[1].a1, 90);
});

test('SPLINE: Grad, Knoten, Kontrollpunkte, Gewichte', () => {
  const d = parseDxf(doc(e('SPLINE', 70, 8, 71, 2, 40, 0, 40, 0, 40, 0, 40, 1, 40, 1, 40, 1,
    10, 0, 20, 0, 10, 5, 20, 10, 10, 10, 20, 0, 41, 1, 41, 2, 41, 1)));
  const s = d.entities[0];
  assert.equal(s.degree, 2);
  assert.deepEqual(s.knots, [0, 0, 0, 1, 1, 1]);
  assert.deepEqual(s.ctrl, [{ x: 0, y: 0 }, { x: 5, y: 10 }, { x: 10, y: 0 }]);
  assert.deepEqual(s.weights, [1, 2, 1]);
});

test('unbekannte Entitäten bleiben als Typ erhalten (für die Ignoriert-Statistik)', () => {
  const d = parseDxf(doc(e('MTEXT', 8, 'T', 10, 0, 20, 0, 1, 'Hallo') + e('DIMENSION', 8, 'T')));
  assert.deepEqual(d.entities.map((x) => x.type), ['MTEXT', 'DIMENSION']);
});

test('binäres DXF wird mit Code "binary" abgelehnt', () => {
  assert.throws(() => parseDxf('AutoCAD Binary DXF\r\n\x1a\x00abc'),
    (err) => err instanceof DxfError && err.code === 'binary');
});

test('leere Datei → Code "empty"; Text ohne DXF-Struktur → Code "invalid"', () => {
  assert.throws(() => parseDxf('   \n'), (err) => err instanceof DxfError && err.code === 'empty');
  assert.throws(() => parseDxf('Das ist keine DXF-Datei\nnur Text\n'),
    (err) => err instanceof DxfError && err.code === 'invalid');
});

test('DXF ohne SECTION-Rahmen (nur Entitäten bis EOF) ist nicht gültig', () => {
  assert.throws(() => parseDxf('0\nLINE\n10\n0\n20\n0\n11\n1\n21\n1\n0\nEOF\n'),
    (err) => err instanceof DxfError && err.code === 'invalid');
});

test('Leerzeilen am Dateiende stören nicht', () => {
  const d = parseDxf(doc(e('LINE', 10, 0, 20, 0, 11, 1, 21, 0)) + '\n\n  \n');
  assert.equal(d.entities.length, 1);
});
