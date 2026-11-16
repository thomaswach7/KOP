// Einzeldatei-Fassung im echten Browser: direkt als Datei geöffnet (file://, kein Webserver)
// und eingebettet in einen abgeschotteten Rahmen (sandbox), wie ihn Vorschau-Ansichten verwenden.
//   node --test tests/e2e/standalone.e2e.mjs      (Playwright und esbuild müssen installiert sein)

import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { buildStandalone } from '../../tools/build-standalone.mjs';
import { createPart, pricePart } from '../../src/ui/part.js';
import { sanitizeSettings } from '../../src/cost/defaults.js';
import { quoteTotals } from '../../src/cost/model.js';
import { createFormat } from '../../src/ui/format.js';

const { chromium } = createRequire(import.meta.url)('playwright');
const FILE = fileURLToPath(new URL('../../standalone/kerfquote.html', import.meta.url));
const FILE_URL = pathToFileURL(FILE).href;
const SAMPLES = fileURLToPath(new URL('../../samples/', import.meta.url));
const sampleFile = (name) => `${SAMPLES}${name}.dxf`;
const sampleText = (name) => readFileSync(sampleFile(name), 'utf8');
const norm = (s) => s.replace(/\s+/g, ' ').trim();

const settings = sanitizeSettings();
const de = createFormat('de', 'EUR');

let browser;
before(async () => { browser = await chromium.launch(); });
after(async () => { await browser?.close(); });

