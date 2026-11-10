#!/usr/bin/env node
// Kleiner statischer Webserver für die lokale Entwicklung:  node tools/serve.mjs [Port]
// (Die App nutzt ES-Module und lässt sich deshalb nicht per Doppelklick als file:// öffnen.)

import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { extname, join, normalize, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('..', import.meta.url));
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.svg': 'image/svg+xml', '.json': 'application/json; charset=utf-8',
  '.dxf': 'application/dxf', '.txt': 'text/plain; charset=utf-8', '.xml': 'application/xml; charset=utf-8',
  '.png': 'image/png', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json',
};

export function createStaticServer(root = ROOT) {
  return createServer(async (req, res) => {
    try {
      const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
      // Versteckte Dateien (.git, .env …) und Schlüsseldateien werden grundsätzlich nicht ausgeliefert
      if (pathname.split('/').some((part) => part.startsWith('.')) || /private-key/i.test(pathname)) {
        res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }).end('Nicht gefunden');
        return;
      }
      let file = normalize(join(root, pathname));
      if (file !== root.replace(/[\\/]$/, '') && !file.startsWith(root.endsWith(sep) ? root : root + sep)) {
        res.writeHead(403).end('Forbidden');
        return;
      }
      if ((await stat(file)).isDirectory()) {
        if (!pathname.endsWith('/')) {
          res.writeHead(301, { Location: `${pathname}/` }).end();
          return;
        }
        file = join(file, 'index.html');
      }
      const data = await readFile(file);
      res.writeHead(200, { 'Content-Type': TYPES[extname(file).toLowerCase()] ?? 'application/octet-stream', 'Cache-Control': 'no-store' });
      res.end(data);
    } catch {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }).end('Nicht gefunden');
    }
  });
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const port = Number(process.argv[2]) || 8080;
  createStaticServer().listen(port, () => console.log(`KerfQuote läuft auf http://localhost:${port}/  (App: /app/)`));
}
