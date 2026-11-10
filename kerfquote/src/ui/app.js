// KerfQuote – Hauptmodul der Oberfläche.

import { CONFIG } from '../config.js';
import { LICENSE_PUBLIC_KEY } from '../license-public-key.js';
import { createI18n, detectLanguage, LANGUAGES } from '../i18n.js';
import { sanitizeSettings } from '../cost/defaults.js';
import { quoteTotals } from '../cost/model.js';
import { verifyLicense, FREE_LIMITS } from '../license.js';
import { DxfError } from '../dxf/parse.js';
import { decodeDxfBytes } from '../dxf/decode.js';
import { createPart, refreshGeometry, pricePart, normalizePart } from './part.js';
import { $, h, clear, renderPreview, download, confirmClick } from './dom.js';
import { createFormat, todayIso, defaultQuoteNumber } from './format.js';
import { quoteCsv } from './csv.js';
import { renderQuoteDoc } from './quote-doc.js';
import { createSettingsDialog } from './settings-dialog.js';
import { KEYS, load, save, remove } from '../store.js';

const UNIT_CHOICES = ['mm', 'cm', 'm', 'in', 'ft'];

const storedLast = load(KEYS.last);
const state = {
  lang: 'de',
  settings: sanitizeSettings(load(KEYS.settings)),
  license: { token: null, valid: false, payload: null, reason: null },
  parts: [],
  selectedId: null,
  quote: { customer: '', number: '', numberEdited: false, date: todayIso() },
  last: storedLast && typeof storedLast === 'object' ? storedLast : {},
};

let t = createI18n(state.lang);
let fmt = createFormat(state.lang, state.settings.currency);
let toastTimer = null;
const previewCache = new WeakMap();

const isPro = () => state.license.valid;
const selectedPart = () => state.parts.find((p) => p.id === state.selectedId) ?? null;
const pricedRows = () => state.parts.map((part) => ({ part, ...pricePart(part, state.settings) }));

// --- Meldungen ------------------------------------------------------------------------------

function toast(message, isError = false) {
  const el = $('#toast');
  clearTimeout(toastTimer);
  el.textContent = message;
  el.classList.toggle('is-error', isError);
  toastTimer = setTimeout(() => { el.textContent = ''; }, isError ? 9000 : 5000);
}

// --- Teile laden ----------------------------------------------------------------------------

function roomForParts() {
  return isPro() ? Infinity : FREE_LIMITS.maxParts - state.parts.length;
}

/** @returns {boolean} true, wenn das Teil aufgenommen wurde */
function addDxfText(fileName, text, errors) {
  try {
    const part = createPart(fileName, text, state.settings, state.last);
    if (part.flat.prims.length === 0) {
      errors.push(t('err.noGeometry', { file: fileName }));
      return false;
    }
    state.parts.push(part);
    return true;
  } catch (err) {
    const key = err instanceof DxfError && ['binary', 'empty'].includes(err.code) ? `err.${err.code}` : 'err.invalid';
    errors.push(t(key, { file: fileName }));
    return false;
  }
}

/** Warteschlange: mehrere Ladevorgänge laufen nacheinander, damit die Free-Grenze zuverlässig gilt. */
let loadQueue = Promise.resolve();
function addEntries(entries) {
  loadQueue = loadQueue.then(() => processEntries(entries)).catch(() => toast(t('err.sample'), true));
  return loadQueue;
}

async function processEntries(entries) {
  const errors = [];
  let added = 0;
  let firstId = null;
  let limited = false;
  for (const entry of entries) {
    if (roomForParts() <= 0) { limited = true; break; }
    const text = await entry.read(errors);
    if (text === null) continue;
    if (addDxfText(entry.name, text, errors)) {
      added++;
      firstId ??= state.parts[state.parts.length - 1].id;
    }
  }
  if (firstId !== null) state.selectedId = firstId;
  if (added > 0) {
    renderDetailForm();
    refresh();
  }
  if (errors.length) toast(errors.join(' '), true);
  else if (limited) toast(t('toast.limit', { max: FREE_LIMITS.maxParts }), true);
  else if (added > 0) toast(t('toast.added', { n: added }));
}

