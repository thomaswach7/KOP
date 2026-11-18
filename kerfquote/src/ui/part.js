// Eine Angebotsposition: DXF-Datei + Kalkulationsparameter + abgeleitete Geometrie.
// Reine Logik ohne DOM, damit sie in Node getestet werden kann.

import { parseDxf } from '../dxf/parse.js';
import { flatten } from '../dxf/flatten.js';
import { analyze, layerStats, guessIgnoredLayers } from '../geom/analyze.js';
import { priceLine, quantityBreaks, featureWarnings, roundTo } from '../cost/model.js';

let nextId = 1;

export function cleanName(fileName) {
  const base = String(fileName).trim().split(/[\\/]/).pop().replace(/\.dxf$/i, '').trim();
  return (base || 'Teil').slice(0, 120);
}

const nearestThickness = (material, t) =>
  material.thicknesses.reduce((best, row) => (Math.abs(row.t - t) < Math.abs(best.t - t) ? row : best)).t;

/** Stellt sicher, dass Material und Dicke der Position in den aktuellen Einstellungen existieren. */
export function normalizePart(part, settings) {
  let material = settings.materials.find((m) => m.id === part.materialId);
  if (!material) {
    material = settings.materials[0];
    part.materialId = material.id;
  }
  if (!material.thicknesses.some((row) => row.t === part.thickness)) {
    part.thickness = nearestThickness(material, part.thickness ?? 3);
  }
  return material;
}

/** Berechnet Geometrie und Analyse neu (nach Änderung von Einheit, Toleranz oder Layern). */
export function refreshGeometry(part, settings, initial = false) {
  part.flat = flatten(part.dxf, { units: part.units, defaultUnit: settings.defaultUnit });
  part.layers = layerStats(part.flat.prims);
  if (initial) {
    const guess = guessIgnoredLayers(part.layers.map((l) => l.name));
    part.ignoreLayers = guess.length < part.layers.length ? guess : [];
  }
  part.analysis = analyze(part.flat.prims, { tol: part.tol, ignoreLayers: part.ignoreLayers });
}

/**
 * @param {string} fileName
 * @param {string} text DXF-Inhalt (wirft DxfError bei unlesbaren Dateien)
 * @param {object} settings
 * @param {{materialId?: string, thickness?: number}} [defaults] zuletzt verwendete Werte
 */
export function createPart(fileName, text, settings, defaults = {}) {
  const part = {
    id: nextId++,
    name: cleanName(fileName),
    dxf: parseDxf(text),
    units: 'auto',
    tol: 0.05,
    ignoreLayers: [],
    materialId: defaults.materialId,
    thickness: defaults.thickness ?? 3,
    qty: 1,
    bends: 0,
    extra: 0,
  };
  normalizePart(part, settings);
  refreshGeometry(part, settings, true);
  return part;
}

/** Preis, Staffel und Hinweise einer Position. */
export function pricePart(part, settings) {
  const material = normalizePart(part, settings);
  const a = part.analysis;
  const price = priceLine(a, part, material, settings);
  const breaks = quantityBreaks(a, part, material, settings, settings.quantities);
  const warnings = [];
  const add = (level, key, vars) => warnings.push({ level, key, vars });
  const flags = featureWarnings(a, part.thickness);

  if (a.pierces === 0) add('warn', 'warn.none');
  if (flags.includes('openContours')) add('warn', 'warn.open', { n: a.openCount });
  if (flags.includes('smallFeature')) add('warn', 'warn.small', { size: roundTo(a.minInnerSize, 2), t: part.thickness });
  if (part.flat.notes.missingBlocks > 0) add('warn', 'warn.blocks', { n: part.flat.notes.missingBlocks });
  if (warnings.length === 0) add('ok', 'warn.ok');
  if (a.outerCount > 1) add('info', 'warn.multi', { n: a.outerCount });
  if (a.removed.duplicates > 0) add('info', 'warn.duplicates', { n: a.removed.duplicates });
  if (a.removed.zeroLength > 0) add('info', 'warn.zero', { n: a.removed.zeroLength });
  if (part.flat.notes.fitSplines > 0) add('info', 'warn.fit', { n: part.flat.notes.fitSplines });
  if (part.flat.unit.source === 'assumed') add('info', 'warn.unitAssumed', { unit: part.flat.unit.name });
  const ignored = Object.entries(part.flat.ignored).map(([type, n]) => `${n}× ${type}`);
  if (ignored.length) add('info', 'warn.ignored', { list: ignored.join(', ') });
  if (part.flat.notes.paperSpace > 0) add('info', 'warn.paper', { n: part.flat.notes.paperSpace });

  return { material, price, breaks, warnings };
}
