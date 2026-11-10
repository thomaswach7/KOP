// End-to-End-Test der App in einem echten Browser (Chromium über Playwright).
//   node --test tests/e2e/app.e2e.mjs        (Playwright muss installiert sein)
// Die erwarteten Preise werden mit dem Rechenmodell in Node berechnet und mit der
// Anzeige im Browser verglichen – so fällt jeder Verdrahtungsfehler der Oberfläche auf.

import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createStaticServer } from '../../tools/serve.mjs';
import { generateKeyPair, issueLicense, publicKeyModule } from '../../tools/license.mjs';
import { createPart, pricePart } from '../../src/ui/part.js';
import { sanitizeSettings } from '../../src/cost/defaults.js';
import { quoteTotals } from '../../src/cost/model.js';
import { createFormat } from '../../src/ui/format.js';

const { chromium } = createRequire(import.meta.url)('playwright');
const SAMPLES = fileURLToPath(new URL('../../samples/', import.meta.url));
const sampleFile = (name) => `${SAMPLES}${name}.dxf`;
const sampleText = (name) => readFileSync(sampleFile(name), 'utf8');
const norm = (s) => s.replace(/\s+/g, ' ').trim();

const settings = sanitizeSettings();
const de = createFormat('de', 'EUR');
const en = createFormat('en', 'EUR');

let server;
let browser;
let base;
let keys;
let proToken;
let expiredToken;

before(async () => {
  server = createStaticServer();
  await new Promise((resolve) => server.listen(0, resolve));
  base = `http://localhost:${server.address().port}`;
  browser = await chromium.launch();
  keys = await generateKeyPair();
  proToken = await issueLicense({ name: 'Testkunde GmbH', plan: 'pro', exp: '2099-12-31', id: 'K-E2E' }, keys.privateJwk);
  expiredToken = await issueLicense({ name: 'Altkunde', plan: 'pro', exp: '2020-01-01', id: 'K-OLD' }, keys.privateJwk);
});

after(async () => {
  await browser?.close();
  server?.close();
});