function addFiles(fileList) {
  const files = [...fileList];
  if (files.length === 0) return;
  addEntries(files.map((file) => ({
    name: file.name,
    read: async (errors) => {
      if (file.size > CONFIG.maxFileMb * 1024 * 1024) {
        errors.push(t('err.tooBig', { file: file.name, mb: CONFIG.maxFileMb }));
        return null;
      }
      return decodeDxfBytes(await file.arrayBuffer());
    },
  })));
}

function addSamples() {
  addEntries(CONFIG.samples.map((name) => ({
    name,
    read: async (errors) => {
      try {
        const res = await fetch(new URL(`../../samples/${name}`, import.meta.url));
        if (!res.ok) throw new Error(String(res.status));
        return await res.text();
      } catch {
        if (!errors.includes(t('err.sample'))) errors.push(t('err.sample'));
        return null;
      }
    },
  })));
}

function removePart(id) {
  const index = state.parts.findIndex((p) => p.id === id);
  if (index < 0) return;
  state.parts.splice(index, 1);
  if (state.selectedId === id) {
    state.selectedId = state.parts[Math.min(index, state.parts.length - 1)]?.id ?? null;
    renderDetailForm();
  }
  refresh();
}

function selectPart(id) {
  state.selectedId = id;
  renderDetailForm();
  refresh();
}

// --- Darstellung ----------------------------------------------------------------------------

function renderPlan() {
  const pro = isPro();
  const button = $('#btn-license');
  button.textContent = t('plan.badge', { plan: t(pro ? 'plan.pro' : 'plan.free') });
  button.dataset.plan = pro ? 'pro' : 'free';
  $('#csv-tag').hidden = pro;
  $('#free-note').hidden = pro;
  $('#free-note-text').textContent = `${t('quote.freeNote', { max: FREE_LIMITS.maxParts })} `;
}

function renderParts(rows) {
  clear($('#part-list')).append(...rows.map(({ part, material, price }) => h('li', { class: 'part-item' },
    h('button', {
      type: 'button', class: 'part-select', 'aria-current': part.id === state.selectedId ? 'true' : null,
      onclick: () => selectPart(part.id),
    },
    h('span', { class: 'part-name' }, part.name),
    h('span', { class: 'part-meta' },
      `${material.name} · ${fmt.num(part.thickness, 2)} mm · ${fmt.num(part.qty, 0)} ${t('unit.pcs')}`),
    h('span', { class: 'part-meta num' }, price ? `${fmt.money(price.unitPrice)} ${t('parts.each')}` : '–')),
    h('button', {
      type: 'button', class: 'part-remove', 'aria-label': t('parts.remove', { name: part.name }),
      title: t('parts.remove', { name: part.name }), onclick: () => removePart(part.id),
    }, '×'))));
  $('#parts-empty').hidden = rows.length > 0;
}

function fillThicknessSelect(part, material) {
  clear($('#p-thickness')).append(...material.thicknesses.map((row) =>
    h('option', { value: String(row.t), selected: row.t === part.thickness }, fmt.num(row.t, 2))));
}

function renderLayers(part) {
  clear($('#layers')).append(...part.layers.map((layer) => h('li', null, h('label', null,
    h('input', {
      type: 'checkbox', checked: !part.ignoreLayers.includes(layer.name),
      onchange: (e) => {
        part.ignoreLayers = e.target.checked
          ? part.ignoreLayers.filter((name) => name !== layer.name)
          : [...part.ignoreLayers, layer.name];
        refreshGeometry(part, state.settings);
        refresh();
      },
    }),
    h('span', { class: 'layer-name' }, layer.name),
    h('span', { class: 'layer-info' }, t('layers.count', { count: layer.count, length: fmt.length(layer.length) }))))));
}

