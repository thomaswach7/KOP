// Wandelt geparste DXF-Entitäten in einfache Schnittprimitive um: Linien ('L') und
// Kreisbögen ('A'), alle in Millimetern und im Weltkoordinatensystem.
// Blöcke werden aufgelöst, Ellipsen und Splines fein in Linien zerlegt.

const TAU = 2 * Math.PI;
const DEG = Math.PI / 180;
const MAX_BLOCK_DEPTH = 16;
/** relative Sehnenhöhe beim Zerlegen von Ellipsen/verzerrten Bögen (bezogen auf den Radius) */
const REL_SAGITTA = 1e-5;
const SPLINE_STEPS_PER_SPAN = 48;

const UNITS = {
  mm: 1, cm: 10, m: 1000, in: 25.4, ft: 304.8,
};
const INSUNITS = { 1: 'in', 2: 'ft', 4: 'mm', 5: 'cm', 6: 'm' };

/**
 * Bestimmt die Zeichnungseinheit.
 * @param {{insunits: number|null}} header
 * @param {'auto'|'mm'|'cm'|'m'|'in'|'ft'} override manuelle Wahl des Nutzers
 * @param {'mm'|'in'} fallback Standardeinheit, wenn die Datei keine Einheit nennt
 */
export function resolveUnits(header, override = 'auto', fallback = 'mm') {
  if (override !== 'auto' && UNITS[override]) {
    return { name: override, scale: UNITS[override], source: 'manual' };
  }
  const name = INSUNITS[header?.insunits];
  if (name) return { name, scale: UNITS[name], source: 'header' };
  const fb = UNITS[fallback] ? fallback : 'mm';
  return { name: fb, scale: UNITS[fb], source: 'assumed' };
}

const line = (x0, y0, x1, y1, layer) => ({ k: 'L', x0, y0, x1, y1, layer });

/** Bogen um (cx,cy) ab Winkel a0 (rad) mit vorzeichenbehaftetem Öffnungswinkel sw (CCW positiv). */
function arc(cx, cy, r, a0, sw, layer) {
  const a1 = a0 + sw;
  return {
    k: 'A', cx, cy, r, a0, sw, layer,
    x0: cx + r * Math.cos(a0), y0: cy + r * Math.sin(a0),
    x1: cx + r * Math.cos(a1), y1: cy + r * Math.sin(a1),
  };
}

export function primLength(p) {
  return p.k === 'L' ? Math.hypot(p.x1 - p.x0, p.y1 - p.y0) : p.r * Math.abs(p.sw);
}

/** Stützpunkte eines Bogens (inkl. Start und Ende) mit Sehnenhöhe ≤ tol. */
export function arcPoints(p, tol) {
  const ratio = Math.min(Math.max(tol / p.r, 1e-9), 0.5);
  const step = 2 * Math.acos(1 - ratio);
  const n = Math.min(4096, Math.max(2, Math.ceil(Math.abs(p.sw) / step)));
  const pts = [];
  for (let i = 0; i <= n; i++) {
    const a = p.a0 + (p.sw * i) / n;
    pts.push([p.cx + p.r * Math.cos(a), p.cy + p.r * Math.sin(a)]);
  }
  return pts;
}

// --- affine Abbildungen: [a, b, c, d, e, f] bildet (x, y) auf (a·x + c·y + e, b·x + d·y + f) ab

const IDENTITY = [1, 0, 0, 1, 0, 0];
const MIRROR_X = [-1, 0, 0, 1, 0, 0];

const mul = (m, n) => [
  m[0] * n[0] + m[2] * n[1], m[1] * n[0] + m[3] * n[1],
  m[0] * n[2] + m[2] * n[3], m[1] * n[2] + m[3] * n[3],
  m[0] * n[4] + m[2] * n[5] + m[4], m[1] * n[4] + m[3] * n[5] + m[5],
];
const tx = (m, x, y) => [m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]];

function insertMatrix(ins, base, col, row) {
  const c = Math.cos(ins.rot * DEG);
  const s = Math.sin(ins.rot * DEG);
  const rotate = [c, s, -s, c, ins.x, ins.y];
  const offset = [1, 0, 0, 1, col * ins.dx, row * ins.dy];
  const scale = [ins.sx, 0, 0, ins.sy, 0, 0];
  const toBase = [1, 0, 0, 1, -base.x, -base.y];
  return mul(mul(mul(rotate, offset), scale), toBase);
}

