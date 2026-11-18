// Baut das druckfertige Angebotsdokument (wird über den Browser-Druckdialog zu Papier oder PDF).

import { h, clear, renderPreview } from './dom.js';
import { addDays } from './format.js';

/**
 * @param {HTMLElement} root
 * @param {{settings: object, quote: {customer: string, number: string, date: string},
 *          rows: Array<{part: object, material: object, price: object|null}>,
 *          totals: object, t: Function, fmt: object, isPro: boolean}} ctx
 */
export function renderQuoteDoc(root, { settings, quote, rows, totals, t, fmt, isPro }) {
  const { company } = settings;
  const logo = isPro && company.logo ? h('img', { class: 'doc-logo', src: company.logo, alt: company.name }) : null;

  const body = rows.map(({ part, material, price }, i) => {
    const thumb = renderPreview(part.analysis);
    const rect = part.analysis.rect;
    const spec = t('doc.spec', {
      material: material.name,
      t: fmt.num(part.thickness, 2),
      w: rect ? fmt.num(rect.w, 1) : '–',
      h: rect ? fmt.num(rect.h, 1) : '–',
      weight: price ? fmt.weight(price.weightKg) : '–',
    });
    return h('tr', null,
      h('td', null, String(i + 1)),
      h('td', null, h('div', { class: 'doc-thumb' }, thumb)),
      h('td', null, h('div', null, h('strong', null, part.name)), h('div', { class: 'doc-spec' }, spec)),
      h('td', { class: 'r' }, price ? `${fmt.num(price.qty, 0)} ${t('unit.pcs')}` : '–'),
      h('td', { class: 'r' }, price ? fmt.money(price.unitPrice) : '–'),
      h('td', { class: 'r' }, price ? fmt.money(price.total) : '–'));
  });

  const totalRows = [h('tr', null, h('td', null, t('quote.net')), h('td', { class: 'r' }, fmt.money(totals.net)))];
  if (totals.surcharge > 0) {
    totalRows.push(h('tr', null, h('td', null, t('quote.surcharge')), h('td', { class: 'r' }, fmt.money(totals.surcharge))));
  }
  totalRows.push(
    h('tr', null, h('td', null, t('quote.vat', { pct: fmt.num(settings.vatPct, 2) })), h('td', { class: 'r' }, fmt.money(totals.vat))),
    h('tr', { class: 'grand' }, h('td', null, t('quote.gross')), h('td', { class: 'r' }, fmt.money(totals.gross))));

  clear(root).append(h('article', { class: 'doc' },
    h('header', { class: 'doc-head' },
      h('div', null, logo ?? h('div', { class: 'doc-company' }, company.name)),
      h('div', { class: 'doc-address' }, logo && company.name ? `${company.name}\n${company.address}` : company.address)),
    h('section', { class: 'doc-meta' },
      h('div', { class: 'doc-customer' }, quote.customer),
      h('dl', { class: 'doc-facts' },
        h('dt', null, t('doc.number')), h('dd', null, quote.number),
        h('dt', null, t('doc.date')), h('dd', null, fmt.date(quote.date)),
        h('dt', null, t('doc.validUntil')), h('dd', null, fmt.date(addDays(quote.date, settings.validityDays))))),
    h('h1', null, `${t('doc.title')} ${quote.number}`),
    h('p', null, t('doc.intro')),
    h('table', { class: 'doc-table' },
      h('thead', null, h('tr', null,
        h('th', { scope: 'col' }, t('quote.pos')), h('th', { scope: 'col' }), h('th', { scope: 'col' }, t('quote.desc')),
        h('th', { scope: 'col', class: 'r' }, t('quote.qty')), h('th', { scope: 'col', class: 'r' }, t('quote.unit')),
        h('th', { scope: 'col', class: 'r' }, t('quote.total')))),
      h('tbody', null, body)),
    h('table', { class: 'doc-totals' }, h('tbody', null, totalRows)),
    company.footer ? h('footer', { class: 'doc-footer' }, company.footer) : null,
    isPro ? null : h('p', { class: 'doc-watermark' }, t('doc.watermark'))));
}