/** Füllt die Eingabefelder des Detailbereichs (bei Auswahl, Sprach- oder Einstellungswechsel). */
function renderDetailForm() {
  const part = selectedPart();
  $('#detail').hidden = !part;
  $('#detail-empty').hidden = Boolean(part);
  if (!part) return;
  const material = normalizePart(part, state.settings);
  $('#part-name').value = part.name;
  clear($('#p-material')).append(...state.settings.materials.map((m) =>
    h('option', { value: m.id, selected: m.id === part.materialId }, m.name)));
  fillThicknessSelect(part, material);
  $('#p-qty').value = String(part.qty);
  $('#p-bends').value = String(part.bends);
  $('#p-extra').value = String(part.extra);
  $('#p-tol').value = String(part.tol);
  const detected = t(`unit.${part.flat.unit.source === 'manual' ? resolveAutoUnit(part) : part.flat.unit.name}`);
  clear($('#p-units')).append(
    h('option', { value: 'auto', selected: part.units === 'auto' }, t('p.unitsAuto', { unit: detected })),
    ...UNIT_CHOICES.map((u) => h('option', { value: u, selected: part.units === u }, t(`unit.${u}`))));
  renderLayers(part);
}

/** Einheit, die "Automatisch" ergeben würde, auch wenn gerade eine manuelle Einheit gewählt ist. */
function resolveAutoUnit(part) {
  const names = { 1: 'in', 2: 'ft', 4: 'mm', 5: 'cm', 6: 'm' };
  return names[part.dxf.header.insunits] ?? state.settings.defaultUnit;
}

function renderOutputs(row) {
  const { part, price, breaks, warnings } = row;
  const a = part.analysis;

  // Die Vorschau hängt nur von der Geometrie ab: je Analyse einmal bauen, bei Preisänderungen wiederverwenden
  if (!previewCache.has(a)) previewCache.set(a, renderPreview(a));
  const preview = previewCache.get(a);
  const box = $('#preview');
  if (!preview) clear(box).append(h('p', { class: 'muted' }, t('warn.none')));
  else if (box.firstChild !== preview || box.childNodes.length !== 1) clear(box).append(preview);

  const metrics = [
    ['m.cutLength', fmt.length(a.cutLength)],
    ['m.pierces', fmt.num(a.pierces, 0)],
    ['m.contours', t('m.contoursValue', { closed: a.closedCount, open: a.openCount })],
    ['m.size', a.rect ? fmt.dims(a.rect.w, a.rect.h) : '–'],
    ['m.area', fmt.area(a.netArea)],
    ['m.weight', price ? fmt.weight(price.weightKg) : '–'],
    ['m.cutTime', price ? fmt.time(price.cutTimeSec) : '–'],
  ];
  clear($('#metrics')).append(...metrics.map(([key, value]) =>
    h('div', { class: 'metric' }, h('dt', null, t(key)), h('dd', null, value))));

  clear($('#warnings')).append(...warnings.map((w) => {
    const vars = w.vars?.unit ? { ...w.vars, unit: t(`unit.${w.vars.unit}`) } : w.vars;
    return h('li', { class: `w-${w.level}` }, t(w.key, vars));
  }));

  const costBody = clear($('#cost-table tbody'));
  $('#cost-none').hidden = Boolean(price);
  $('#cost-table').hidden = !price;
  if (price) {
    const line = (label, value, cls) => h('tr', { class: cls }, h('td', null, label), h('td', { class: 'r' }, fmt.money(value)));
    costBody.append(
      line(t('cost.material', { weight: fmt.weight(price.chargedWeightKg) }), price.materialCost),
      line(t('cost.cutting', { time: fmt.time(price.cutTimeSec) }), price.cutCost),
      line(t('cost.setup'), price.setupPerPart));
    if (price.bendCost > 0) costBody.append(line(t('cost.bending'), price.bendCost));
    if (price.extraCost > 0) costBody.append(line(t('cost.extra'), price.extraCost));
    costBody.append(
      line(t('cost.markup', { pct: fmt.num(state.settings.markupPct, 2) }), price.markup),
      line(t('cost.unit'), price.unitPrice, 'sum'),
      line(t('cost.total', { qty: fmt.num(price.qty, 0) }), price.total, 'sum'));
  }

  clear($('#breaks-table tbody')).append(...breaks.map((b) => h('tr', { class: price && b.qty === price.qty ? 'is-current' : null },
    h('td', null, fmt.num(b.qty, 0)),
    h('td', { class: 'r' }, fmt.money(b.unitPrice)),
    h('td', { class: 'r' }, fmt.money(b.total)))));
}

