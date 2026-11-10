// Dekodiert den Dateiinhalt: DXF ab AutoCAD 2007 ist UTF-8, ältere Dateien nutzen meist
// die Windows-Codepage 1252 (Umlaute in Layernamen).

/** @param {ArrayBuffer} buffer */
export function decodeDxfBytes(buffer) {
  try {
    return new TextDecoder('utf-8', { fatal: true }).decode(buffer);
  } catch {
    return new TextDecoder('windows-1252').decode(buffer);
  }
}
