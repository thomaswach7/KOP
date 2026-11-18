// Einstellungsdialog. Änderungen wirken sofort (kein "Speichern"-Knopf, nichts geht verloren):
// Der Dialog bearbeitet einen Entwurf, der 1:1 den Eingabefeldern entspricht; wirksam wird
// immer die geprüfte Fassung (sanitizeSettings). Ungültige Felder werden rot markiert und
// bis zur Korrektur durch den Standardwert ersetzt.

import { h, clear, download, confirmClick } from './dom.js';
import { sanitizeSettings, CURRENCIES } from '../cost/defaults.js';

const MAX_LOGO_BYTES = 250 * 1024;

function setPath(target, path, value) {
  const keys = path.split('.');
  let obj = target;
  for (let i = 0; i < keys.length - 1; i++) obj = obj[keys[i]];
  obj[keys[keys.length - 1]] = value;
}

/**
 * @param {{dialog: HTMLDialogElement, body: HTMLElement, getSettings: () => object,
 *          commit: (draft: object) => void, getT: () => Function, isPro: () => boolean,
 *          toast: (message: string, isError?: boolean) => void}} ctx
 */
export function createSettingsDialog({ dialog, body, getSettings, commit, getT, isPro, toast }) {
  let draft = null;
  let openSection = 0;
  let openMaterial = -1;

  const field = (label, control, hint) => h('div', { class: 'field' },
    h('label', { htmlFor: control.id }, label), control, hint ? h('span', { class: 'hint' }, hint) : null);

  const text = (id, path, value, maxlength) =>
    h('input', { type: 'text', id, maxlength, autocomplete: 'off', value: value ?? '', dataset: { path, type: 'text' } });

  const area = (id, path, value, maxlength) =>
    h('textarea', { id, maxlength, autocomplete: 'off', value: value ?? '', dataset: { path, type: 'text' } });

  const number = (id, path, value, min, max, extra = {}) => h('input', {
    type: 'number', id, min, max, step: extra.step ?? 'any', inputmode: extra.step === 1 ? 'numeric' : 'decimal',
    'aria-label': extra.label, value: Number.isFinite(value) ? String(value) : '', required: true,
    dataset: { path, type: 'num' },
  });

  const select = (id, path, value, options) => h('select', { id, dataset: { path, type: 'text' } },
    options.map(([v, label]) => h('option', { value: v, selected: v === value }, label)));

  const section = (index, title, ...content) => h('details', {
    class: 'sect', name: 'settings', open: index === openSection,
    ontoggle: (e) => { if (e.target.open) openSection = index; else if (openSection === index) openSection = -1; },
  }, h('summary', null, title), h('div', { class: 'sect-body' }, content));

  function companySection(t) {
    const c = draft.company;
    const logoInput = h('input', {
      type: 'file', id: 's-logo', accept: 'image/png,image/jpeg,image/webp,image/svg+xml', disabled: !isPro(),
      onchange: (e) => {
        const file = e.target.files[0];
        if (!file) return;
        if (file.size > MAX_LOGO_BYTES) { toast(t('s.logoTooBig'), true); e.target.value = ''; return; }
        const reader = new FileReader();
        reader.onload = () => {
          const before = draft.company.logo;
          draft.company.logo = String(reader.result);
          commit(draft);
          if (getSettings().company.logo !== draft.company.logo) {
            // von der Prüfung abgelehnt (Format/Größe): vorheriges Logo behalten
            draft.company.logo = before;
            commit(draft);
            toast(t('s.logoTooBig'), true);
          }
          render();
        };
        reader.readAsDataURL(file);
      },
    });
    return section(0, t('settings.company'),
      field(t('s.companyName'), text('s-company', 'company.name', c.name, 120)),
      field(t('s.address'), area('s-address', 'company.address', c.address, 600)),
      field(t('s.logo'), logoInput, isPro() ? null : t('s.logoPro')),
      c.logo ? h('div', { class: 'row-actions' },
        h('img', { class: 'logo-preview', src: c.logo, alt: '' }),
        h('button', { type: 'button', class: 'btn', onclick: () => { draft.company.logo = ''; commit(draft); render(); } }, t('s.logoRemove')))
        : null,
      field(t('s.footer'), area('s-footer', 'company.footer', c.footer, 600)),
      h('div', { class: 'form-grid' },
        field(t('s.quotePrefix'), text('s-prefix', 'quotePrefix', draft.quotePrefix, 20)),
        field(t('s.validity'), number('s-validity', 'validityDays', draft.validityDays, 1, 365, { step: 1 }))));
  }

  function calcSection(t) {
    return section(1, t('settings.calc'), h('div', { class: 'form-grid' },
      field(t('s.currency'), select('s-currency', 'currency', draft.currency, CURRENCIES.map((c) => [c, c]))),
      field(t('s.vat'), number('s-vat', 'vatPct', draft.vatPct, 0, 100)),
      field(t('s.machineRate'), number('s-rate', 'machineRate', draft.machineRate, 0, 100000)),
      field(t('s.setup'), number('s-setup', 'setupCost', draft.setupCost, 0, 100000)),
      field(t('s.markup'), number('s-markup', 'markupPct', draft.markupPct, 0, 1000)),
      field(t('s.gap'), number('s-gap', 'partGap', draft.partGap, 0, 1000)),
      field(t('s.bend'), number('s-bend', 'pricePerBend', draft.pricePerBend, 0, 10000)),
      field(t('s.minOrder'), number('s-minorder', 'minOrder', draft.minOrder, 0, 1000000)),
      field(t('s.quantities'), h('input', {
        type: 'text', id: 's-quantities', autocomplete: 'off', inputmode: 'numeric', pattern: '[0-9]+([,; ]+[0-9]+)*',
        required: true, value: draft.quantities.join(', '), dataset: { path: 'quantities', type: 'list' },
      })),
      field(t('s.defaultUnit'), select('s-defunit', 'defaultUnit', draft.defaultUnit,
        [['mm', t('unit.mm')], ['in', t('unit.in')]]))));
  }

  function materialEditor(t, m, mi) {
    const base = `materials.${mi}`;
    const rows = m.thicknesses.map((row, ri) => h('tr', null,
      h('td', null, number(`s-m${mi}-t${ri}`, `${base}.thicknesses.${ri}.t`, row.t, 0.01, 500, { label: `${t('s.t')} ${ri + 1}` })),
      h('td', null, number(`s-m${mi}-v${ri}`, `${base}.thicknesses.${ri}.speed`, row.speed, 1, 1000000, { label: `${t('s.speed')} ${ri + 1}` })),
      h('td', null, number(`s-m${mi}-p${ri}`, `${base}.thicknesses.${ri}.pierce`, row.pierce, 0, 600, { label: `${t('s.pierce')} ${ri + 1}` })),
      h('td', null, h('button', {
        type: 'button', class: 'icon-btn', 'aria-label': `${t('s.removeRow')} ${ri + 1}`, title: t('s.removeRow'),
        onclick: () => { m.thicknesses.splice(ri, 1); commit(draft); render(); },
      }, '×'))));
    // exklusives Akkordeon: es ist immer höchstens ein Material aufgeklappt (passend zu openMaterial)
    return h('details', {
      class: 'mat', name: 'settings-material', open: mi === openMaterial,
      ontoggle: (e) => { if (e.target.open) openMaterial = mi; else if (openMaterial === mi) openMaterial = -1; },
    },
    h('summary', { id: `s-m${mi}-summary` }, m.name || t('s.newMaterial')),
    h('div', { class: 'mat-body' },
      h('div', { class: 'form-grid' },
        field(t('s.matName'), text(`s-m${mi}-name`, `${base}.name`, m.name, 60)),
        field(t('s.density'), number(`s-m${mi}-density`, `${base}.density`, m.density, 0.01, 25)),
        field(t('s.pricePerKg'), number(`s-m${mi}-price`, `${base}.pricePerKg`, m.pricePerKg, 0, 100000))),
      h('table', { class: 'mat-table' },
        h('thead', null, h('tr', null,
          h('th', { scope: 'col' }, t('s.t')), h('th', { scope: 'col' }, t('s.speed')),
          h('th', { scope: 'col' }, t('s.pierce')), h('th', { scope: 'col' }, h('span', { class: 'sr-only' }, t('s.removeRow'))))),
        h('tbody', null, rows)),
      h('div', { class: 'row-actions' },
        h('button', {
          type: 'button', class: 'btn',
          onclick: () => {
            m.thicknesses.push({ t: NaN, speed: NaN, pierce: NaN });
            render();
            body.querySelector(`#s-m${mi}-t${m.thicknesses.length - 1}`)?.focus();
          },
        }, t('s.addRow')),
        draft.materials.length > 1 ? h('button', {
          type: 'button', class: 'btn btn-danger',
          onclick: () => { draft.materials.splice(mi, 1); openMaterial = -1; commit(draft); render(); },
        }, t('s.removeMaterial')) : null)));
  }

  function materialsSection(t) {
    return section(2, t('settings.materials'),
      h('p', { class: 'hint' }, t('s.matHint')),
      draft.materials.map((m, mi) => materialEditor(t, m, mi)),
      h('div', { class: 'row-actions' }, h('button', {
        type: 'button', class: 'btn',
        onclick: () => {
          draft.materials.push({
            id: `m${Date.now().toString(36)}`, name: t('s.newMaterial'), density: 7.85, pricePerKg: 1,
            thicknesses: [{ t: 1, speed: 5000, pierce: 0.3 }],
          });
          openMaterial = draft.materials.length - 1;
          commit(draft);
          render();
        },
      }, t('s.addMaterial'))));
  }

  function backupSection(t) {
    const importInput = h('input', {
      type: 'file', class: 'sr-only', accept: 'application/json,.json', 'aria-label': t('s.import'), tabindex: '-1',
      onchange: async (e) => {
        const file = e.target.files[0];
        e.target.value = '';
        if (!file) return;
        try {
          const parsed = JSON.parse(await file.text());
          if (!parsed || typeof parsed !== 'object') throw new Error('kein Objekt');
          draft = structuredClone(sanitizeSettings(parsed));
          commit(draft);
          render();
          toast(t('s.imported'));
        } catch {
          toast(t('s.importError'), true);
        }
      },
    });
    const reset = h('button', { type: 'button', class: 'btn btn-danger' }, t('s.reset'));
    confirmClick(reset, () => t('s.resetConfirm'), () => {
      draft = structuredClone(sanitizeSettings());
      commit(draft);
      render();
    });
    return section(3, t('settings.backup'), h('div', { class: 'row-actions' },
      h('button', {
        type: 'button', class: 'btn',
        onclick: () => download('kerfquote-einstellungen.json', JSON.stringify(getSettings(), null, 2), 'application/json'),
      }, t('s.export')),
      h('button', { type: 'button', class: 'btn', onclick: () => importInput.click() }, t('s.import')),
      importInput, reset));
  }

  function render() {
    const t = getT();
    clear(body).append(companySection(t), calcSection(t), materialsSection(t), backupSection(t));
  }

  body.addEventListener('change', (e) => {
    const el = e.target;
    const path = el.dataset?.path;
    if (!path || !draft) return;
    let value = el.value;
    if (el.dataset.type === 'num') value = el.value === '' ? NaN : Number(el.value);
    else if (el.dataset.type === 'list') value = el.value.split(/[\s,;]+/).filter(Boolean).map(Number);
    setPath(draft, path, value);
    commit(draft);
    const material = /^materials\.(\d+)\.name$/.exec(path);
    if (material) body.querySelector(`#s-m${material[1]}-summary`).textContent = value || getT()('s.newMaterial');
  });

  return {
    open() {
      draft = structuredClone(getSettings());
      render();
      dialog.showModal();
    },
    /** nach Sprach- oder Lizenzwechsel neu zeichnen, falls der Dialog offen ist */
    refresh() {
      if (dialog.open) render();
    },
  };
}
