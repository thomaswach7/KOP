// Einzeldatei-Fassung der App: eine HTML-Datei, die ohne Webserver per Doppelklick läuft.
// Der Build braucht esbuild (npm install). Fehlt es, werden diese Tests übersprungen.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { CONFIG } from '../src/config.js';

let esbuildMissing = false;
try { await import('esbuild'); } catch { esbuildMissing = true; }
const skip = esbuildMissing ? 'esbuild fehlt – zuerst "npm install" ausführen' : false;

const OUT = fileURLToPath(new URL('../standalone/kerfquote.html', import.meta.url));
const sha256 = (text) => createHash('sha256').update(text, 'utf8').digest('base64');
const only = (html, re, what) => {
  const all = [...html.matchAll(re)];
  assert.equal(all.length, 1, `genau ein ${what}`);
  return all[0][1];
};
const build = async (options) => (await import('../tools/build-standalone.mjs')).buildStandalone(options);

test('Einzeldatei: verweist auf keine andere Datei', { skip }, async () => {
  const html = await build();
  assert.match(html, /^<!doctype html>/i);
  const refs = [...html.matchAll(/\s(?:src|href)="([^"]*)"/g)].map((m) => m[1]);
  assert.ok(refs.length > 0);
  for (const ref of refs) assert.match(ref, /^(#|data:)/, `Verweis ${ref.slice(0, 60)}`);
  assert.doesNotMatch(html, /rel="stylesheet"/);
  assert.doesNotMatch(html, /type="module"/);
  assert.doesNotMatch(html, /import\.meta/);
  assert.doesNotMatch(html, /\bfetch\(/, 'kein Netzwerkzugriff im Code');
});

test('Einzeldatei: Richtlinie erlaubt genau den eingebetteten Stil und das eingebettete Skript', { skip }, async () => {
  const html = await build();
  const csp = only(html, /<meta http-equiv="Content-Security-Policy" content="([^"]*)">/g, 'CSP-Eintrag');
  const style = only(html, /<style>([\s\S]*?)<\/style>/g, 'Stilblock');
  const script = only(html, /<script>([\s\S]*?)<\/script>/g, 'Skriptblock');
  assert.ok(style.length > 5000 && script.length > 20000);
  const rules = Object.fromEntries(csp.split(';').map((r) => r.trim().split(/\s+/)).map(([name, ...v]) => [name, v.join(' ')]));
  assert.equal(rules['default-src'], "'none'");
  assert.equal(rules['style-src'], `'sha256-${sha256(style)}'`);
  assert.equal(rules['script-src'], `'sha256-${sha256(script)}'`);
  assert.equal(rules['img-src'], 'data: blob:');
  assert.equal(rules['base-uri'], "'none'");
  // Das Skript steht am Ende des Dokuments: Die Seite ist aufgebaut, bevor es läuft.
  assert.ok(html.indexOf('<script>') > html.indexOf('id="print-root"'));
});

test('Einzeldatei: Beispielteile sind eingebettet', { skip }, async () => {
  const html = await build();
  for (const name of CONFIG.samples) assert.ok(html.includes(`"${name}"`), name);
  assert.match(html, /LWPOLYLINE/);
});

test('Einzeldatei: Fassung ohne eigene Richtlinie für eingebettete Ansichten', { skip }, async () => {
  const [withCsp, without] = await Promise.all([build(), build({ csp: false })]);
  assert.doesNotMatch(without, /Content-Security-Policy/);
  assert.equal(without, withCsp.replace(/\s*<meta http-equiv="Content-Security-Policy"[^>]*>/, ''));
});

test('Einzeldatei: der Build ist wiederholbar und die abgelegte Datei ist aktuell', { skip }, async () => {
  const [a, b] = await Promise.all([build(), build()]);
  assert.equal(a, b);
  assert.ok(existsSync(OUT), 'standalone/kerfquote.html fehlt – "npm run build:standalone" ausführen');
  const stored = readFileSync(OUT, 'utf8').replace(/\r\n/g, '\n');
  assert.equal(stored === a, true, 'standalone/kerfquote.html ist veraltet – "npm run build:standalone" ausführen');
});
