// Speichert Einstellungen, Sprache und Lizenz im Browser (localStorage).
// Ist der Speicher gesperrt (privater Modus, eingebettete Seite), läuft die App ohne Speichern weiter.

const memory = new Map();

export const KEYS = {
  settings: 'kerfquote.settings.v1',
  license: 'kerfquote.license',
  lang: 'kerfquote.lang',
  last: 'kerfquote.last',
};

export function load(key) {
  try {
    const raw = localStorage.getItem(key);
    return raw === null ? (memory.get(key) ?? null) : JSON.parse(raw);
  } catch {
    return memory.get(key) ?? null;
  }
}

export function save(key, value) {
  memory.set(key, value);
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // z. B. Speicher voll oder gesperrt: Wert bleibt nur für diese Sitzung erhalten
  }
}

export function remove(key) {
  memory.delete(key);
  try {
    localStorage.removeItem(key);
  } catch {
    // siehe oben
  }
}
