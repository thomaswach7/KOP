// Formatierung von Zahlen, Währungen, Maßen und Datumswerten je Sprache.

const pad2 = (n) => String(n).padStart(2, '0');

export function todayIso(now = new Date()) {
  return `${now.getFullYear()}-${pad2(now.getMonth() + 1)}-${pad2(now.getDate())}`;
}

export function addDays(iso, days) {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

export const defaultQuoteNumber = (prefix, iso) => `${prefix}${iso.replace(/-/g, '')}-01`;

export function createFormat(lang, currency) {
  const locale = lang === 'de' ? 'de-DE' : 'en-US';
  const nf = (min, max) => new Intl.NumberFormat(locale, { minimumFractionDigits: min, maximumFractionDigits: max });
  const money = new Intl.NumberFormat(locale, { style: 'currency', currency });
  const dateFormat = new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeZone: 'UTC' });
  return {
    locale,
    money: (v) => money.format(v),
    num: (v, max = 2, min = 0) => nf(min, max).format(v),
    length: (mm) => (mm >= 1000 ? `${nf(2, 2).format(mm / 1000)} m` : `${nf(0, 1).format(mm)} mm`),
    area: (mm2) => (mm2 >= 1e6 ? `${nf(3, 3).format(mm2 / 1e6)} m²` : `${nf(1, 1).format(mm2 / 100)} cm²`),
    weight: (kg) => (kg < 10 ? `${nf(3, 3).format(kg)} kg` : `${nf(1, 1).format(kg)} kg`),
    dims: (w, h) => `${nf(0, 1).format(w)} × ${nf(0, 1).format(h)} mm`,
    time: (sec) => {
      const s = Math.round(sec);
      if (s < 3600 - 30) return `${Math.floor(s / 60)}:${pad2(s % 60)} min`;
      const minutes = Math.round(s / 60);
      return `${Math.floor(minutes / 60)} h ${pad2(minutes % 60)} min`;
    },
    date: (iso) => {
      const d = new Date(`${iso}T00:00:00Z`);
      return Number.isNaN(d.getTime()) ? '' : dateFormat.format(d);
    },
  };
}
