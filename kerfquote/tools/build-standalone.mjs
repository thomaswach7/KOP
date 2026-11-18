#!/usr/bin/env node
// Baut die App als eine einzige HTML-Datei, die ohne Webserver per Doppelklick läuft:
//   node tools/build-standalone.mjs [--out Datei] [--no-csp]
// Stil, Skript, Symbol und Beispielteile werden eingebettet; die Datei lädt nichts nach.
// Braucht esbuild (Entwicklungsabhängigkeit, „npm install“). Die App selbst bleibt ohne Abhängigkeiten.
//
// --no-csp lässt die eigene Inhaltsrichtlinie weg. Nötig für eingebettete Ansichten, deren
// Gastgeber eigene Skripte in die Seite setzt und selbst eine Richtlinie vorgibt.

import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { CONFIG } from '../src/config.js';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const DEFAULT_OUT = resolve(ROOT, 'standalone/kerfquote.html');
const SAMPLES_MODULE = resolve(ROOT, 'src/ui/samples.js');

// Zeilenenden vereinheitlichen, damit der Build auf jedem System dieselbe Datei ergibt
const text = async (path) => (await readFile(resolve(ROOT, path), 'utf8')).replace(/\r\n/g, '\n');
const sha256 = (content) => createHash('sha256').update(content, 'utf8').digest('base64');

/** Ersetzt genau eine Fundstelle; alles andere ist ein Fehler im Build, kein stiller Ausfall. */
function replaceOnce(html, pattern, replacement, what) {
  const found = html.match(new RegExp(pattern.source, pattern.flags.includes('g') ? pattern.flags : `${pattern.flags}g`)) ?? [];
  if (found.length !== 1) throw new Error(`Einzeldatei-Build: ${what} ${found.length}-mal gefunden, erwartet genau einmal`);
  return html.replace(pattern, () => replacement);
}

/** Ersatz für src/ui/samples.js: die Beispielteile stehen als Text im Skript. */
async function embeddedSamplesModule() {
  const entries = [];
  for (const name of CONFIG.samples) entries.push([name, await text(`samples/${name}`)]);
  return `const SAMPLES = ${JSON.stringify(Object.fromEntries(entries))};
export async function loadSample(name) {
  if (!Object.hasOwn(SAMPLES, name)) throw new Error('Beispielteil fehlt: ' + name);
  return SAMPLES[name];
}
`;
}

async function bundleScript() {
  const { build } = await import('esbuild');
  const samples = await embeddedSamplesModule();
  const result = await build({
    entryPoints: [resolve(ROOT, 'src/ui/app.js')],
    bundle: true,
    format: 'iife',
    target: ['es2022'],
    minify: true,
    charset: 'utf8',
    legalComments: 'none',
    write: false,
    logLevel: 'silent',
    plugins: [{
      name: 'beispielteile-einbetten',
      setup(b) {
        b.onLoad({ filter: /[\\/]src[\\/]ui[\\/]samples\.js$/ }, (args) =>
          (resolve(args.path) === SAMPLES_MODULE ? { contents: samples, loader: 'js' } : undefined));
      },
    }],
  });
  if (result.warnings.length > 0) throw new Error(`Einzeldatei-Build: ${result.warnings.map((w) => w.text).join('; ')}`);
  const js = result.outputFiles[0].text.trim();
  // Diese Folgen würden das Skript im HTML vorzeitig beenden bzw. den Parser umschalten
  if (/<\/script|<!--/i.test(js)) throw new Error('Einzeldatei-Build: Skript enthält eine im HTML unzulässige Zeichenfolge');
  return js;
}

/**
 * @param {{ csp?: boolean }} [options] csp=false lässt die eigene Inhaltsrichtlinie weg
 * @returns {Promise<string>} vollständiges HTML-Dokument
 */
export async function buildStandalone({ csp = true } = {}) {
  const [shell, base, app, icon, js] = await Promise.all([
    text('app/index.html'), text('assets/base.css'), text('assets/app.css'),
    readFile(resolve(ROOT, 'assets/favicon.svg')), bundleScript(),
  ]);
  const css = `${base.trim()}\n${app.trim()}`;
  if (/<\/style|url\(/i.test(css)) throw new Error('Einzeldatei-Build: Stil enthält einen Dateiverweis oder ein schließendes style-Tag');

  const policy = `default-src 'none'; img-src data: blob:; style-src 'sha256-${sha256(css)}'; script-src 'sha256-${sha256(js)}'; base-uri 'none'`;
  let html = shell;
  html = replaceOnce(html, /[ \t]*<meta http-equiv="Content-Security-Policy"[^>]*>\n/,
    csp ? `  <meta http-equiv="Content-Security-Policy" content="${policy}">\n` : '', 'CSP-Eintrag');
  html = replaceOnce(html, /<link rel="icon" href="\.\.\/assets\/favicon\.svg" type="image\/svg\+xml">/,
    `<link rel="icon" href="data:image/svg+xml;base64,${icon.toString('base64')}" type="image/svg+xml">`, 'Symbol');
  html = replaceOnce(html, /[ \t]*<link rel="stylesheet" href="\.\.\/assets\/base\.css">\n/, '', 'Grundstil');
  html = replaceOnce(html, /<link rel="stylesheet" href="\.\.\/assets\/app\.css">/, `<style>${css}</style>`, 'App-Stil');
  html = replaceOnce(html, /[ \t]*<script type="module" src="\.\.\/src\/ui\/app\.js"><\/script>\n/, '', 'Modul-Skript');
  // Ohne Startseite führt das Logo an den Seitenanfang statt in den übergeordneten Ordner
  html = replaceOnce(html, /<a class="brand" href="\.\.\/" id="brand-link">/, '<a class="brand" href="#" id="brand-link">', 'Logo-Link');
  // Das Skript steht am Ende: Ein eingebettetes Skript läuft sofort, die Seite muss dann schon aufgebaut sein
  html = replaceOnce(html, /<\/body>/, `<script>${js}</script>\n</body>`, 'Dokumentende');

  const refs = [...html.matchAll(/\s(?:src|href)="([^"]*)"/g)].map((m) => m[1]).filter((ref) => !/^(#|data:)/.test(ref));
  if (refs.length > 0) throw new Error(`Einzeldatei-Build: verbleibende Dateiverweise: ${refs.join(', ')}`);
  return html;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === resolve(process.argv[1])) {
  const args = process.argv.slice(2);
  const outIndex = args.indexOf('--out');
  const out = outIndex >= 0 && args[outIndex + 1] ? resolve(args[outIndex + 1]) : DEFAULT_OUT;
  try {
    const html = await buildStandalone({ csp: !args.includes('--no-csp') });
    await mkdir(dirname(out), { recursive: true });
    await writeFile(out, html);
    console.log(`Einzeldatei geschrieben: ${out} (${Math.round(Buffer.byteLength(html) / 1024)} kB)`);
  } catch (error) {
    console.error(error.code === 'ERR_MODULE_NOT_FOUND' ? 'esbuild fehlt – zuerst "npm install" ausführen.' : error.message);
    process.exitCode = 1;
  }
}
