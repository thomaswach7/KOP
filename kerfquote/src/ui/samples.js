// Beispielteile laden. Hier per Abruf aus dem Ordner samples/ neben der App.
// Der Einzeldatei-Build (tools/build-standalone.mjs) ersetzt dieses Modul durch eine Fassung
// mit eingebetteten Dateien, weil eine per Doppelklick geöffnete Seite nichts nachladen darf.

/**
 * @param {string} name Dateiname aus CONFIG.samples
 * @returns {Promise<string>} Inhalt der DXF-Datei
 */
export async function loadSample(name) {
  const res = await fetch(new URL(`../../samples/${name}`, import.meta.url));
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.text();
}
