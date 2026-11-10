// Konturanalyse: verkettet Schnittprimitive zu Konturen, erkennt offene Konturen und
// Duplikate und berechnet Schnittlänge, Einstiche, Fläche und Abmessungen.

import { primLength, arcPoints } from '../dxf/flatten.js';

const TAU = 2 * Math.PI;
const HALF_PI = Math.PI / 2;
const TESS_TOL = 0.01; // mm Sehnenhöhe für Punkt-in-Polygon und Hülle
const KEY_GRID = 1e-4; // mm Raster zum Erkennen exakter Duplikate
const ZERO_LENGTH = 1e-9;

const q = (v) => Math.round(v / KEY_GRID);

function reversePrim(p) {
  if (p.k === 'L') return { ...p, x0: p.x1, y0: p.y1, x1: p.x0, y1: p.y0 };
  return { ...p, a0: p.a0 + p.sw, sw: -p.sw, x0: p.x1, y0: p.y1, x1: p.x0, y1: p.y0 };
}

const isFullCircle = (p) => p.k === 'A' && Math.abs(p.sw) >= TAU - 1e-9;

function duplicateKey(p) {
  if (isFullCircle(p)) return `C|${q(p.cx)},${q(p.cy)},${q(p.r)}`;
  let a = `${q(p.x0)},${q(p.y0)}`;
  let b = `${q(p.x1)},${q(p.y1)}`;
  if (a > b) [a, b] = [b, a];
  if (p.k === 'L') return `L|${a}|${b}`;
  const mid = p.a0 + p.sw / 2;
  return `A|${a}|${b}|${q(p.cx + p.r * Math.cos(mid))},${q(p.cy + p.r * Math.sin(mid))}`;
}

function extend(box, x, y) {
  if (x < box[0]) box[0] = x;
  if (y < box[1]) box[1] = y;
  if (x > box[2]) box[2] = x;
  if (y > box[3]) box[3] = y;
}

function primExtents(p, box) {
  extend(box, p.x0, p.y0);
  extend(box, p.x1, p.y1);
  if (p.k !== 'A') return;
  const lo = p.sw >= 0 ? p.a0 : p.a0 + p.sw;
  const hi = lo + Math.abs(p.sw);
  for (let k = Math.ceil(lo / HALF_PI - 1e-12); k * HALF_PI <= hi + 1e-12; k++) {
    extend(box, p.cx + p.r * Math.cos(k * HALF_PI), p.cy + p.r * Math.sin(k * HALF_PI));
  }
}

function pointInPolygon(x, y, pts) {
  let inside = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const xi = pts[i][0];
    const yi = pts[i][1];
    const xj = pts[j][0];
    const yj = pts[j][1];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

/** Kleinstes umschließendes Rechteck (beliebig gedreht) einer Punktmenge. */
export function minAreaRect(points) {
  if (points.length === 0) return null;
  const pts = points.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lower = [];
  for (const p of pts) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) lower.pop();
    lower.push(p);
  }
  const upper = [];
  for (let i = pts.length - 1; i >= 0; i--) {
    const p = pts[i];
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) upper.pop();
    upper.push(p);
  }
  const hull = lower.slice(0, -1).concat(upper.slice(0, -1));
  if (hull.length < 3) {
    const a = pts[0];
    const b = pts[pts.length - 1];
    return { w: Math.hypot(b[0] - a[0], b[1] - a[1]), h: 0, angle: Math.atan2(b[1] - a[1], b[0] - a[0]) };
  }
  let best = null;
  for (let i = 0; i < hull.length; i++) {
    const a = hull[i];
    const b = hull[(i + 1) % hull.length];
    const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (len === 0) continue;
    const ux = (b[0] - a[0]) / len;
    const uy = (b[1] - a[1]) / len;
    let minU = Infinity;
    let maxU = -Infinity;
    let maxN = 0; // alle Hüllpunkte liegen links der Kante (n ≥ 0)
    for (const p of hull) {
      const du = (p[0] - a[0]) * ux + (p[1] - a[1]) * uy;
      const dn = -(p[0] - a[0]) * uy + (p[1] - a[1]) * ux;
      if (du < minU) minU = du;
      if (du > maxU) maxU = du;
      if (dn > maxN) maxN = dn;
    }
    const area = (maxU - minU) * maxN;
    if (!best || area < best.area) best = { area, a: maxU - minU, b: maxN, angle: Math.atan2(uy, ux) };
  }
  return { w: Math.max(best.a, best.b), h: Math.min(best.a, best.b), angle: best.angle };
}

