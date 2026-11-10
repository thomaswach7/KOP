// Kleine DOM-Helfer. Inhalte aus Dateien (Layernamen, Dateinamen) werden grundsätzlich
// als Text eingefügt, nie als HTML – so kann eine präparierte DXF-Datei kein Skript einschleusen.

import { previewData } from './preview-data.js';

export const $ = (selector, root = document) => root.querySelector(selector);

const AS_PROPERTY = new Set(['value', 'checked', 'selected', 'disabled', 'hidden', 'open', 'textContent', 'htmlFor', 'required']);

/** h('button', { class: 'btn', onclick: fn }, 'Text') */
export function h(tag, props, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(props ?? {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === 'class') el.className = value;
    else if (key === 'dataset') Object.assign(el.dataset, value);
    else if (key.startsWith('on') && typeof value === 'function') el.addEventListener(key.slice(2), value);
    else if (AS_PROPERTY.has(key)) el[key] = value;
    else el.setAttribute(key, value === true ? '' : String(value));
  }
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    el.append(child instanceof Node ? child : String(child));
  }
  return el;
}

export function clear(el) {
  el.replaceChildren();
  return el;
}

const SVG_NS = 'http://www.w3.org/2000/svg';

function svgEl(tag, attrs) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
}

/** SVG-Vorschau eines analysierten Teils oder null, wenn es keine Geometrie gibt. */
export function renderPreview(analysis) {
  const data = previewData(analysis);
  if (!data) return null;
  const svg = svgEl('svg', { viewBox: data.viewBox.join(' '), preserveAspectRatio: 'xMidYMid meet', 'aria-hidden': 'true' });
  if (data.fill) svg.append(svgEl('path', { class: 'pv-fill', d: data.fill, 'fill-rule': 'evenodd' }));
  if (data.outer) svg.append(svgEl('path', { class: 'pv-outer', d: data.outer }));
  if (data.inner) svg.append(svgEl('path', { class: 'pv-inner', d: data.inner }));
  if (data.open) svg.append(svgEl('path', { class: 'pv-open', d: data.open }));
  for (const [cx, cy] of data.gaps) svg.append(svgEl('circle', { class: 'pv-gap', cx, cy, r: data.markerRadius }));
  return svg;
}

/** Bietet Text als Datei zum Herunterladen an. */
export function download(fileName, text, mime) {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  const a = h('a', { href: url, download: fileName });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/**
 * Sicherheitsabfrage ohne confirm(): Der erste Klick "schärft" den Knopf und zeigt die
 * Rückfrage als Beschriftung, erst der zweite Klick innerhalb von 5 s führt die Aktion aus.
 */
export function confirmClick(button, getQuestion, action) {
  let timer = null;
  let original = '';
  const disarm = () => {
    clearTimeout(timer);
    timer = null;
    button.textContent = original;
    button.removeAttribute('data-armed');
  };
  button.addEventListener('click', () => {
    if (timer !== null) {
      disarm();
      action();
      return;
    }
    original = button.textContent;
    button.textContent = getQuestion();
    button.setAttribute('data-armed', '');
    timer = setTimeout(disarm, 5000);
  });
}
