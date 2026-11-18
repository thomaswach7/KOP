// CSV-Export der Angebotspositionen (für Excel, ERP-Import).

import { roundTo } from '../cost/model.js';

/** Byte Order Mark: daran erkennt Excel UTF-8 */
const BOM = String.fromCharCode(0xfeff);

/**
 * Maskiert eine Textzelle. Zellen, die mit = + - @ beginnen, würde Excel als Formel
 * ausführen (Dateinamen stammen vom Kunden!) – sie bekommen ein führendes Hochkomma.
 */
export function csvCell(value, sep) {
  let s = String(value ?? '');
  if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`;
  if (s.includes(sep) || s.includes('"') || s.includes('\n') || s.includes('\r')) {
    s = `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

/**
 * @param {Array<{name:string, material:string, thickness:number, qty:number, cutLength:number,
 *   pierces:number, weightKg:number, unitPrice:number, total:number}>} rows
 * @param {{lang: string, header: string[]}} opts
 */
export function quoteCsv(rows, { lang, header }) {
  const german = lang === 'de';
  const sep = german ? ';' : ',';
  const num = (v, digits, fixed = false) => {
    const r = roundTo(v, digits);
    const s = fixed ? r.toFixed(digits) : String(r);
    return german ? s.replace('.', ',') : s;
  };
  const lines = [header.map((h) => csvCell(h, sep)).join(sep)];
  rows.forEach((r, i) => {
    lines.push([
      i + 1, csvCell(r.name, sep), csvCell(r.material, sep), num(r.thickness, 3), r.qty,
      num(r.cutLength, 1), r.pierces, num(r.weightKg, 3), num(r.unitPrice, 2, true), num(r.total, 2, true),
    ].join(sep));
  });
  return `${BOM}${lines.join('\r\n')}\r\n`;
}