/** Elemente und Länge je Layer (für die Layer-Auswahl in der Oberfläche). */
export function layerStats(prims) {
  const map = new Map();
  for (const p of prims) {
    const s = map.get(p.layer) ?? { name: p.layer, count: 0, length: 0 };
    s.count++;
    s.length += primLength(p);
    map.set(p.layer, s);
  }
  return [...map.values()].sort((a, b) => a.name.localeCompare(b.name));
}

const NON_CUT_LAYER = new RegExp([
  'bema(ss|ß)ung', '^dim', 'defpoints', 'text', 'hilfs', 'mittellini', '^cent(er|re)', 'schriftfeld',
  'rahmen', 'tit(le|el)', 'gravur', 'engrav', 'bieg', '^bend', 'annot', 'schraff', 'hatch',
].join('|'), 'i');

/** Layer, die dem Namen nach keine Schnittkontur sind (Bemaßung, Text, Biegelinien …). Nur ein Vorschlag. */
export function guessIgnoredLayers(names) {
  return names.filter((name) => NON_CUT_LAYER.test(name));
}

function chainPrims(items, tol) {
  const cell = Math.max(tol, 1e-6);
  const tol2 = tol * tol;
  const buckets = new Map();
  const cellKey = (ix, iy) => `${ix}:${iy}`;
  const put = (x, y, id) => {
    const k = cellKey(Math.floor(x / cell), Math.floor(y / cell));
    const list = buckets.get(k);
    if (list) list.push(id); else buckets.set(k, [id]);
  };
  items.forEach((p, i) => { put(p.x0, p.y0, 2 * i); put(p.x1, p.y1, 2 * i + 1); });
  const used = new Uint8Array(items.length);

  /** nächster freier Endpunkt innerhalb der Toleranz; Rückgabe 2·Index + Ende oder -1 */
  const nearest = (x, y) => {
    const ix = Math.floor(x / cell);
    const iy = Math.floor(y / cell);
    let best = -1;
    let bestD = tol2;
    for (let dx = -1; dx <= 1; dx++) {
      for (let dy = -1; dy <= 1; dy++) {
        const list = buckets.get(cellKey(ix + dx, iy + dy));
        if (!list) continue;
        for (const id of list) {
          const p = items[id >> 1];
          if (used[id >> 1]) continue;
          const px = id & 1 ? p.x1 : p.x0;
          const py = id & 1 ? p.y1 : p.y0;
          const d = (px - x) * (px - x) + (py - y) * (py - y);
          if (d <= bestD) { bestD = d; best = id; }
        }
      }
    }
    return best;
  };
  const meets = (a, b) => (a.x1 - b.x0) ** 2 + (a.y1 - b.y0) ** 2 <= tol2;

  const chains = [];
  for (let s = 0; s < items.length; s++) {
    if (used[s]) continue;
    used[s] = 1;
    if (isFullCircle(items[s])) { chains.push({ prims: [items[s]], closed: true }); continue; }
    const fwd = [items[s]];
    const back = []; // rückwärts angefügte Elemente, in umgekehrter Reihenfolge
    let closed = false;
    for (;;) {
      const tail = fwd[fwd.length - 1];
      if (fwd.length >= 2 && meets(tail, fwd[0])) { closed = true; break; }
      const hit = nearest(tail.x1, tail.y1);
      if (hit < 0) break;
      used[hit >> 1] = 1;
      fwd.push(hit & 1 ? reversePrim(items[hit >> 1]) : items[hit >> 1]);
    }
    while (!closed) {
      const head = back.length ? back[back.length - 1] : fwd[0];
      const hit = nearest(head.x0, head.y0);
      if (hit < 0) break;
      used[hit >> 1] = 1;
      back.push(hit & 1 ? items[hit >> 1] : reversePrim(items[hit >> 1]));
      if (meets(fwd[fwd.length - 1], back[back.length - 1])) closed = true;
    }
    chains.push({ prims: back.reverse().concat(fwd), closed });
  }
  return chains;
}

