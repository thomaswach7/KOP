import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseDxf } from '../src/dxf/parse.js';
import { flatten } from '../src/dxf/flatten.js';
import { analyze, layerStats, minAreaRect } from '../src/geom/analyze.js';
import { e, doc, sample, reference, close, relClose } from './helpers.mjs';

const PI = Math.PI;
const run = (text, opts) => analyze(flatten(parseDxf(text)).prims, opts);
const rectLines = (x, y, w, h, layer = '0') =>
  e('LINE', 8, layer, 10, x, 20, y, 11, x + w, 21, y)
  + e('LINE', 8, layer, 10, x + w, 20, y, 11, x + w, 21, y + h)
  + e('LINE', 8, layer, 10, x + w, 20, y + h, 11, x, 21, y + h)
  + e('LINE', 8, layer, 10, x, 20, y + h, 11, x, 21, y);

// --- Beispiel-Dateien gegen die unabhängige ezdxf-Referenz ---------------------------------

for (const [name, ref] of Object.entries(reference)) {
  test(`Beispiel ${name}: Schnittlänge, Einstiche, Fläche und Abmessungen stimmen mit der Referenz`, () => {
    const a = run(sample(name), { ignoreLayers: ref.skipLayers ?? [] });
    const refLength = ref.cutLength ?? ref.length;
    // ezdxf nähert Kreisbögen mit Bézierkurven an (Abweichung bis ca. 0,02 %)
    assert.ok(relClose(a.cutLength, refLength, 5e-4), `Länge ${a.cutLength} vs ${refLength}`);
    assert.equal(a.pierces, ref.pierces);
    assert.equal(a.openCount, ref.open);
    if (ref.netArea !== undefined) {
      assert.ok(relClose(a.netArea, ref.netArea, 1e-3), `Fläche ${a.netArea} vs ${ref.netArea}`);
    }
    const [minX, minY, maxX, maxY] = ref.bbox;
    assert.ok(close(a.bbox.minX, minX, 0.01) && close(a.bbox.minY, minY, 0.01), JSON.stringify(a.bbox));
    assert.ok(close(a.bbox.maxX, maxX, 0.01) && close(a.bbox.maxY, maxY, 0.01), JSON.stringify(a.bbox));
    if (ref.duplicates !== undefined) assert.equal(a.removed.duplicates, ref.duplicates);
    if (ref.zeroLength !== undefined) assert.equal(a.removed.zeroLength, ref.zeroLength);
  });
}

test('Flansch: exakte Werte (analytisch)', () => {
  const a = run(sample('flansch'));
  assert.ok(close(a.cutLength, PI * 214, 1e-6));
  assert.ok(close(a.netArea, (PI / 4) * (120 ** 2 - 40 ** 2 - 6 * 81), 1e-6));
  assert.equal(a.outerCount, 1);
  assert.equal(a.closedCount, 8);
  assert.ok(close(a.bbox.w, 120) && close(a.bbox.h, 120));
  assert.ok(close(a.minInnerSize, 9, 1e-6));
});

test('Halteblech: exakte Länge 530 + 52π; mit Hilfslinien-Layer entsteht eine offene Kontur', () => {
  const without = run(sample('halteblech'), { ignoreLayers: ['HILFSLINIE'] });
  assert.ok(close(without.cutLength, 530 + 52 * PI, 1e-6), String(without.cutLength));
  const withLayer = run(sample('halteblech'));
  assert.equal(withLayer.openCount, 1);
  assert.ok(close(withLayer.cutLength, 530 + 52 * PI + 170, 1e-6));
  assert.ok(close(withLayer.bbox.w, 170));
});

test('Block-Beispiel: exakte Länge und Fläche (analytisch), Außenkontur mit gespiegeltem Bogen ist geschlossen', () => {
  const a = run(sample('block-insert'));
  const length = (280 + 10 * PI) + 3 * 8 * PI + 12 * PI + 2 * 8 * PI + (40 + 8 * PI);
  assert.ok(close(a.cutLength, length, 1e-6), `${a.cutLength} vs ${length}`);
  assert.ok(close(a.netArea, reference['block-insert'].netArea, 1e-6));
  assert.equal(a.outerCount, 1);
});

// --- Verkettung ---------------------------------------------------------------------------

test('ungeordnete, gemischt gerichtete Linien werden zu einer geschlossenen Kontur', () => {
  const text = doc(
    e('LINE', 10, 10, 20, 5, 11, 10, 21, 0) + e('LINE', 10, 0, 20, 0, 11, 10, 21, 0)
    + e('LINE', 10, 0, 20, 5, 11, 0, 21, 0) + e('LINE', 10, 0, 20, 5, 11, 10, 21, 5));
  const a = run(text);
  assert.equal(a.contours.length, 1);
  assert.equal(a.contours[0].closed, true);
  assert.ok(close(a.contours[0].area, 50));
  assert.ok(close(a.cutLength, 30));
  assert.equal(a.pierces, 1);
});

test('Lücke: offen bei Standardtoleranz, geschlossen bei größerer Toleranz', () => {
  const text = doc(
    e('LINE', 10, 0, 20, 0, 11, 10, 21, 0) + e('LINE', 10, 10, 20, 0, 11, 10, 21, 5)
    + e('LINE', 10, 10, 20, 5, 11, 0, 21, 5) + e('LINE', 10, 0, 20, 5, 11, 0, 21, 0.3));
  const strict = run(text);
  assert.equal(strict.openCount, 1);
  assert.equal(strict.openEnds.length, 2);
  assert.equal(strict.netArea, 0);
  const loose = run(text, { tol: 0.5 });
  assert.equal(loose.openCount, 0);
  assert.ok(close(loose.netArea, 50, 1e-9), String(loose.netArea));
});