function renderQuote(rows) {
  const priced = rows.filter((r) => r.price);
  const totals = quoteTotals(priced.map((r) => r.price.total), state.settings);
  $('#quote-table').hidden = rows.length === 0;
  $('#quote-empty').hidden = rows.length > 0;
  clear($('#quote-table tbody')).append(...rows.map(({ part, price }, i) => h('tr', null,
    h('td', null, String(i + 1)),
    h('td', null, part.name),
    h('td', { class: 'r' }, fmt.num(part.qty, 0)),
    h('td', { class: 'r' }, price ? fmt.money(price.unitPrice) : '–'),
    h('td', { class: 'r' }, price ? fmt.money(price.total) : '–'))));

  const items = [[t('quote.net'), totals.net, null]];
  if (totals.surcharge > 0) items.push([t('quote.surcharge'), totals.surcharge, null]);
  items.push([t('quote.vat', { pct: fmt.num(state.settings.vatPct, 2) }), totals.vat, null]);
  items.push([t('quote.gross'), totals.gross, 'grand']);
  clear($('#quote-totals')).append(...items.flatMap(([label, value, cls]) => [
    h('dt', { class: cls }, label), h('dd', { class: cls }, fmt.money(value)),
  ]));

  const none = priced.length === 0;
  $('#btn-print').disabled = none;
  $('#btn-csv').disabled = none;
  $('#btn-clear').disabled = rows.length === 0;
  return { priced, totals };
}

/** Rechnet alle Positionen neu und aktualisiert Listen, Kennwerte und Angebot. */
function refresh() {
  const rows = pricedRows();
  renderParts(rows);
  const current = rows.find((r) => r.part.id === state.selectedId);
  if (current) renderOutputs(current);
  renderQuote(rows);
}

function applyLanguage() {
  t = createI18n(state.lang);
  fmt = createFormat(state.lang, state.settings.currency);
  document.documentElement.lang = state.lang;
  document.title = t('app.title');
  for (const el of document.querySelectorAll('[data-i18n]')) el.textContent = t(el.dataset.i18n);
  $('#preview').setAttribute('aria-label', t('detail.preview'));
  $('#brand-link').setAttribute('aria-label', `KerfQuote – ${t('nav.home')}`);
  $('#lang').value = state.lang;
  renderPlan();
  renderLicense();
  renderDetailForm();
  refresh();
  settingsDialog.refresh();
}

// --- Angebot: Druck und CSV -----------------------------------------------------------------

function printQuote() {
  const { priced, totals } = renderQuote(pricedRows());
  if (priced.length === 0) return;
  renderQuoteDoc($('#print-root'), { settings: state.settings, quote: state.quote, rows: priced, totals, t, fmt, isPro: isPro() });
  const title = document.title;
  document.title = `${t('doc.title')} ${state.quote.number}`.trim();
  window.addEventListener('afterprint', () => { document.title = title; }, { once: true });
  window.print();
}

function exportCsv() {
  if (!isPro()) {
    toast(t('toast.csvPro'), true);
    openLicense();
    return;
  }
  const rows = pricedRows().filter((r) => r.price).map(({ part, material, price }) => ({
    name: part.name, material: material.name, thickness: part.thickness, qty: price.qty,
    cutLength: part.analysis.cutLength, pierces: part.analysis.pierces, weightKg: price.weightKg,
    unitPrice: price.unitPrice, total: price.total,
  }));
  const header = ['pos', 'name', 'material', 'thickness', 'qty', 'cutLength', 'pierces', 'weight', 'unitPrice', 'total']
    .map((key) => t(`csv.${key}`));
  const fileName = `${(state.quote.number || 'angebot').replace(/[^\w.-]+/g, '_')}.csv`;
  download(fileName, quoteCsv(rows, { lang: state.lang, header }), 'text/csv;charset=utf-8');
}

