// End-to-End-Test der Startseiten, Rechtstexte und der Barrierefreiheit.
//   node --test tests/e2e/site.e2e.mjs
// Der Barrierefreiheits-Test nutzt axe-core, falls installiert (sonst wird er übersprungen).

import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { createStaticServer } from '../../tools/serve.mjs';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
let axePath = null;
try { axePath = require.resolve('axe-core/axe.min.js'); } catch { /* optional */ }

const norm = (s) => s.replace(/\s+/g, ' ').trim();
let server;
let browser;
let base;

before(async () => {
  server = createStaticServer();
  await new Promise((resolve) => server.listen(0, resolve));
  base = `http://localhost:${server.address().port}`;
  browser = await chromium.launch();
});

after(async () => {
  await browser?.close();
  server?.close();
});

async function open(path, options = {}) {
  const context = await browser.newContext({ locale: 'de-DE', viewport: { width: 1280, height: 900 }, ...options });
  const page = await context.newPage();
  const problems = [];
  page.on('console', (m) => { if (['error', 'warning'].includes(m.type())) problems.push(`${m.type()}: ${m.text()}`); });
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`));
  page.on('requestfailed', (r) => problems.push(`requestfailed: ${r.url()}`));
  page.on('response', (r) => { if (r.status() >= 400) problems.push(`HTTP ${r.status()}: ${r.url()}`); });
  await page.goto(`${base}${path}`);
  return { page, context, done: async () => { assert.deepEqual(problems, [], 'keine Fehler'); await context.close(); } };
}

test('deutsche Startseite: Inhalt, strukturierte Daten und alle internen Links funktionieren', async () => {
  const { page, done } = await open('/');
  const title = await page.title();
  assert.equal(title, 'Laserschneiden kalkulieren aus der DXF-Datei – KerfQuote');
  assert.ok(title.length >= 45 && title.length <= 60, `Titel hat ${title.length} Zeichen`);
  assert.equal(await page.locator('html').getAttribute('lang'), 'de');
  assert.equal(await page.locator('h1').count(), 1);
  assert.equal(norm(await page.locator('h1').innerText()), 'Laserzuschnitte kalkulieren: vom DXF zum Angebot in 30 Sekunden.');
  const description = await page.locator('meta[name="description"]').getAttribute('content');
  assert.ok(description.length >= 140 && description.length <= 165, `Beschreibung hat ${description.length} Zeichen`);
  // Überschriften: genau eine H1, danach keine übersprungene Ebene
  const levels = await page.locator('h1, h2, h3').evaluateAll((hs) => hs.map((h) => Number(h.tagName[1])));
  assert.equal(levels[0], 1);
  levels.forEach((level, i) => { if (i > 0) assert.ok(level - levels[i - 1] <= 1, `Überschriftenebene springt bei Nr. ${i + 1}`); });

  const blocks = await page.locator('script[type="application/ld+json"]').allTextContents();
  const data = blocks.map((b) => JSON.parse(b));
  assert.deepEqual(data.map((d) => d['@type']), ['SoftwareApplication', 'FAQPage']);
  assert.equal(data[1].mainEntity.length, await page.locator('.faq details').count());
  assert.equal(data[1].mainEntity.length, 7);

  const hrefs = await page.locator('a[href]').evaluateAll((links) => [...new Set(links.map((a) => a.href))]);
  assert.ok(hrefs.length >= 6);
  for (const href of hrefs) {
    assert.ok(href.startsWith(base), `nur interne Links erwartet: ${href}`);
    const res = await page.request.get(href);
    assert.equal(res.status(), 200, href);
  }
  for (const id of ['features', 'calc', 'pricing', 'faq']) assert.equal(await page.locator(`#${id}`).count(), 1, id);
  await done();
});

test('Startseite → App: der Hauptknopf öffnet die App', async () => {
  const { page, done } = await open('/');
  await page.locator('.hero .btn-primary').click();
  await page.waitForSelector('html[data-ready="true"]');
  assert.match(page.url(), /\/app\/$/);
  assert.equal(await page.locator('html').getAttribute('lang'), 'de');
  await page.locator('#brand-link').click();
  await page.waitForSelector('.hero');
  await done();
});

