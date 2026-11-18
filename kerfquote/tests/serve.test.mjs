import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, mkdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createStaticServer } from '../tools/serve.mjs';

let server;
let base;
let root;

before(async () => {
  root = mkdtempSync(join(tmpdir(), 'kerfquote-serve-'));
  mkdirSync(join(root, 'app'));
  mkdirSync(join(root, '.git'));
  writeFileSync(join(root, 'index.html'), '<!doctype html><title>start</title>');
  writeFileSync(join(root, 'app', 'index.html'), '<!doctype html><title>app</title>');
  writeFileSync(join(root, 'license-private-key.json'), '{"d":"geheim"}');
  writeFileSync(join(root, '.env'), 'GEHEIM=1');
  writeFileSync(join(root, '.git', 'config'), '[core]');
  server = createStaticServer(root);
  await new Promise((resolve) => server.listen(0, resolve));
  base = `http://localhost:${server.address().port}`;
});

after(() => {
  server.close();
  rmSync(root, { recursive: true, force: true });
});

const status = async (path) => (await fetch(base + path, { redirect: 'manual' })).status;

test('liefert Startseite und Unterverzeichnisse aus', async () => {
  const res = await fetch(`${base}/`);
  assert.equal(res.status, 200);
  assert.match(res.headers.get('content-type'), /^text\/html/);
  assert.equal(await status('/app/'), 200);
  assert.equal(await status('/app'), 301);
  assert.equal(await status('/gibtsnicht.html'), 404);
});

test('private Schlüssel und versteckte Dateien werden nie ausgeliefert', async () => {
  assert.equal(await status('/license-private-key.json'), 404);
  assert.equal(await status('/LICENSE-PRIVATE-KEY.json'), 404);
  assert.equal(await status('/.env'), 404);
  assert.equal(await status('/.git/config'), 404);
});

test('kein Zugriff außerhalb des Website-Ordners', async () => {
  assert.notEqual(await status('/..%2f..%2fetc%2fpasswd'), 200);
  assert.notEqual(await status('/%2e%2e/%2e%2e/etc/passwd'), 200);
});