function pushTransformed(out, p, m) {
  if (p.k === 'L') {
    const [x0, y0] = tx(m, p.x0, p.y0);
    const [x1, y1] = tx(m, p.x1, p.y1);
    // Linien mit Länge 0 bleiben erhalten: die Analyse zählt sie als Zeichnungsfehler
    out.push(line(x0, y0, x1, y1, p.layer));
    return;
  }
  const sa = m[0] * m[0] + m[1] * m[1];
  const sc = m[2] * m[2] + m[3] * m[3];
  const dot = m[0] * m[2] + m[1] * m[3];
  const big = Math.max(sa, sc);
  const similar = Math.abs(sa - sc) <= 1e-9 * big && Math.abs(dot) <= 1e-9 * big;
  if (similar) {
    const [cx, cy] = tx(m, p.cx, p.cy);
    const [sx, sy] = tx(m, p.x0, p.y0);
    const det = m[0] * m[3] - m[1] * m[2];
    out.push(arc(cx, cy, p.r * Math.sqrt(sa), Math.atan2(sy - cy, sx - cx), det < 0 ? -p.sw : p.sw, p.layer));
    return;
  }
  // ungleichmäßige Skalierung: Bogen wird zum Ellipsenbogen → fein zerlegen
  const pts = arcPoints(p, p.r * REL_SAGITTA).map(([x, y]) => tx(m, x, y));
  for (let i = 1; i < pts.length; i++) {
    out.push(line(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1], p.layer));
  }
}

function polylinePrims(vertices, closed, layer) {
  const out = [];
  const n = vertices.length;
  const count = closed ? n : n - 1;
  for (let i = 0; i < count; i++) {
    const a = vertices[i];
    const b = vertices[(i + 1) % n];
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    if (dx === 0 && dy === 0) continue;
    const bulge = a.bulge || 0;
    if (Math.abs(bulge) < 1e-12) {
      out.push(line(a.x, a.y, b.x, b.y, layer));
      continue;
    }
    // Bulge = tan(Öffnungswinkel / 4), positiv = gegen den Uhrzeigersinn
    const k = (1 - bulge * bulge) / (4 * bulge);
    const cx = (a.x + b.x) / 2 - dy * k;
    const cy = (a.y + b.y) / 2 + dx * k;
    const r = Math.hypot(a.x - cx, a.y - cy);
    const p = arc(cx, cy, r, Math.atan2(a.y - cy, a.x - cx), 4 * Math.atan(bulge), layer);
    // Endpunkte exakt auf die Scheitelpunkte legen (vermeidet Rundungslücken beim Verketten)
    p.x0 = a.x; p.y0 = a.y; p.x1 = b.x; p.y1 = b.y;
    out.push(p);
  }
  return out;
}

function pointsToLines(pts, layer) {
  const out = [];
  for (let i = 1; i < pts.length; i++) {
    const [x0, y0] = pts[i - 1];
    const [x1, y1] = pts[i];
    if (x0 !== x1 || y0 !== y1) out.push(line(x0, y0, x1, y1, layer));
  }
  return out;
}

function ellipsePrims(e, layer) {
  const a = Math.hypot(e.mx, e.my);
  if (a === 0) return [];
  // Nebenachse = N × Hauptachse · Verhältnis; bei Extrusion -Z läuft der Parameter andersherum
  const nx = -e.my * e.ratio * e.extZ;
  const ny = e.mx * e.ratio * e.extZ;
  let span = e.t1 - e.t0;
  while (span <= 1e-12) span += TAU;
  if (span > TAU) span = TAU;
  const step = 2 * Math.acos(1 - REL_SAGITTA);
  const n = Math.min(4096, Math.max(16, Math.ceil(span / step)));
  const pts = [];
  for (let i = 0; i <= n; i++) {
    const t = e.t0 + (span * i) / n;
    pts.push([e.cx + Math.cos(t) * e.mx + Math.sin(t) * nx, e.cy + Math.cos(t) * e.my + Math.sin(t) * ny]);
  }
  if (span === TAU) pts[n] = pts[0].slice();
  return pointsToLines(pts, layer);
}

/** De-Boor-Auswertung eines (rationalen) B-Splines im Knotenintervall k. */
function deBoor(k, u, knots, pts, p) {
  const d = [];
  for (let j = 0; j <= p; j++) d.push(pts[j + k - p].slice());
  for (let r = 1; r <= p; r++) {
    for (let j = p; j >= r; j--) {
      const i = j + k - p;
      const denom = knots[i + p - r + 1] - knots[i];
      const alpha = denom === 0 ? 0 : (u - knots[i]) / denom;
      for (let c = 0; c < 3; c++) d[j][c] = (1 - alpha) * d[j - 1][c] + alpha * d[j][c];
    }
  }
  return d[p];
}

