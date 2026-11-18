// DXF-Parser (ASCII-DXF, R12 bis aktuell). Liest nur, was für 2D-Zuschnitte zählt:
// HEADER-Einheiten, BLOCKS und ENTITIES. Keine Abhängigkeiten, läuft in Browser und Node.

export class DxfError extends Error {
  /** @param {'empty'|'binary'|'invalid'} code */
  constructor(code, message) {
    super(message);
    this.name = 'DxfError';
    this.code = code;
  }
}

const num = (v) => {
  const n = Number.parseFloat(v);
  return Number.isFinite(n) ? n : 0;
};
const int = (v) => Math.trunc(num(v));

/** Zerlegt den Text in Gruppencode/Wert-Paare. */
function tokenize(text) {
  const lines = text.replace(/^\uFEFF/, '').replace(/\s+$/, '').split(/\r\n|\r|\n/);
  const codes = [];
  const values = [];
  for (let i = 0; i + 1 < lines.length; i += 2) {
    const raw = lines[i].trim();
    const code = Number(raw);
    if (raw === '' || !Number.isInteger(code)) {
      throw new DxfError('invalid', `Zeile ${i + 1}: Gruppencode erwartet, gefunden "${raw.slice(0, 20)}"`);
    }
    codes.push(code);
    values.push(lines[i + 1].trim());
  }
  return { codes, values };
}

function buildEntity(type, codes, values, from, to) {
  const ent = { type, layer: '0', paperSpace: false, extZ: 1 };
  for (let i = from; i < to; i++) {
    const c = codes[i];
    if (c === 8) ent.layer = values[i];
    else if (c === 67) ent.paperSpace = int(values[i]) === 1;
    else if (c === 230) ent.extZ = num(values[i]) < 0 ? -1 : 1;
  }
  const first = (code, fallback = 0) => {
    for (let i = from; i < to; i++) if (codes[i] === code) return num(values[i]);
    return fallback;
  };
  const all = (code) => {
    const out = [];
    for (let i = from; i < to; i++) if (codes[i] === code) out.push(num(values[i]));
    return out;
  };
  /** Punktlisten: Code cx eröffnet einen Punkt, cy ergänzt ihn. */
  const points = (cx, cy) => {
    const out = [];
    for (let i = from; i < to; i++) {
      if (codes[i] === cx) out.push({ x: num(values[i]), y: 0 });
      else if (codes[i] === cy && out.length) out[out.length - 1].y = num(values[i]);
    }
    return out;
  };

  switch (type) {
    case 'LINE':
      ent.x1 = first(10); ent.y1 = first(20); ent.x2 = first(11); ent.y2 = first(21);
      break;
    case 'CIRCLE':
      ent.cx = first(10); ent.cy = first(20); ent.r = first(40);
      break;
    case 'ARC':
      ent.cx = first(10); ent.cy = first(20); ent.r = first(40);
      ent.a0 = first(50); ent.a1 = first(51);
      break;
    case 'LWPOLYLINE': {
      ent.closed = (int(first(70)) & 1) === 1;
      ent.vertices = [];
      for (let i = from; i < to; i++) {
        const c = codes[i];
        const last = ent.vertices[ent.vertices.length - 1];
        if (c === 10) ent.vertices.push({ x: num(values[i]), y: 0, bulge: 0 });
        else if (c === 20 && last) last.y = num(values[i]);
        else if (c === 42 && last) last.bulge = num(values[i]);
      }
      break;
    }
    case 'POLYLINE': {
      const flags = int(first(70));
      ent.closed = (flags & 1) === 1;
      ent.mesh = (flags & (16 | 64)) !== 0;
      ent.vertices = [];
      break;
    }
    case 'VERTEX':
      ent.x = first(10); ent.y = first(20); ent.bulge = first(42); ent.flags = int(first(70));
      break;
    case 'ELLIPSE':
      ent.cx = first(10); ent.cy = first(20); ent.mx = first(11); ent.my = first(21);
      ent.ratio = first(40, 1); ent.t0 = first(41, 0); ent.t1 = first(42, 2 * Math.PI);
      break;
    case 'SPLINE':
      ent.closed = (int(first(70)) & 1) === 1;
      ent.degree = int(first(71, 3));
      ent.knots = all(40);
      ent.ctrl = points(10, 20);
      ent.weights = all(41);
      ent.fit = points(11, 21);
      break;
    case 'INSERT': {
      for (let i = from; i < to; i++) if (codes[i] === 2) { ent.name = values[i]; break; }
      ent.name ??= '';
      ent.x = first(10); ent.y = first(20);
      ent.sx = first(41, 1); ent.sy = first(42, 1); ent.rot = first(50);
      ent.cols = Math.max(1, int(first(70, 1))); ent.rows = Math.max(1, int(first(71, 1)));
      ent.dx = first(44); ent.dy = first(45);
      break;
    }
    default:
      break;
  }
  return ent;
}