// --- Lizenz ---------------------------------------------------------------------------------

function renderLicense() {
  const lic = state.license;
  const status = $('#license-status');
  status.classList.toggle('is-pro', lic.valid);
  if (lic.valid) {
    status.textContent = t('license.statusPro', { name: lic.payload.name ?? '', date: fmt.date(lic.payload.exp) });
  } else if (lic.reason === 'expired' && lic.payload) {
    status.textContent = `${t('license.statusFree')} ${t('license.errExpired', { date: fmt.date(lic.payload.exp) })}`;
  } else {
    status.textContent = t('license.statusFree');
  }
  const buy = clear($('#license-buy'));
  if (/^https:\/\//.test(CONFIG.checkoutUrl)) {
    buy.append(h('a', { class: 'btn', href: CONFIG.checkoutUrl, target: '_blank', rel: 'noopener' }, t('license.buy')));
  } else {
    buy.append(h('span', { class: 'muted' }, t('license.noCheckout')));
  }
  $('#btn-remove-license').hidden = !lic.token;
}

function openLicense() {
  $('#license-error').textContent = '';
  renderLicense();
  const dialog = $('#dlg-license');
  if (!dialog.open) dialog.showModal();
}

function onLicenseChanged() {
  renderPlan();
  renderLicense();
  settingsDialog.refresh();
  refresh();
}

async function activateLicense() {
  const token = $('#license-key').value.replace(/\s+/g, '');
  const result = await verifyLicense(token, LICENSE_PUBLIC_KEY);
  if (!result.valid) {
    const key = {
      format: 'license.errFormat', signature: 'license.errSignature',
      expired: 'license.errExpired', unconfigured: 'license.errUnconfigured',
    }[result.reason];
    $('#license-error').textContent = t(key, { date: result.payload ? fmt.date(result.payload.exp) : '' });
    return;
  }
  state.license = { token, valid: true, payload: result.payload, reason: null };
  save(KEYS.license, token);
  $('#license-key').value = '';
  $('#license-error').textContent = '';
  onLicenseChanged();
  toast(t('license.activated'));
}

function removeLicense() {
  state.license = { token: null, valid: false, payload: null, reason: null };
  remove(KEYS.license);
  onLicenseChanged();
  toast(t('license.removed'));
}

// --- Einstellungen --------------------------------------------------------------------------

function syncQuoteNumber() {
  if (state.quote.numberEdited) return;
  state.quote.number = defaultQuoteNumber(state.settings.quotePrefix, state.quote.date);
  $('#q-number').value = state.quote.number;
}

const settingsDialog = createSettingsDialog({
  dialog: $('#dlg-settings'),
  body: $('#settings-body'),
  getSettings: () => state.settings,
  getT: () => t,
  isPro,
  toast,
  commit: (draft) => {
    const unitBefore = state.settings.defaultUnit;
    state.settings = sanitizeSettings(draft);
    save(KEYS.settings, state.settings);
    fmt = createFormat(state.lang, state.settings.currency);
    if (state.settings.defaultUnit !== unitBefore) {
      for (const part of state.parts) refreshGeometry(part, state.settings);
    }
    syncQuoteNumber();
    renderDetailForm();
    refresh();
  },
});

// --- Ereignisse -----------------------------------------------------------------------------

function readNumber(input) {
  if (input.value === '' || !input.checkValidity()) return null;
  const value = Number(input.value);
  return Number.isFinite(value) ? value : null;
}

