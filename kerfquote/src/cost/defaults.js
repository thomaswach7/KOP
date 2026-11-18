// Standardwerte und Validierung der Einstellungen.
// WICHTIG: Vorschübe, Einstechzeiten und Materialpreise sind Startwerte für einen
// 4-kW-Faserlaser und müssen auf die eigene Maschine und den eigenen Einkauf kalibriert werden.

const rows = (list) => list.map(([t, speed, pierce]) => ({ t, speed, pierce }));

export const DEFAULT_MATERIALS = [
  {
    id: 's235', name: 'S235 (Baustahl)', density: 7.85, pricePerKg: 1.2,
    thicknesses: rows([
      [1, 9000, 0.2], [1.5, 7500, 0.3], [2, 6500, 0.3], [3, 4200, 0.5], [4, 3500, 0.7], [5, 3200, 0.8],
      [6, 2800, 1], [8, 2300, 1.5], [10, 1800, 2], [12, 1500, 2.5], [15, 1100, 3.5], [20, 700, 5],
    ]),
  },
  {
    id: '1.4301', name: '1.4301 (Edelstahl)', density: 7.9, pricePerKg: 4,
    thicknesses: rows([
      [1, 20000, 0.1], [1.5, 14000, 0.2], [2, 10000, 0.2], [3, 6000, 0.4], [4, 4000, 0.6], [5, 2800, 0.8],
      [6, 2200, 1], [8, 1300, 1.5], [10, 800, 2.5], [12, 500, 3.5],
    ]),
  },
  {
    id: 'almg3', name: 'AlMg3 (Aluminium)', density: 2.66, pricePerKg: 5,
    thicknesses: rows([
      [1, 20000, 0.1], [1.5, 15000, 0.2], [2, 11000, 0.2], [3, 7000, 0.4], [4, 4500, 0.6], [5, 3200, 0.8],
      [6, 2500, 1], [8, 1500, 1.5], [10, 900, 2.5],
    ]),
  },
];

export const CURRENCIES = ['EUR', 'USD', 'CHF', 'GBP'];

export const DEFAULT_SETTINGS = {
  currency: 'EUR',
  vatPct: 19,
  machineRate: 120, // Maschinenstundensatz inkl. Bediener, Gas, Strom
  setupCost: 25, // Rüstkosten je Position
  markupPct: 25, // Zuschlag für Gemeinkosten und Gewinn
  partGap: 10, // mm Stegbreite / Zugabe um das umschließende Rechteck
  pricePerBend: 1.5,
  minOrder: 50, // Mindestauftragswert netto
  validityDays: 30,
  defaultUnit: 'mm',
  quotePrefix: 'A-',
  quantities: [1, 5, 10, 25, 50, 100],
  company: { name: '', address: '', logo: '', footer: '' },
  materials: DEFAULT_MATERIALS,
};

const LOGO_RE = /^data:image\/(png|jpeg|webp|gif|svg\+xml);base64,[A-Za-z0-9+/=]+$/;
const MAX_LOGO_CHARS = 400_000;

const isNum = (v, min, max) => typeof v === 'number' && Number.isFinite(v) && v >= min && v <= max;
const numOr = (v, min, max, fallback) => (isNum(v, min, max) ? v : fallback);
const strOr = (v, maxLen, fallback = '') => (typeof v === 'string' ? v.slice(0, maxLen) : fallback);

function sanitizeMaterial(m) {
  if (!m || typeof m !== 'object') return null;
  if (typeof m.id !== 'string' || !m.id.trim() || typeof m.name !== 'string' || !m.name.trim()) return null;
  if (!isNum(m.density, 0.01, 25) || !isNum(m.pricePerKg, 0, 100000) || !Array.isArray(m.thicknesses)) return null;
  const seen = new Set();
  const thicknesses = [];
  for (const r of m.thicknesses) {
    if (!r || !isNum(r.t, 0.01, 500) || !isNum(r.speed, 1, 1e6) || !isNum(r.pierce, 0, 600)) continue;
    if (seen.has(r.t)) continue;
    seen.add(r.t);
    thicknesses.push({ t: r.t, speed: r.speed, pierce: r.pierce });
  }
  if (thicknesses.length === 0) return null;
  thicknesses.sort((a, b) => a.t - b.t);
  return {
    id: m.id.trim().slice(0, 40), name: m.name.trim().slice(0, 60),
    density: m.density, pricePerKg: m.pricePerKg, thicknesses,
  };
}

/**
 * Prüft beliebige Eingaben (localStorage, importierte JSON-Datei) und liefert immer
 * vollständige, gültige Einstellungen. Ungültige Werte werden durch Standardwerte ersetzt.
 */
export function sanitizeSettings(input) {
  const src = input && typeof input === 'object' ? input : {};
  const d = DEFAULT_SETTINGS;
  const company = src.company && typeof src.company === 'object' ? src.company : {};
  const logo = typeof company.logo === 'string' && company.logo.length <= MAX_LOGO_CHARS && LOGO_RE.test(company.logo)
    ? company.logo : '';

  const ids = new Set();
  let materials = (Array.isArray(src.materials) ? src.materials : [])
    .map(sanitizeMaterial)
    .filter((m) => m && !ids.has(m.id) && ids.add(m.id));
  if (materials.length === 0) materials = d.materials.map(sanitizeMaterial);

  let quantities = [...new Set((Array.isArray(src.quantities) ? src.quantities : [])
    .filter((n) => Number.isInteger(n) && n >= 1 && n <= 1_000_000))]
    .sort((a, b) => a - b).slice(0, 8);
  if (quantities.length === 0) quantities = d.quantities.slice();

  return {
    currency: CURRENCIES.includes(src.currency) ? src.currency : d.currency,
    vatPct: numOr(src.vatPct, 0, 100, d.vatPct),
    machineRate: numOr(src.machineRate, 0, 100000, d.machineRate),
    setupCost: numOr(src.setupCost, 0, 100000, d.setupCost),
    markupPct: numOr(src.markupPct, 0, 1000, d.markupPct),
    partGap: numOr(src.partGap, 0, 1000, d.partGap),
    pricePerBend: numOr(src.pricePerBend, 0, 10000, d.pricePerBend),
    minOrder: numOr(src.minOrder, 0, 1e6, d.minOrder),
    validityDays: Number.isInteger(src.validityDays) && src.validityDays >= 1 && src.validityDays <= 365
      ? src.validityDays : d.validityDays,
    defaultUnit: src.defaultUnit === 'in' ? 'in' : 'mm',
    quotePrefix: strOr(src.quotePrefix, 20, d.quotePrefix),
    quantities,
    company: {
      name: strOr(company.name, 120), address: strOr(company.address, 600),
      logo, footer: strOr(company.footer, 600),
    },
    materials,
  };
}
