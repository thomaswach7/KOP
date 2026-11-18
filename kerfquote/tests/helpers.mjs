// Testhilfen: DXF-Texte aus Gruppencode/Wert-Paaren zusammensetzen.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

/** e('LINE', 8, '0', 10, 0, 20, 0, ...) → DXF-Text einer Entität */
export function e(type, ...flat) {
  let out = `0\n${type}\n`;
  for (let i = 0; i < flat.length; i += 2) out += `${flat[i]}\n${flat[i + 1]}\n`;
  return out;
}

/** Vollständiges DXF-Dokument aus Entitäten-Text, optional HEADER-Variablen und BLOCKS-Text. */
export function doc(entities, { header = '', blocks = '' } = {}) {
  let out = '';
  if (header) out += `0\nSECTION\n2\nHEADER\n${header}0\nENDSEC\n`;
  if (blocks) out += `0\nSECTION\n2\nBLOCKS\n${blocks}0\nENDSEC\n`;
  out += `0\nSECTION\n2\nENTITIES\n${entities}0\nENDSEC\n0\nEOF\n`;
  return out;
}

export const sample = (name) =>
  readFileSync(fileURLToPath(new URL(`../samples/${name}.dxf`, import.meta.url)), 'utf8');

export const reference = JSON.parse(
  readFileSync(fileURLToPath(new URL('./reference.json', import.meta.url)), 'utf8'),
);

export const close = (a, b, tol = 1e-6) => Math.abs(a - b) <= tol;
export const relClose = (a, b, rel) => Math.abs(a - b) <= Math.abs(b) * rel;