test('englische Startseite: Sprache, Preise in Dollar, App startet auf Englisch', async () => {
  const { page, done } = await open('/en/');
  assert.equal(await page.locator('html').getAttribute('lang'), 'en');
  assert.equal(norm(await page.locator('h1').innerText()), 'Laser cutting quotes: from DXF to quote in 30 seconds.');
  assert.ok((await page.title()).length <= 60);
  assert.match(norm(await page.locator('.plan.is-pro .price').innerText()), /^\$45 per month$/);
  await page.locator('.site-nav a', { hasText: 'Deutsch' }).click();
  await page.waitForFunction(() => document.documentElement.lang === 'de');
  assert.match(norm(await page.locator('.plan.is-pro .price').innerText()), /^39 € pro Monat$/);
  await page.locator('.site-nav a', { hasText: 'English' }).click();
  await page.waitForFunction(() => document.documentElement.lang === 'en');
  await page.locator('.hero .btn-primary').click();
  await page.waitForSelector('html[data-ready="true"]');
  assert.equal(await page.locator('html').getAttribute('lang'), 'en', 'deutscher Browser, aber englische Startseite → englische App');
  assert.equal(norm(await page.locator('#btn-sample').innerText()), 'Load sample parts');
  await done();
});

test('Rechtstexte: Vorlagen laden fehlerfrei und sind als Vorlage gekennzeichnet', async () => {
  for (const path of ['/impressum.html', '/datenschutz.html']) {
    const { page, done } = await open(path);
    assert.match(norm(await page.locator('.template-banner').innerText()), /^VORLAGE/);
    assert.ok(await page.locator('.placeholder').count() >= 4);
    assert.equal(await page.locator('meta[name="robots"]').getAttribute('content'), 'noindex');
    await done();
  }
});

test('Startseiten ohne horizontales Scrollen auf Smartphone-Breite', async () => {
  for (const path of ['/', '/en/', '/impressum.html', '/datenschutz.html']) {
    const { page, done } = await open(path, { viewport: { width: 360, height: 780 } });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert.ok(overflow <= 0, `${path}: horizontaler Überlauf ${overflow}px`);
    await done();
  }
});

test('Barrierefreiheit (axe-core, WCAG 2.1 A/AA): keine Verstöße auf allen Seiten, hell und dunkel', { skip: axePath ? false : 'axe-core nicht installiert' }, async () => {
  const scan = async (page, label) => {
    await page.addScriptTag({ path: axePath });
    const result = await page.evaluate(() => window.axe.run(document, { runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice'] }));
    const found = result.violations.map((v) => `${label} · ${v.id} (${v.impact}): ${v.nodes.slice(0, 3).map((n) => n.target.join(' ')).join(' | ')}`);
    assert.deepEqual(found, [], 'axe-Verstöße');
  };
  for (const colorScheme of ['light', 'dark']) {
    // axe muss per Skript-Tag eingefügt werden → CSP für diesen Test umgehen
    for (const path of ['/', '/en/', '/impressum.html', '/datenschutz.html']) {
      const { page, context } = await open(path, { colorScheme, bypassCSP: true });
      await page.locator('.faq details').first().evaluate((d) => { d.open = true; }).catch(() => {});
      await scan(page, `${path} ${colorScheme}`);
      await context.close();
    }
    const { page, context } = await open('/app/', { colorScheme, bypassCSP: true });
    await page.waitForSelector('html[data-ready="true"]');
    await scan(page, `App leer ${colorScheme}`);
    await page.click('#btn-sample');
    await page.waitForSelector('.part-item >> nth=1');
    await page.locator('.part-select').nth(1).click();
    await page.locator('#layers li', { hasText: 'HILFSLINIE' }).locator('input').check();
    await page.evaluate(() => { document.querySelector('#toast').textContent = ''; });
    await scan(page, `App mit Teilen ${colorScheme}`);
    await page.click('#btn-settings');
    await scan(page, `Einstellungen Firma ${colorScheme}`);
    await page.locator('#dlg-settings summary', { hasText: 'Kalkulation' }).click();
    await scan(page, `Einstellungen Kalkulation ${colorScheme}`);
    await page.locator('#dlg-settings summary', { hasText: 'Materialien' }).click();
    await page.locator('details.mat summary').first().click();
    await scan(page, `Einstellungen Materialien ${colorScheme}`);
    await page.locator('#dlg-settings summary', { hasText: 'Sicherung' }).click();
    await scan(page, `Einstellungen Sicherung ${colorScheme}`);
    await page.locator('#dlg-settings button[value="close"]').click();
    await page.click('#btn-license');
    await page.fill('#license-key', 'falsch');
    await page.click('#btn-activate');
    await page.waitForFunction(() => document.querySelector('#license-error').textContent !== '');
    await scan(page, `Lizenzdialog ${colorScheme}`);
    await context.close();
  }
});