/**
 * Liest Entitäten ab Index i bis zum Endmarker (ENDSEC bzw. ENDBLK).
 * @returns {{entities: object[], next: number}}
 */
function readEntities(codes, values, i, endMarker) {
  const entities = [];
  let openPolyline = null;
  const n = codes.length;
  while (i < n) {
    if (codes[i] !== 0) { i++; continue; }
    const type = values[i].toUpperCase();
    if (type === endMarker || type === 'ENDSEC' || type === 'EOF') break;
    let end = i + 1;
    while (end < n && codes[end] !== 0) end++;
    const ent = buildEntity(type, codes, values, i + 1, end);
    i = end;
    if (type === 'POLYLINE') {
      openPolyline = ent;
      entities.push(ent);
    } else if (type === 'VERTEX') {
      // Flag 16 = Kontrollpunkt eines Spline-Rahmens: gehört nicht zur sichtbaren Kurve.
      if (openPolyline && (ent.flags & 16) === 0) {
        openPolyline.vertices.push({ x: ent.x, y: ent.y, bulge: ent.bulge });
      }
    } else if (type === 'SEQEND') {
      openPolyline = null;
    } else {
      openPolyline = null;
      entities.push(ent);
    }
  }
  return { entities, next: i };
}

/**
 * @param {string} text Inhalt einer ASCII-DXF-Datei
 * @returns {{header: {insunits: number|null, measurement: number|null, acadver: string|null},
 *            blocks: Map<string, {base: {x:number,y:number}, entities: object[]}>, entities: object[]}}
 */
export function parseDxf(text) {
  if (typeof text !== 'string' || text.trim() === '') {
    throw new DxfError('empty', 'Die Datei ist leer.');
  }
  if (text.startsWith('AutoCAD Binary DXF')) {
    throw new DxfError('binary', 'Binäres DXF wird nicht unterstützt. Bitte als ASCII-DXF speichern.');
  }
  const { codes, values } = tokenize(text);
  const header = { insunits: null, measurement: null, acadver: null };
  const blocks = new Map();
  let entities = [];
  let sawEntities = false;
  const n = codes.length;
  let i = 0;
  while (i < n) {
    if (codes[i] !== 0 || values[i].toUpperCase() !== 'SECTION') { i++; continue; }
    const section = i + 1 < n && codes[i + 1] === 2 ? values[i + 1].toUpperCase() : '';
    i += 2;
    if (section === 'HEADER') {
      for (; i < n && !(codes[i] === 0 && values[i].toUpperCase() === 'ENDSEC'); i++) {
        if (codes[i] !== 9 || i + 1 >= n) continue;
        const name = values[i].toUpperCase();
        if (name === '$INSUNITS') header.insunits = int(values[i + 1]);
        else if (name === '$MEASUREMENT') header.measurement = int(values[i + 1]);
        else if (name === '$ACADVER') header.acadver = values[i + 1];
      }
    } else if (section === 'BLOCKS') {
      while (i < n && !(codes[i] === 0 && values[i].toUpperCase() === 'ENDSEC')) {
        if (codes[i] === 0 && values[i].toUpperCase() === 'BLOCK') {
          let end = i + 1;
          while (end < n && codes[end] !== 0) end++;
          let name = '';
          const base = { x: 0, y: 0 };
          for (let k = i + 1; k < end; k++) {
            if (codes[k] === 2) name = values[k];
            else if (codes[k] === 10) base.x = num(values[k]);
            else if (codes[k] === 20) base.y = num(values[k]);
          }
          const res = readEntities(codes, values, end, 'ENDBLK');
          blocks.set(name, { base, entities: res.entities });
          i = res.next;
        }
        if (i < n && !(codes[i] === 0 && values[i].toUpperCase() === 'ENDSEC')) i++;
      }
    } else if (section === 'ENTITIES') {
      sawEntities = true;
      const res = readEntities(codes, values, i, 'ENDSEC');
      entities = entities.concat(res.entities);
      i = res.next;
    }
  }
  if (!sawEntities) {
    throw new DxfError('invalid', 'Keine ENTITIES-Sektion gefunden – ist das eine DXF-Datei?');
  }
  return { header, blocks, entities };
}