test('exakte Duplikate (auch gegenläufig) und Null-Längen werden entfernt und gezählt', () => {
  const text = doc(rectLines(0, 0, 10, 5)
    + e('LINE', 10, 10, 20, 0, 11, 0, 21, 0)       // gegenläufiges Duplikat der Unterkante
    + e('CIRCLE', 10, 5, 20, 2.5, 40, 1) + e('CIRCLE', 10, 5, 20, 2.5, 40, 1)
    + e('LINE', 10, 3, 20, 3, 11, 3, 21, 3));
  const a = run(text);
  assert.equal(a.removed.duplicates, 2);
  assert.equal(a.removed.zeroLength, 1);
  assert.equal(a.pierces, 2);
  assert.ok(close(a.cutLength, 30 + 2 * PI));
});

test('zwei Bögen mit gleichen Endpunkten (oberer und unterer Halbkreis) sind kein Duplikat', () => {
  const text = doc(e('ARC', 10, 0, 20, 0, 40, 5, 50, 0, 51, 180) + e('ARC', 10, 0, 20, 0, 40, 5, 50, 180, 51, 360));
  const a = run(text);
  assert.equal(a.removed.duplicates, 0);
  assert.equal(a.contours.length, 1);
  assert.equal(a.contours[0].closed, true);
  assert.ok(close(a.netArea, PI * 25, 1e-9));
});

// --- Verschachtelung ----------------------------------------------------------------------

test('Insel im Loch: Fläche = außen − Loch + Insel, Rollen wechseln je Tiefe', () => {
  const text = doc(rectLines(0, 0, 100, 100) + e('CIRCLE', 10, 50, 20, 50, 40, 30) + rectLines(45, 45, 10, 10));
  const a = run(text);
  assert.ok(close(a.netArea, 10000 - PI * 900 + 100, 1e-6));
  assert.deepEqual(a.contours.map((c) => c.role).sort(), ['inner', 'outer', 'outer']);
  assert.equal(a.outerCount, 2);
});

test('zwei getrennte Teile in einer Datei: zwei Außenkonturen', () => {
  const a = run(doc(rectLines(0, 0, 10, 10) + rectLines(20, 0, 10, 10)));
  assert.equal(a.outerCount, 2);
  assert.ok(close(a.netArea, 200));
  assert.ok(close(a.bbox.w, 30) && close(a.bbox.h, 10));
});

// --- Abmessungen --------------------------------------------------------------------------

test('Bounding-Box eines Bogens berücksichtigt den Scheitel, nicht nur die Endpunkte', () => {
  const a = run(doc(e('ARC', 10, 0, 20, 0, 40, 10, 50, 45, 51, 135)));
  assert.ok(close(a.bbox.maxY, 10) && close(a.bbox.minY, 10 * Math.SQRT1_2));
  assert.ok(close(a.bbox.w, 2 * 10 * Math.SQRT1_2));
});

test('kleinstes umschließendes Rechteck eines um 30° gedrehten Rechtecks 40 × 10', () => {
  const c = Math.cos(PI / 6); const s = Math.sin(PI / 6);
  const pts = [[0, 0], [40, 0], [40, 10], [0, 10], [20, 5]].map(([x, y]) => [x * c - y * s, x * s + y * c]);
  const r = minAreaRect(pts);
  assert.ok(close(r.w, 40, 1e-9) && close(r.h, 10, 1e-9), JSON.stringify(r));
});

test('analyse liefert das kleinste umschließende Rechteck (schräg gezeichnetes Teil)', () => {
  const c = Math.cos(PI / 4); const s = Math.sin(PI / 4);
  const P = [[0, 0], [60, 0], [60, 20], [0, 20]].map(([x, y]) => [x * c - y * s, x * s + y * c]);
  const lines = P.map((p, i) => { const q = P[(i + 1) % 4]; return e('LINE', 10, p[0], 20, p[1], 11, q[0], 21, q[1]); }).join('');
  const a = run(doc(lines));
  assert.ok(close(a.rect.w, 60, 1e-6) && close(a.rect.h, 20, 1e-6), JSON.stringify(a.rect));
  assert.ok(a.bbox.w > 56 && a.bbox.h > 56, 'achsparallele Box ist deutlich größer');
});

// --- Layer und Sonderfälle ----------------------------------------------------------------

test('layerStats zählt Elemente und Länge je Layer', () => {
  const { prims } = flatten(parseDxf(sample('halteblech')));
  const stats = layerStats(prims);
  const hilfs = stats.find((l) => l.name === 'HILFSLINIE');
  assert.equal(hilfs.count, 1);
  assert.ok(close(hilfs.length, 170));
  assert.ok(stats.find((l) => l.name === '0').count > 10);
});

test('keine Geometrie: leeres Ergebnis ohne Absturz', () => {
  const a = run(doc(e('TEXT', 10, 0, 20, 0, 1, 'nur Text')));
  assert.equal(a.pierces, 0);
  assert.equal(a.cutLength, 0);
  assert.equal(a.bbox, null);
  assert.equal(a.rect, null);
  assert.equal(a.netArea, 0);
});

test('Kontur im Uhrzeigersinn: Fläche bleibt positiv', () => {
  const text = doc(e('LWPOLYLINE', 90, 4, 70, 1, 10, 0, 20, 0, 10, 0, 20, 5, 10, 10, 20, 5, 10, 10, 20, 0));
  assert.ok(close(run(text).netArea, 50));
});