/**
 * @param {object[]} prims Ergebnis von flatten()
 * @param {{tol?: number, ignoreLayers?: string[]}} [opts] tol = Lückentoleranz in mm
 */
export function analyze(prims, opts = {}) {
  const tol = opts.tol > 0 ? opts.tol : 0.05;
  const skip = new Set(opts.ignoreLayers ?? []);
  const removed = { duplicates: 0, zeroLength: 0 };
  const seen = new Set();
  const items = [];
  for (const p of prims) {
    if (skip.has(p.layer)) continue;
    if (primLength(p) <= ZERO_LENGTH) { removed.zeroLength++; continue; }
    const key = duplicateKey(p);
    if (seen.has(key)) { removed.duplicates++; continue; }
    seen.add(key);
    items.push(p);
  }

  const contours = chainPrims(items, tol).map((chain) => {
    const n = chain.prims.length;
    const box = [Infinity, Infinity, -Infinity, -Infinity];
    const points = [];
    let length = 0;
    let twiceArea = 0;
    chain.prims.forEach((p, i) => {
      length += primLength(p);
      primExtents(p, box);
      if (p.k === 'A') {
        const pts = arcPoints(p, TESS_TOL);
        for (let j = 0; j < pts.length - 1; j++) points.push(pts[j]);
        twiceArea += p.r * p.r * (p.sw - Math.sin(p.sw));
      } else {
        points.push([p.x0, p.y0]);
      }
      const next = chain.prims[(i + 1) % n];
      // Sehne des Elements plus (winzige) Lücke zum nächsten Element
      twiceArea += p.x0 * p.y1 - p.x1 * p.y0 + (p.x1 * next.y0 - next.x0 * p.y1);
    });
    if (!chain.closed) {
      const last = chain.prims[n - 1];
      points.push([last.x1, last.y1]);
    }
    return {
      closed: chain.closed,
      prims: chain.prims,
      length,
      area: chain.closed ? Math.abs(twiceArea) / 2 : 0,
      bbox: box,
      size: Math.min(box[2] - box[0], box[3] - box[1]),
      points,
      depth: 0,
      role: chain.closed ? 'outer' : 'open',
    };
  });

  // Verschachtelungstiefe: wie viele größere geschlossene Konturen umschließen diese?
  const closed = contours.filter((c) => c.closed).sort((a, b) => b.area - a.area);
  const EPS = 1e-9;
  closed.forEach((c, j) => {
    const [px, py] = c.points[0];
    for (let i = 0; i < j; i++) {
      const o = closed[i];
      if (c.bbox[0] < o.bbox[0] - EPS || c.bbox[1] < o.bbox[1] - EPS
        || c.bbox[2] > o.bbox[2] + EPS || c.bbox[3] > o.bbox[3] + EPS) continue;
      if (pointInPolygon(px, py, o.points)) c.depth++;
    }
    c.role = c.depth % 2 === 0 ? 'outer' : 'inner';
  });

  let cutLength = 0;
  let netArea = 0;
  let outerCount = 0;
  let openCount = 0;
  let minInnerSize = null;
  const openEnds = [];
  const total = [Infinity, Infinity, -Infinity, -Infinity];
  const hullPoints = [];
  for (const c of contours) {
    cutLength += c.length;
    extend(total, c.bbox[0], c.bbox[1]);
    extend(total, c.bbox[2], c.bbox[3]);
    if (c.role === 'outer') { netArea += c.area; outerCount++; }
    else if (c.role === 'inner') {
      netArea -= c.area;
      if (minInnerSize === null || c.size < minInnerSize) minInnerSize = c.size;
    } else {
      openCount++;
      const first = c.prims[0];
      const last = c.prims[c.prims.length - 1];
      openEnds.push([first.x0, first.y0], [last.x1, last.y1]);
    }
    if (c.depth === 0) for (const pt of c.points) hullPoints.push(pt);
  }

  const has = contours.length > 0;
  return {
    contours,
    cutLength,
    pierces: contours.length,
    closedCount: closed.length,
    openCount,
    outerCount,
    netArea: Math.max(0, netArea),
    bbox: has
      ? { minX: total[0], minY: total[1], maxX: total[2], maxY: total[3], w: total[2] - total[0], h: total[3] - total[1] }
      : null,
    rect: has ? minAreaRect(hullPoints) : null,
    minInnerSize,
    openEnds,
    removed,
    tol,
  };
}
