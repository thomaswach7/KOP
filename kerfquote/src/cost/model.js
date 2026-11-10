// Kalkulationsmodell: aus Geometrie-Kennwerten, Material und Betriebssätzen wird ein Stückpreis.
//
//   Material   = (Rechteck + Stegzugabe) · Dicke · Dichte · Preis/kg
//   Schneiden  = (Schnittlänge / Vorschub + Einstiche · Einstechzeit) · Maschinenstundensatz
//   Rüsten     = Rüstkosten je Position / Menge
//   Stückpreis = (Material + Schneiden + Rüsten + Biegen + Zusatz) · (1 + Zuschlag)

/** Kaufmännisches Runden ohne Gleitkomma-Ausreißer (1.005 → 1.01 bei zwei Stellen). */
export function roundTo(x, digits) {
  if (!Number.isFinite(x) || Math.abs(x) < 1e-9) return 0;
  const r = Number(`${Math.round(Number(`${x}e${digits}`))}e-${digits}`);
  if (Number.isFinite(r)) return r;
  const f = 10 ** digits;
  return Math.round(x * f) / f;
}

/** Runden auf Cent. */
export const round2 = (x) => roundTo(x, 2);

export function findThickness(material, t) {
  return material?.thicknesses?.find((row) => Math.abs(row.t - t) < 1e-9) ?? null;
}

/**
 * @param {{cutLength:number, pierces:number, rect:{w:number,h:number}|null, netArea:number}} metrics in mm / mm²
 * @param {{thickness:number, qty:number, bends?:number, extra?:number}} line
 * @param {object|null} material
 * @param {object} settings
 * @returns {object|null} Kostenaufschlüsselung je Stück oder null, wenn Material/Dicke fehlen
 */
export function priceLine(metrics, line, material, settings) {
  const row = findThickness(material, line.thickness);
  if (!row) return null;
  const qty = Math.max(1, Math.floor(Number(line.qty) || 0));
  const bends = Math.max(0, Math.floor(Number(line.bends) || 0));
  const extraCost = Math.max(0, Number(line.extra) || 0);

  const kgPerMm2 = (row.t * material.density) / 1e6; // mm² · mm · kg/dm³ → kg
  const chargedAreaMm2 = metrics.rect
    ? (metrics.rect.w + settings.partGap) * (metrics.rect.h + settings.partGap) : 0;
  const chargedWeightKg = chargedAreaMm2 * kgPerMm2;
  const weightKg = metrics.netArea * kgPerMm2;
  const materialCost = chargedWeightKg * material.pricePerKg;

  const cutTimeSec = (metrics.cutLength / row.speed) * 60 + metrics.pierces * row.pierce;
  const cutCost = (cutTimeSec / 3600) * settings.machineRate;
  const setupPerPart = settings.setupCost / qty;
  const bendCost = bends * settings.pricePerBend;

  const costPerPart = materialCost + cutCost + setupPerPart + bendCost + extraCost;
  const unitPrice = round2(costPerPart * (1 + settings.markupPct / 100));
  return {
    qty, weightKg, chargedAreaMm2, chargedWeightKg, materialCost, cutTimeSec, cutCost,
    setupPerPart, bendCost, extraCost, costPerPart,
    markup: unitPrice - costPerPart, unitPrice, total: round2(unitPrice * qty),
  };
}

/** Staffelpreise für mehrere Mengen. */
export function quantityBreaks(metrics, line, material, settings, quantities) {
  const out = [];
  for (const qty of quantities) {
    const r = priceLine(metrics, { ...line, qty }, material, settings);
    if (r) out.push({ qty, unitPrice: r.unitPrice, total: r.total });
  }
  return out;
}

/** Angebotssumme: Mindestauftragswert als Zuschlag, darauf Mehrwertsteuer. */
export function quoteTotals(lineTotals, settings) {
  const net = round2(lineTotals.reduce((s, v) => s + v, 0));
  const surcharge = net > 0 && net < settings.minOrder ? round2(settings.minOrder - net) : 0;
  const subtotal = round2(net + surcharge);
  const vat = round2((subtotal * settings.vatPct) / 100);
  return { net, surcharge, subtotal, vat, gross: round2(subtotal + vat) };
}

/** Fertigungshinweise, die vom gewählten Blech abhängen. */
export function featureWarnings(metrics, thickness) {
  const out = [];
  if (metrics.openCount > 0) out.push('openContours');
  if (metrics.minInnerSize !== null && metrics.minInnerSize !== undefined && metrics.minInnerSize < thickness) {
    out.push('smallFeature');
  }
  return out;
}