/** Öffnet die App in einem frischen Browser-Profil. Jeder Konsolen- oder Seitenfehler lässt den Test scheitern. */
async function openApp({ locale = 'de-DE', pro = false, viewport = { width: 1440, height: 900 } } = {}) {
  const context = await browser.newContext({ locale, viewport, acceptDownloads: true });
  // Der Test nutzt ein eigenes Schlüsselpaar; der echte öffentliche Schlüssel wird nur für diesen Lauf ersetzt.
  await context.route('**/src/license-public-key.js', (route) =>
    route.fulfill({ contentType: 'text/javascript', body: publicKeyModule(keys.publicJwk) }));
  await context.addInitScript(() => { window.print = () => { window.__printed = (window.__printed ?? 0) + 1; }; });
  if (pro) {
    await context.addInitScript((token) => {
      if (!localStorage.getItem('kerfquote.license')) localStorage.setItem('kerfquote.license', JSON.stringify(token));
    }, proToken);
  }
  const page = await context.newPage();
  const problems = [];
  page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) problems.push(`${m.type()}: ${m.text()}`); });
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`));
  page.on('requestfailed', (r) => problems.push(`requestfailed: ${r.url()}`));
  await page.goto(`${base}/app/`);
  await page.waitForSelector('html[data-ready="true"]');
  const done = async () => {
    assert.deepEqual(problems, [], 'keine Konsolen-/Seitenfehler');
    await context.close();
  };
  return { page, context, done };
}

const metric = async (page, label) =>
  norm(await page.locator('.metric', { has: page.locator('dt', { hasText: label }) }).locator('dd').innerText());
const costRow = async (page, label) =>
  norm(await page.locator('#cost-table tr', { hasText: label }).locator('td.r').innerText());
const upload = (page, ...files) => page.setInputFiles('#file-input', files);

test('Start: leerer Zustand, deutsche Oberfläche, keine Fehler', async () => {
  const { page, done } = await openApp();
  assert.equal(await page.title(), 'KerfQuote – Zuschnitt-Kalkulation aus DXF');
  assert.equal(await page.locator('html').getAttribute('lang'), 'de');
  assert.ok(await page.locator('#detail-empty').isVisible());
  assert.ok(await page.locator('#detail').isHidden());
  assert.ok(await page.locator('#btn-print').isDisabled());
  assert.equal(norm(await page.locator('#btn-license').innerText()), 'Lizenz: Free');
  assert.match(await page.locator('#q-number').inputValue(), /^A-\d{8}-01$/);
  await done();
});

test('Beispielteile: Kennwerte und Preise stimmen mit dem Rechenmodell überein', async () => {
  const { page, done } = await openApp();
  await page.click('#btn-sample');
  await page.waitForSelector('.part-item >> nth=1');
  assert.equal(await page.locator('.part-item').count(), 2);

  const flansch = createPart('flansch.dxf', sampleText('flansch'), settings);
  const row = pricePart(flansch, settings);
  assert.equal(await metric(page, 'Schnittlänge'), norm(de.length(flansch.analysis.cutLength)));
  assert.equal(await metric(page, 'Schnittlänge'), '672,3 mm');
  assert.equal(await metric(page, 'Einstiche'), '8');
  assert.equal(await metric(page, 'Konturen'), '8 geschlossen, 0 offen');
  assert.equal(await metric(page, 'Abmessungen'), '120 × 120 mm');
  assert.equal(await metric(page, 'Gewicht'), norm(de.weight(row.price.weightKg)));
  assert.equal(await costRow(page, 'Stückpreis'), norm(de.money(row.price.unitPrice)));
  assert.equal(await page.locator('#preview svg path.pv-outer').count(), 1);
  assert.equal(await page.locator('#preview svg path.pv-inner').count(), 1);
  assert.equal(await page.locator('#preview svg path.pv-open').count(), 0);
  assert.equal(await page.locator('#warnings li.w-ok').count(), 1);

  // Menge 10, Dicke 5 mm, 2 Biegungen, 0,50 Zusatz
  await page.fill('#p-qty', '10');
  await page.selectOption('#p-thickness', '5');
  await page.fill('#p-bends', '2');
  await page.fill('#p-extra', '0.5');
  Object.assign(flansch, { qty: 10, thickness: 5, bends: 2, extra: 0.5 });
  const changed = pricePart(flansch, settings);
  assert.equal(await costRow(page, 'Stückpreis'), norm(de.money(changed.price.unitPrice)));
  assert.equal(await costRow(page, 'Gesamt (10 Stk.)'), norm(de.money(changed.price.total)));
  assert.equal(await costRow(page, 'Biegen'), norm(de.money(3)));
  assert.equal(norm(await page.locator('#breaks-table tr.is-current td').first().innerText()), '10');

  // Angebotssumme = Summe beider Positionen + MwSt.
  const halteblech = pricePart(createPart('halteblech.dxf', sampleText('halteblech'), settings), settings);
  const totals = quoteTotals([changed.price.total, halteblech.price.total], settings);
  assert.equal(norm(await page.locator('#quote-totals dd.grand').innerText()), norm(de.money(totals.gross)));
  assert.equal(await page.locator('#quote-table tbody tr').count(), 2);

  // Material wechseln: Dickenliste passt sich an, Preis folgt dem Modell
  await page.selectOption('#p-material', 'almg3');
  flansch.materialId = 'almg3';
  const alu = pricePart(flansch, settings);
  assert.equal(await page.locator('#p-thickness').inputValue(), '5');
  assert.equal(await costRow(page, 'Stückpreis'), norm(de.money(alu.price.unitPrice)));
  await done();
});

test('ungültige Mengen werden nicht übernommen (Feld bleibt markiert, Preis bleibt)', async () => {
  const { page, done } = await openApp();
  await page.click('#btn-sample');
  await page.waitForSelector('.part-item');
  const before = await costRow(page, 'Stückpreis');
  for (const bad of ['0', '-3', '2.5', '']) {
    await page.fill('#p-qty', bad);
    assert.equal(await costRow(page, 'Stückpreis'), before, `Menge "${bad}"`);
  }
  assert.equal(await page.locator('#p-qty').evaluate((el) => el.checkValidity()), false);
  await done();
});

test('Layer: Hilfslinien sind vorab abgewählt; zuschalten erzeugt eine offene Kontur mit Warnung', async () => {
  const { page, done } = await openApp();
  await upload(page, sampleFile('halteblech'));
  await page.waitForSelector('.part-item');
  const hilfs = page.locator('#layers li', { hasText: 'HILFSLINIE' }).locator('input');
  assert.equal(await hilfs.isChecked(), false);
  assert.equal(await metric(page, 'Konturen'), '5 geschlossen, 0 offen');
  await hilfs.check();
  assert.equal(await metric(page, 'Konturen'), '5 geschlossen, 1 offen');
  assert.equal(await page.locator('#warnings li.w-warn').count(), 1);
  assert.equal(await page.locator('#preview svg path.pv-open').count(), 1);
  assert.equal(await page.locator('#preview svg circle.pv-gap').count(), 2);
  await hilfs.uncheck();
  assert.equal(await metric(page, 'Konturen'), '5 geschlossen, 0 offen');
  assert.match(norm(await page.locator('#warnings').innerText()), /Nicht geschnitten: 1× TEXT/);
  await done();
});

test('offene Kontur: Warnung und Markierung; höhere Lückentoleranz schließt sie', async () => {
  const { page, done } = await openApp();
  await upload(page, sampleFile('offene-kontur'));
  await page.waitForSelector('.part-item');
  assert.equal(await metric(page, 'Konturen'), '1 geschlossen, 1 offen');
  const text = norm(await page.locator('#warnings').innerText());
  assert.match(text, /1 offene Kontur/);
  assert.match(text, /1 doppelte Elemente entfernt/);
  assert.match(text, /1 Elemente mit Länge 0 entfernt/);
  await page.fill('#p-tol', '1');
  assert.equal(await metric(page, 'Konturen'), '2 geschlossen, 0 offen');
  assert.equal(await page.locator('#warnings li.w-ok').count(), 1);
  await done();
});

test('Einheit: Zoll-Datei wird erkannt; manuelle Umstellung skaliert die Abmessungen', async () => {
  const { page, done } = await openApp();
  await upload(page, sampleFile('zoll-platte'));
  await page.waitForSelector('.part-item');
  assert.equal(await metric(page, 'Abmessungen'), '101,6 × 50,8 mm');
  assert.equal(norm(await page.locator('#p-units option:checked').innerText()), 'Automatisch (Zoll)');
  await page.selectOption('#p-units', 'mm');
  assert.equal(await metric(page, 'Abmessungen'), '4 × 2 mm');
  await page.selectOption('#p-units', 'auto');
  assert.equal(await metric(page, 'Abmessungen'), '101,6 × 50,8 mm');
  await done();
});

test('Free: dritte Position wird abgelehnt; unlesbare und binäre Dateien melden einen Fehler', async () => {
  const { page, done } = await openApp();
  await upload(page, sampleFile('flansch'), sampleFile('halteblech'), sampleFile('zoll-platte'));
  await page.waitForSelector('.part-item >> nth=1');
  assert.equal(await page.locator('.part-item').count(), 2);
  assert.match(await page.locator('#toast').innerText(), /kostenlose Version erlaubt 2 Positionen/);

  await page.locator('.part-remove').first().click();
  assert.equal(await page.locator('.part-item').count(), 1);
  await upload(page, { name: 'notiz.dxf', mimeType: 'text/plain', buffer: Buffer.from('Das ist keine Zeichnung') });
  await page.waitForFunction(() => document.querySelector('#toast').textContent.includes('notiz.dxf'));
  assert.match(await page.locator('#toast').innerText(), /notiz\.dxf: Das ist keine lesbare DXF-Datei/);
  await upload(page, { name: 'binaer.dxf', mimeType: 'application/dxf', buffer: Buffer.from('AutoCAD Binary DXF\r\n\x1a\x00\x00\xff\xfe') });
  await page.waitForFunction(() => document.querySelector('#toast').textContent.includes('binaer.dxf'));
  assert.match(await page.locator('#toast').innerText(), /Binäres DXF wird nicht unterstützt/);
  await upload(page, { name: 'nurtext.dxf', mimeType: 'application/dxf', buffer: Buffer.from('0\nSECTION\n2\nENTITIES\n0\nTEXT\n10\n0\n20\n0\n1\nHallo\n0\nENDSEC\n0\nEOF\n') });
  await page.waitForFunction(() => document.querySelector('#toast').textContent.includes('nurtext.dxf'));
  assert.match(await page.locator('#toast').innerText(), /keine Linien, Bögen oder Polylinien/);
  assert.equal(await page.locator('.part-item').count(), 1);
  await done();
});

test('Dateien per Drag-and-drop auf die Seite ziehen', async () => {
  const { page, done } = await openApp();
  const data = await page.evaluateHandle((text) => {
    const dt = new DataTransfer();
    dt.items.add(new File([text], 'gezogen.dxf', { type: 'application/dxf' }));
    return dt;
  }, sampleText('r12-polyline'));
  await page.dispatchEvent('body', 'dragover', { dataTransfer: data });
  assert.match(await page.locator('#dropzone').getAttribute('class'), /is-over/);
  await page.dispatchEvent('body', 'drop', { dataTransfer: data });
  await page.waitForSelector('.part-item');
  assert.equal(norm(await page.locator('.part-name').innerText()), 'gezogen');
  assert.match(norm(await page.locator('#warnings').innerText()), /Die Datei nennt keine Einheit\. Angenommen: mm/);
  await done();
});

test('Sicherheit: HTML in Datei- und Layernamen wird als Text angezeigt, nicht ausgeführt', async () => {
  const { page, done } = await openApp();
  const evil = '<img src=x onerror="window.__xss=1">';
  const dxf = `0\nSECTION\n2\nENTITIES\n0\nCIRCLE\n8\n${evil}\n10\n0\n20\n0\n40\n5\n0\nENDSEC\n0\nEOF\n`;
  await upload(page, { name: `${evil}.dxf`, mimeType: 'application/dxf', buffer: Buffer.from(dxf) });
  await page.waitForSelector('.part-item');
  assert.equal(norm(await page.locator('.layer-name').innerText()), evil);
  assert.equal(await page.locator('main img').count(), 0);
  await page.fill('#q-customer', evil);
  await page.click('#btn-print');
  assert.equal(await page.locator('#print-root img').count(), 0);
  assert.equal(await page.evaluate(() => window.__xss), undefined);
  await done();
});

test('Lizenz: falsche Schlüssel werden abgelehnt, gültiger schaltet Pro frei und bleibt nach Neuladen', async () => {
  const { page, done } = await openApp();
  await page.click('#btn-license');
  assert.ok(await page.locator('#dlg-license').evaluate((d) => d.open && d.matches(':modal')));
  assert.equal(norm(await page.locator('#license-status').innerText()), 'Sie nutzen die kostenlose Version.');

  await page.fill('#license-key', 'kein-schluessel');
  await page.click('#btn-activate');
  await page.waitForFunction(() => document.querySelector('#license-error').textContent !== '');
  assert.match(await page.locator('#license-error').innerText(), /kein gültiger Lizenzschlüssel/);

  const forged = `${proToken.slice(0, -6)}AAAAAA`;
  await page.fill('#license-key', forged);
  await page.click('#btn-activate');
  await page.waitForFunction(() => document.querySelector('#license-error').textContent.includes('ungültig'));

  await page.fill('#license-key', expiredToken);
  await page.click('#btn-activate');
  await page.waitForFunction(() => document.querySelector('#license-error').textContent.includes('abgelaufen'));
  assert.match(await page.locator('#license-error').innerText(), /01\.01\.2020 abgelaufen/);
  assert.equal(norm(await page.locator('#btn-license').innerText()), 'Lizenz: Free');

  await page.fill('#license-key', `  ${proToken.slice(0, 40)}\n${proToken.slice(40)}  `);
  await page.click('#btn-activate');
  await page.waitForFunction(() => document.querySelector('#btn-license').textContent.includes('Pro'));
  assert.match(norm(await page.locator('#license-status').innerText()), /Pro ist aktiv – lizenziert für Testkunde GmbH, gültig bis 31\.12\.2099/);
  assert.equal(await page.locator('#license-error').innerText(), '');
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('#dlg-license').evaluate((d) => d.open), false);
  assert.ok(await page.locator('#free-note').isHidden());

  await page.reload();
  await page.waitForSelector('html[data-ready="true"]');
  await page.waitForFunction(() => document.querySelector('#btn-license').textContent.includes('Pro'));

  // Pro: mehr als zwei Positionen
  await upload(page, sampleFile('flansch'), sampleFile('halteblech'), sampleFile('zoll-platte'), sampleFile('block-insert'));
  await page.waitForSelector('.part-item >> nth=3');
  assert.equal(await page.locator('.part-item').count(), 4);

  await page.click('#btn-license');
  await page.click('#btn-remove-license');
  await page.waitForFunction(() => document.querySelector('#btn-license').textContent.includes('Free'));
  assert.equal(await page.evaluate(() => localStorage.getItem('kerfquote.license')), null);
  await done();
});

test('CSV-Export: in Free gesperrt, in Pro lädt er die Positionen als Datei', async () => {
  const free = await openApp();
  await free.page.click('#btn-sample');
  await free.page.waitForSelector('.part-item');
  await free.page.click('#btn-csv');
  assert.match(await free.page.locator('#toast').innerText(), /CSV-Export ist eine Pro-Funktion/);
  assert.ok(await free.page.locator('#dlg-license').evaluate((d) => d.open));
  await free.done();

  const { page, done } = await openApp({ pro: true });
  await page.waitForFunction(() => document.querySelector('#btn-license').textContent.includes('Pro'));
  await page.click('#btn-sample');
  await page.waitForSelector('.part-item >> nth=1');
  await page.fill('#q-number', 'A 2026/17');
  const [download] = await Promise.all([page.waitForEvent('download'), page.click('#btn-csv')]);
  assert.equal(download.suggestedFilename(), 'A_2026_17.csv');
  const csv = readFileSync(await download.path(), 'utf8');
  const lines = csv.replace(String.fromCharCode(0xfeff), '').trim().split('\r\n');
  assert.equal(lines[0], 'Pos;Bezeichnung;Material;Dicke (mm);Menge;Schnittlänge (mm);Einstiche;Gewicht (kg);Einzelpreis;Gesamt');
  assert.equal(lines.length, 3);
  assert.equal(lines[1], '1;flansch;S235 (Baustahl);3;1;672,3;8;0,228;32,41;32,41');
  await done();
});

test('Einstellungen: Stundensatz und Währung wirken sofort und bleiben nach dem Neuladen erhalten', async () => {
  const { page, done } = await openApp();
  await page.click('#btn-sample');
  await page.waitForSelector('.part-item');
  await page.click('#btn-settings');
  assert.ok(await page.locator('#dlg-settings').evaluate((d) => d.matches(':modal')));
  await page.locator('#dlg-settings summary', { hasText: 'Kalkulation' }).click();
  await page.fill('#s-rate', '240');
  await page.locator('#s-rate').blur();
  await page.fill('#s-setup', '0');
  await page.locator('#s-setup').blur();
  await page.selectOption('#s-currency', 'CHF');
  // die Abschnitte sind ein exklusives Akkordeon: "Firma" ist zugeklappt, solange "Kalkulation" offen ist
  assert.ok(await page.locator('#s-company').isHidden());
  await page.locator('#dlg-settings summary', { hasText: 'Firma' }).click();
  await page.fill('#s-company', 'Blechwerk Muster GmbH');
  await page.locator('#dlg-settings button[value="close"]').click();

  const custom = sanitizeSettings({ ...settings, machineRate: 240, setupCost: 0, currency: 'CHF' });
  const chf = createFormat('de', 'CHF');
  const expected = pricePart(createPart('flansch.dxf', sampleText('flansch'), custom), custom);
  assert.equal(await costRow(page, 'Stückpreis'), norm(chf.money(expected.price.unitPrice)));
  // Angebot unter Mindestauftragswert → Zuschlag erscheint
  assert.ok(await page.locator('#quote-totals dt', { hasText: 'Mindermengenzuschlag' }).isVisible());

  await page.reload();
  await page.waitForSelector('html[data-ready="true"]');
  await page.click('#btn-settings');
  assert.equal(await page.locator('#s-company').inputValue(), 'Blechwerk Muster GmbH');
  await page.locator('#dlg-settings summary', { hasText: 'Kalkulation' }).click();
  assert.equal(await page.locator('#s-rate').inputValue(), '240');
  assert.equal(await page.locator('#s-currency').inputValue(), 'CHF');
  await done();
});

test('Einstellungen: Material anlegen, Dicke ergänzen, zurücksetzen mit Rückfrage', async () => {
  const { page, done } = await openApp();
  await page.click('#btn-sample');
  await page.waitForSelector('.part-item');
  await page.click('#btn-settings');
  await page.locator('#dlg-settings summary', { hasText: 'Materialien' }).click();
  await page.getByRole('button', { name: 'Material hinzufügen' }).click();
  await page.fill('#s-m3-name', 'Messing CuZn37');
  await page.locator('#s-m3-name').blur();
  assert.equal(norm(await page.locator('#s-m3-summary').innerText()), 'Messing CuZn37');
  await page.locator('details.mat[open]').getByRole('button', { name: 'Dicke hinzufügen' }).click();
  await page.fill('#s-m3-t1', '2');
  await page.fill('#s-m3-v1', '3000');
  await page.fill('#s-m3-p1', '0.4');
  await page.locator('#s-m3-p1').blur();
  await page.locator('#dlg-settings button[value="close"]').click();

  assert.equal(await page.locator('#p-material option').count(), 4);
  await page.selectOption('#p-material', { label: 'Messing CuZn37' });
  assert.deepEqual(await page.locator('#p-thickness option').allInnerTexts(), ['1', '2']);
  assert.match(await costRow(page, 'Stückpreis'), /€$/);

  await page.click('#btn-settings');
  await page.locator('#dlg-settings summary', { hasText: 'Sicherung' }).click();
  const reset = page.getByRole('button', { name: 'Auf Standardwerte zurücksetzen' });
  await reset.click();
  await page.getByRole('button', { name: 'Alle Einstellungen auf die Standardwerte zurücksetzen?' }).click();
  await page.locator('#dlg-settings button[value="close"]').click();
  assert.equal(await page.locator('#p-material option').count(), 3);
  assert.equal(await page.locator('#p-material').inputValue(), 's235');
  await done();
});

// 1×1-Pixel-PNG als Test-Logo
const TINY_PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');

test('Logo: in Free gesperrt; in Pro erscheint es im Angebot und lässt sich wieder entfernen', async () => {
  const free = await openApp();
  await free.page.click('#btn-settings');
  assert.ok(await free.page.locator('#s-logo').isDisabled());
  assert.match(norm(await free.page.locator('#dlg-settings').innerText()), /eigenes Logo im Angebot ist eine Pro-Funktion/);
  await free.done();

  const { page, done } = await openApp({ pro: true });
  await page.waitForFunction(() => document.querySelector('#btn-license').textContent.includes('Pro'));
  await page.click('#btn-sample');
  await page.waitForSelector('.part-item');
  await page.click('#btn-settings');
  await page.fill('#s-company', 'Blechwerk Muster GmbH');
  await page.locator('#s-company').blur();
  assert.ok(await page.locator('#s-logo').isEnabled());
  await page.setInputFiles('#s-logo', { name: 'logo.png', mimeType: 'image/png', buffer: TINY_PNG });
  await page.waitForSelector('#dlg-settings img.logo-preview');
  // zu große Datei und falsches Format werden abgelehnt, das vorhandene Logo bleibt
  await page.setInputFiles('#s-logo', { name: 'riesig.png', mimeType: 'image/png', buffer: Buffer.alloc(300 * 1024, 1) });
  await page.waitForFunction(() => document.querySelector('#toast').textContent.includes('zu groß'));
  await page.setInputFiles('#s-logo', { name: 'text.png', mimeType: 'text/plain', buffer: Buffer.from('kein Bild') });
  await page.waitForFunction(() => document.querySelector('#toast').classList.contains('is-error'));
  assert.equal(await page.locator('#dlg-settings img.logo-preview').count(), 1);
  await page.locator('#dlg-settings button[value="close"]').click();

  await page.click('#btn-print');
  const logo = page.locator('#print-root img.doc-logo');
  assert.equal(await logo.count(), 1);
  assert.match(await logo.getAttribute('src'), /^data:image\/png;base64,/);
  assert.equal(await logo.getAttribute('alt'), 'Blechwerk Muster GmbH');

  await page.click('#btn-settings');
  await page.getByRole('button', { name: 'Logo entfernen' }).click();
  assert.equal(await page.locator('#dlg-settings img.logo-preview').count(), 0);
  await page.locator('#dlg-settings button[value="close"]').click();
  await page.click('#btn-print');
  assert.equal(await page.locator('#print-root img').count(), 0);
  assert.equal(norm(await page.locator('#print-root .doc-company').innerText()), 'Blechwerk Muster GmbH');
  await done();
});

test('Einstellungen: Staffelmengen, Zeile und Material löschen, Export und Import', async () => {
  const { page, done } = await openApp();
  await page.click('#btn-sample');
  await page.waitForSelector('.part-item');
  await page.click('#btn-settings');
  await page.locator('#dlg-settings summary', { hasText: 'Kalkulation' }).click();
  await page.fill('#s-quantities', '1, 20; 300');
  await page.locator('#s-quantities').blur();
  await page.fill('#s-vat', '20');
  await page.locator('#s-vat').blur();

  await page.locator('#dlg-settings summary', { hasText: 'Materialien' }).click();
  await page.locator('details.mat summary').first().click();
  assert.equal(await page.locator('details.mat[open] tbody tr').count(), 12);
  await page.getByRole('button', { name: 'Zeile entfernen 1', exact: true }).click();
  assert.equal(await page.locator('details.mat[open] tbody tr').count(), 11);
  assert.equal(await page.locator('#s-m0-t0').inputValue(), '1.5');
  // ungültige Eingabe: Feld wird markiert, die Zeile fällt bis zur Korrektur aus der Kalkulation
  await page.fill('#s-m0-v0', '');
  await page.locator('#s-m0-v0').blur();
  assert.equal(await page.locator('#s-m0-v0').evaluate((el) => el.matches(':user-invalid')), true);
  await page.fill('#s-m0-v0', '7000');
  await page.locator('#s-m0-v0').blur();

  await page.locator('details.mat summary').nth(2).click();
  await page.getByRole('button', { name: 'Material löschen' }).click();
  assert.equal(await page.locator('details.mat').count(), 2);

  await page.locator('#dlg-settings summary', { hasText: 'Sicherung' }).click();
  const [download] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Einstellungen exportieren' }).click()]);
  assert.equal(download.suggestedFilename(), 'kerfquote-einstellungen.json');
  const exported = JSON.parse(readFileSync(await download.path(), 'utf8'));
  assert.deepEqual(exported.quantities, [1, 20, 300]);
  assert.equal(exported.vatPct, 20);
  assert.equal(exported.materials.length, 2);
  assert.deepEqual(exported.materials[0].thicknesses[0], { t: 1.5, speed: 7000, pierce: 0.3 });
  assert.deepEqual(exported, sanitizeSettings(exported), 'Export ist bereits vollständig und gültig');
  await page.locator('#dlg-settings button[value="close"]').click();

  assert.deepEqual(await page.locator('#breaks-table tbody td:first-child').allInnerTexts(), ['1', '20', '300']);
  assert.ok(await page.locator('#quote-totals dt', { hasText: 'MwSt. 20 %' }).isVisible());
  assert.equal(await page.locator('#p-material option').count(), 2);
  assert.deepEqual((await page.locator('#p-thickness option').allInnerTexts()).slice(0, 2), ['1,5', '2']);

  // Import: geänderte Datei einlesen; kaputte Datei meldet einen Fehler und ändert nichts
  await page.click('#btn-settings');
  await page.locator('#dlg-settings summary', { hasText: 'Sicherung' }).click();
  const importInput = page.locator('#dlg-settings input[type="file"][accept*="json"]');
  await importInput.setInputFiles({ name: 'kaputt.json', mimeType: 'application/json', buffer: Buffer.from('{ kein json') });
  await page.waitForFunction(() => document.querySelector('#toast').textContent.includes('konnte nicht gelesen werden'));
  const changed = { ...exported, machineRate: 99, company: { ...exported.company, name: 'Import GmbH' }, boese: '<script>' };
  await page.locator('#dlg-settings input[type="file"][accept*="json"]')
    .setInputFiles({ name: 'neu.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(changed)) });
  await page.waitForFunction(() => document.querySelector('#toast').textContent.includes('Einstellungen übernommen'));
  await page.locator('#dlg-settings summary', { hasText: 'Firma' }).click();
  assert.equal(await page.locator('#s-company').inputValue(), 'Import GmbH');
  const stored = await page.evaluate(() => JSON.parse(localStorage.getItem('kerfquote.settings.v1')));
  assert.equal(stored.machineRate, 99);
  assert.equal('boese' in stored, false);
  await done();
});

test('Sprache: Umschalten auf Englisch übersetzt Oberfläche und Zahlenformat', async () => {
  const { page, done } = await openApp();
  await page.click('#btn-sample');
  await page.waitForSelector('.part-item');
  await page.selectOption('#lang', 'en');
  assert.equal(await page.locator('html').getAttribute('lang'), 'en');
  assert.equal(norm(await page.locator('#parts-h').innerText()), 'Parts');
  assert.equal(await metric(page, 'Cut length'), '672.3 mm');
  assert.equal(await metric(page, 'Contours'), '8 closed, 0 open');
  const expected = pricePart(createPart('flansch.dxf', sampleText('flansch'), settings), settings);
  assert.equal(await costRow(page, 'Unit price'), norm(en.money(expected.price.unitPrice)));
  assert.equal(norm(await page.locator('#btn-license').innerText()), 'License: Free');
  await page.reload();
  await page.waitForSelector('html[data-ready="true"]');
  assert.equal(await page.locator('#lang').inputValue(), 'en');
  assert.equal(norm(await page.locator('#btn-sample').innerText()), 'Load sample parts');
  await done();

  const english = await openApp({ locale: 'en-US' });
  assert.equal(await english.page.locator('html').getAttribute('lang'), 'en');
  await english.done();
});

test('Angebot drucken: Dokument enthält Kunde, Positionen und Summen; Free mit Hinweis, Pro ohne', async () => {
  const { page, done } = await openApp();
  await page.click('#btn-sample');
  await page.waitForSelector('.part-item >> nth=1');
  await page.fill('#q-customer', 'Maschinenbau Beispiel AG\nIndustriestraße 5\n12345 Musterstadt');
  await page.fill('#q-number', 'A-2026-0042');
  await page.fill('#q-date', '2026-11-10');
  await page.click('#btn-print');
  assert.equal(await page.evaluate(() => window.__printed), 1);
  await page.emulateMedia({ media: 'print' });
  assert.ok(await page.locator('#print-root').isVisible());
  assert.ok(await page.locator('.topbar').isHidden());
  const doc = norm(await page.locator('#print-root').innerText());
  assert.match(doc, /Angebot A-2026-0042/);
  assert.match(doc, /Maschinenbau Beispiel AG/);
  assert.match(doc, /Datum 10\.11\.2026/);
  assert.match(doc, /Gültig bis 10\.12\.2026/);
  assert.match(doc, /flansch S235 \(Baustahl\), 3 mm · 120 × 120 mm · 0,228 kg/);
  assert.match(doc, /Erstellt mit der kostenlosen Version von KerfQuote/);
  assert.equal(await page.locator('#print-root .doc-table tbody tr').count(), 2);
  assert.equal(await page.locator('#print-root .doc-thumb svg').count(), 2);
  const gross = norm(await page.locator('#print-root .doc-totals tr.grand td.r').innerText());
  await page.emulateMedia({ media: 'screen' });
  assert.equal(gross, norm(await page.locator('#quote-totals dd.grand').innerText()));
  const pdf = await page.pdf({ format: 'A4' });
  assert.ok(pdf.length > 5000, 'PDF wurde erzeugt');
  await done();

  const pro = await openApp({ pro: true });
  await pro.page.waitForFunction(() => document.querySelector('#btn-license').textContent.includes('Pro'));
  await pro.page.click('#btn-sample');
  await pro.page.waitForSelector('.part-item');
  await pro.page.click('#btn-print');
  assert.doesNotMatch(await pro.page.locator('#print-root').innerHTML(), /kostenlosen Version/);
  await pro.done();
});

test('Angebot leeren fragt nach und entfernt dann alle Positionen', async () => {
  const { page, done } = await openApp();
  await page.click('#btn-sample');
  await page.waitForSelector('.part-item >> nth=1');
  await page.click('#btn-clear');
  assert.equal(norm(await page.locator('#btn-clear').innerText()), 'Alle Positionen aus dem Angebot entfernen?');
  assert.equal(await page.locator('.part-item').count(), 2, 'erster Klick löscht noch nichts');
  await page.click('#btn-clear');
  assert.equal(await page.locator('.part-item').count(), 0);
  assert.ok(await page.locator('#detail-empty').isVisible());
  assert.ok(await page.locator('#btn-print').isDisabled());
  await done();
});

test('schmale Bildschirme: kein horizontales Scrollen (Smartphone-Breite)', async () => {
  const { page, done } = await openApp({ viewport: { width: 375, height: 800 } });
  await page.click('#btn-sample');
  await page.waitForSelector('.part-item');
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 0, `horizontaler Überlauf: ${overflow}px`);
  await done();
});