/** Öffnet die Datei direkt von der Platte. Jeder Fehler und jeder Zugriff auf eine weitere Adresse lässt den Test scheitern. */
async function openFile(query = '') {
  const context = await browser.newContext({ locale: 'de-DE', viewport: { width: 1440, height: 900 }, acceptDownloads: true });
  // Ersatz für den Druckdialog; meldet sich wie ein echter Browser mit beforeprint/afterprint
  await context.addInitScript(() => {
    window.print = () => {
      window.__printed = (window.__printed ?? 0) + 1;
      window.dispatchEvent(new Event('beforeprint'));
      window.dispatchEvent(new Event('afterprint'));
    };
  });
  const page = await context.newPage();
  const problems = [];
  const requests = [];
  page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) problems.push(`${m.type()}: ${m.text()}`); });
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`));
  page.on('requestfailed', (r) => problems.push(`requestfailed: ${r.url()}`));
  page.on('request', (r) => { if (!/^(data|blob):/.test(r.url())) requests.push(r.url()); });
  await page.goto(FILE_URL + query);
  await page.waitForSelector('html[data-ready="true"]');
  const done = async () => {
    assert.deepEqual(problems, [], 'keine Konsolen-/Seitenfehler');
    assert.deepEqual(requests, [FILE_URL + query], 'außer der Datei selbst wird nichts geladen');
    await context.close();
  };
  return { page, done };
}

const costRow = async (page, label) =>
  norm(await page.locator('#cost-table tr', { hasText: label }).locator('td.r').innerText());

test('Datei direkt geöffnet: Beispielteile laden ohne Netzwerk, Preise stimmen mit dem Rechenmodell', async () => {
  const { page, done } = await openFile();
  assert.equal(await page.locator('html').getAttribute('lang'), 'de');
  await page.click('#btn-sample');
  await page.waitForSelector('.part-item >> nth=1');
  assert.equal(await page.locator('.part-item').count(), 2);

  const flansch = pricePart(createPart('flansch.dxf', sampleText('flansch'), settings), settings);
  const halteblech = pricePart(createPart('halteblech.dxf', sampleText('halteblech'), settings), settings);
  assert.equal(await costRow(page, 'Stückpreis'), norm(de.money(flansch.price.unitPrice)));
  const totals = quoteTotals([flansch.price.total, halteblech.price.total], settings);
  assert.equal(norm(await page.locator('#quote-totals dd.grand').innerText()), norm(de.money(totals.gross)));
  assert.equal(await page.locator('#preview svg path.pv-outer').count(), 1);
  await done();
});

test('Datei direkt geöffnet: eigene DXF-Datei, Sprachwechsel und Link-Parameter', async () => {
  const { page, done } = await openFile();
  await page.setInputFiles('#file-input', [sampleFile('zoll-platte')]);
  await page.waitForSelector('.part-item');
  assert.equal(norm(await page.locator('#part-name').inputValue()), 'zoll-platte');
  const part = pricePart(createPart('zoll-platte.dxf', sampleText('zoll-platte'), settings), settings);
  assert.equal(await costRow(page, 'Stückpreis'), norm(de.money(part.price.unitPrice)));

  await page.selectOption('#lang', 'en');
  assert.equal(await page.locator('html').getAttribute('lang'), 'en');
  assert.equal(norm(await page.locator('#parts-h').innerText()), 'Parts');
  await page.click('#brand-link');
  assert.ok(page.url().startsWith(FILE_URL), 'das Logo führt nicht aus der Datei hinaus');
  await done();

  const english = await openFile('?lang=en');
  assert.equal(await english.page.locator('html').getAttribute('lang'), 'en');
  await english.done();
});

test('Datei direkt geöffnet: Angebot drucken und Einstellungen als Datei sichern', async () => {
  const { page, done } = await openFile();
  await page.click('#btn-sample');
  await page.waitForSelector('.part-item >> nth=1');
  await page.fill('#q-number', 'A-2026-0042');
  await page.click('#btn-print');
  assert.equal(await page.evaluate(() => window.__printed), 1);
  assert.equal(await page.locator('#print-root .doc-table tbody tr').count(), 2);
  assert.equal(await page.locator('#print-root .doc-thumb svg').count(), 2);
  await page.waitForTimeout(1300);
  assert.doesNotMatch(await page.locator('#toast').innerText(), /blockiert/, 'kein Hinweis auf blockiertes Drucken');
  const pdf = await page.pdf({ format: 'A4' });
  assert.ok(pdf.length > 5000, 'PDF wurde erzeugt');

  await page.click('#btn-settings');
  await page.locator('#dlg-settings summary', { hasText: 'Sicherung' }).click();
  const [download] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Einstellungen exportieren' }).click()]);
  assert.equal(download.suggestedFilename(), 'kerfquote-einstellungen.json');
  assert.deepEqual(JSON.parse(readFileSync(await download.path(), 'utf8')), settings);

  // Eine ungültige Lizenz wird auch ohne Server sauber abgelehnt
  await page.locator('#dlg-settings').getByRole('button', { name: 'Schließen' }).click();
  await page.click('#btn-license');
  await page.fill('#license-key', 'KQ1.abc.def');
  await page.click('#btn-activate');
  await page.waitForFunction(() => document.querySelector('#license-error').textContent.trim() !== '');
  assert.equal(norm(await page.locator('#btn-license').innerText()), 'Lizenz: Free');
  await done();
});

test('Im abgeschotteten Rahmen: App läuft ohne Speicher; blockiertes Drucken wird gemeldet', async () => {
  const context = await browser.newContext({ locale: 'de-DE', viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const html = await buildStandalone({ csp: false });
  // Nachbildung einer Vorschau-Umgebung: fremde Richtlinie des Gastgebers, Rahmen ohne Rechte außer Skripten
  await context.route('http://kerfquote.test/**', (route) => {
    if (route.request().url().endsWith('/app.html')) {
      return route.fulfill({
        contentType: 'text/html; charset=utf-8',
        headers: { 'Content-Security-Policy': "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:" },
        body: html,
      });
    }
    return route.fulfill({
      contentType: 'text/html; charset=utf-8',
      body: '<!doctype html><html lang="de"><title>Rahmen</title><body style="margin:0"><iframe title="KerfQuote" sandbox="allow-scripts" src="/app.html" style="border:0;width:100%;height:1000px"></iframe></body></html>',
    });
  });
  const problems = [];
  page.on('console', (m) => {
    if (!['error', 'warning'].includes(m.type())) return;
    if (/Ignored call to 'print\(\)'/.test(m.text())) return; // genau das wird hier geprüft
    problems.push(`${m.type()}: ${m.text()}`);
  });
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`));
  await page.goto('http://kerfquote.test/');
  const app = page.frameLocator('iframe');
  await app.locator('html[data-ready="true"]').waitFor();

  await app.locator('#btn-sample').click();
  await app.locator('.part-item').nth(1).waitFor();
  await app.locator('#file-input').setInputFiles([sampleFile('zoll-platte')]);
  await app.locator('#toast', { hasText: 'kostenlose Version erlaubt 2 Positionen' }).waitFor();
  const flansch = pricePart(createPart('flansch.dxf', sampleText('flansch'), settings), settings);
  await app.locator('.part-item').first().click();
  assert.equal(norm(await app.locator('#cost-table tr', { hasText: 'Stückpreis' }).locator('td.r').innerText()), norm(de.money(flansch.price.unitPrice)));

  // Einstellungen wirken auch ohne dauerhaften Speicher
  await app.locator('#btn-settings').click();
  await app.locator('#dlg-settings summary', { hasText: 'Kalkulation' }).click();
  await app.locator('#s-vat').fill('20');
  await app.locator('#s-vat').blur();
  await app.locator('#dlg-settings').getByRole('button', { name: 'Schließen' }).click();
  assert.match(norm(await app.locator('#quote-totals').innerText()), /MwSt\. 20 %/);

  await app.locator('#btn-print').click();
  await app.locator('#toast', { hasText: 'Drucken wurde blockiert' }).waitFor({ timeout: 5000 });
  assert.deepEqual(problems, [], 'keine Konsolen-/Seitenfehler');
  await context.close();
});