function bindDetailInputs() {
  const withPart = (fn) => (e) => {
    const part = selectedPart();
    if (part) fn(part, e.target);
  };
  $('#part-name').addEventListener('input', withPart((part, el) => {
    part.name = el.value.trim() || part.name;
    refresh();
  }));
  $('#p-material').addEventListener('change', withPart((part, el) => {
    part.materialId = el.value;
    fillThicknessSelect(part, normalizePart(part, state.settings));
    rememberLast(part);
    refresh();
  }));
  $('#p-thickness').addEventListener('change', withPart((part, el) => {
    part.thickness = Number(el.value);
    rememberLast(part);
    refresh();
  }));
  const numeric = (selector, apply) => $(selector).addEventListener('input', withPart((part, el) => {
    const value = readNumber(el);
    if (value === null) return;
    apply(part, value);
    refresh();
  }));
  numeric('#p-qty', (part, v) => { part.qty = v; });
  numeric('#p-bends', (part, v) => { part.bends = v; });
  numeric('#p-extra', (part, v) => { part.extra = v; });
  numeric('#p-tol', (part, v) => { part.tol = v; refreshGeometry(part, state.settings); });
  $('#p-units').addEventListener('change', withPart((part, el) => {
    part.units = el.value;
    refreshGeometry(part, state.settings);
    renderLayers(part);
    refresh();
  }));
}

function rememberLast(part) {
  state.last = { materialId: part.materialId, thickness: part.thickness };
  save(KEYS.last, state.last);
}

function bindEvents() {
  const dropzone = $('#dropzone');
  const fileInput = $('#file-input');
  fileInput.addEventListener('change', () => {
    addFiles(fileInput.files);
    fileInput.value = '';
  });
  for (const type of ['dragenter', 'dragover']) {
    window.addEventListener(type, (e) => {
      e.preventDefault();
      dropzone.classList.add('is-over');
    });
  }
  window.addEventListener('dragleave', (e) => {
    if (!e.relatedTarget) dropzone.classList.remove('is-over');
  });
  window.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('is-over');
    addFiles(e.dataTransfer?.files ?? []);
  });

  $('#btn-sample').addEventListener('click', addSamples);
  $('#btn-settings').addEventListener('click', () => settingsDialog.open());
  $('#btn-license').addEventListener('click', openLicense);
  $('#btn-unlock').addEventListener('click', openLicense);
  $('#btn-activate').addEventListener('click', activateLicense);
  $('#btn-remove-license').addEventListener('click', removeLicense);
  $('#btn-print').addEventListener('click', printQuote);
  $('#btn-csv').addEventListener('click', exportCsv);
  confirmClick($('#btn-clear'), () => t('quote.clearConfirm'), () => {
    state.parts = [];
    state.selectedId = null;
    renderDetailForm();
    refresh();
  });

  $('#lang').addEventListener('change', (e) => {
    state.lang = LANGUAGES.includes(e.target.value) ? e.target.value : 'en';
    save(KEYS.lang, state.lang);
    applyLanguage();
  });

  $('#q-customer').addEventListener('input', (e) => { state.quote.customer = e.target.value; });
  $('#q-number').addEventListener('input', (e) => {
    state.quote.number = e.target.value.trim();
    state.quote.numberEdited = true;
  });
  $('#q-date').addEventListener('change', (e) => {
    if (!e.target.value) { e.target.value = state.quote.date; return; }
    state.quote.date = e.target.value;
    syncQuoteNumber();
  });
  bindDetailInputs();
}

// --- Start ----------------------------------------------------------------------------------

async function init() {
  // Reihenfolge: ausdrücklicher Wunsch per Link (?lang=en) → gespeicherte Wahl → Browsersprache
  const urlLang = new URLSearchParams(location.search).get('lang');
  const storedLang = load(KEYS.lang);
  if (LANGUAGES.includes(urlLang)) {
    state.lang = urlLang;
    save(KEYS.lang, urlLang);
  } else {
    state.lang = LANGUAGES.includes(storedLang) ? storedLang : detectLanguage(navigator.languages ?? [navigator.language]);
  }
  $('#q-date').value = state.quote.date;
  syncQuoteNumber();
  bindEvents();
  applyLanguage();

  const token = load(KEYS.license);
  if (typeof token === 'string' && token) {
    const result = await verifyLicense(token, LICENSE_PUBLIC_KEY);
    state.license = { token, valid: result.valid, payload: result.payload ?? null, reason: result.reason ?? null };
    onLicenseChanged();
  }
  document.documentElement.dataset.ready = 'true';
}

init();