function splinePrims(s, layer, notes) {
  const n = s.ctrl.length;
  const p = s.degree;
  if (n >= 2 && p >= 1 && n > p && s.knots.length === n + p + 1) {
    const rational = s.weights.length === n;
    const pts = s.ctrl.map((c, i) => {
      const w = rational ? s.weights[i] : 1;
      return [c.x * w, c.y * w, w];
    });
    const out = [];
    // gültiger Parameterbereich: [u_p, u_n]; gilt für geklemmte wie für periodische Knotenvektoren
    for (let k = p; k < n; k++) {
      const u0 = s.knots[k];
      const u1 = s.knots[k + 1];
      if (!(u1 > u0)) continue;
      const startAt = out.length ? 1 : 0;
      for (let i = startAt; i <= SPLINE_STEPS_PER_SPAN; i++) {
        const u = i === SPLINE_STEPS_PER_SPAN ? u1 : u0 + ((u1 - u0) * i) / SPLINE_STEPS_PER_SPAN;
        // am rechten Rand im selben Intervall bleiben (u = u1 ist dort noch definiert)
        const q = deBoor(k, u, s.knots, pts, p);
        out.push([q[0] / q[2], q[1] / q[2]]);
      }
    }
    if (out.length >= 2) return pointsToLines(out, layer);
  }
  if (s.fit.length >= 2) {
    notes.fitSplines++;
    const pts = s.fit.map((f) => [f.x, f.y]);
    if (s.closed) pts.push(pts[0].slice());
    return pointsToLines(pts, layer);
  }
  if (n >= 2) {
    notes.fitSplines++;
    return pointsToLines(s.ctrl.map((c) => [c.x, c.y]), layer);
  }
  return [];
}

/**
 * @param {ReturnType<import('./parse.js').parseDxf>} dxf
 * @param {{units?: string, defaultUnit?: 'mm'|'in'}} [opts]
 * @returns {{prims: object[], ignored: Record<string, number>, unit: {name:string, scale:number, source:string},
 *            notes: {fitSplines: number, missingBlocks: number, paperSpace: number}}}
 */
export function flatten(dxf, opts = {}) {
  const unit = resolveUnits(dxf.header, opts.units ?? 'auto', opts.defaultUnit ?? 'mm');
  const prims = [];
  const ignored = {};
  const notes = { fitSplines: 0, missingBlocks: 0, paperSpace: 0 };

  const emit = (ent, m, insertLayer, depth) => {
    if (ent.paperSpace) { notes.paperSpace++; return; }
    const layer = ent.layer === '0' && insertLayer !== null ? insertLayer : ent.layer;
    // OCS-Entitäten mit Extrusion (0,0,-1) liegen an der Y-Achse gespiegelt im WCS
    const ocs = ent.extZ < 0 ? mul(m, MIRROR_X) : m;
    let local = null;
    let matrix = m;
    switch (ent.type) {
      case 'LINE':
        local = [line(ent.x1, ent.y1, ent.x2, ent.y2, layer)];
        break;
      case 'CIRCLE':
        if (ent.r > 0) local = [arc(ent.cx, ent.cy, ent.r, 0, TAU, layer)];
        matrix = ocs;
        break;
      case 'ARC': {
        if (ent.r > 0) {
          let sweep = (ent.a1 - ent.a0) % 360;
          if (sweep <= 0) sweep += 360;
          local = [arc(ent.cx, ent.cy, ent.r, ent.a0 * DEG, sweep * DEG, layer)];
        }
        matrix = ocs;
        break;
      }
      case 'LWPOLYLINE':
        local = polylinePrims(ent.vertices, ent.closed, layer);
        matrix = ocs;
        break;
      case 'POLYLINE':
        if (!ent.mesh) local = polylinePrims(ent.vertices, ent.closed, layer);
        matrix = ocs;
        break;
      case 'ELLIPSE':
        local = ellipsePrims(ent, layer);
        break;
      case 'SPLINE':
        local = splinePrims(ent, layer, notes);
        break;
      case 'INSERT': {
        const block = dxf.blocks.get(ent.name) ?? dxf.blocks.get(String(ent.name).toUpperCase());
        if (!block) { notes.missingBlocks++; return; }
        if (depth >= MAX_BLOCK_DEPTH) return;
        for (let row = 0; row < ent.rows; row++) {
          for (let col = 0; col < ent.cols; col++) {
            const mm = mul(ocs, insertMatrix(ent, block.base, col, row));
            for (const child of block.entities) emit(child, mm, layer, depth + 1);
          }
        }
        return;
      }
      default:
        ignored[ent.type] = (ignored[ent.type] ?? 0) + 1;
        return;
    }
    if (local) for (const p of local) pushTransformed(prims, p, matrix);
  };

  const root = [unit.scale, 0, 0, unit.scale, 0, 0];
  for (const ent of dxf.entities) emit(ent, unit.scale === 1 ? IDENTITY : root, null, 0);
  return { prims, ignored, unit, notes };
}
