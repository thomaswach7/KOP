import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verifyLicense } from '../src/license.js';
import { generateKeyPair, issueLicense } from '../tools/license.mjs';

const keys = await generateKeyPair();
const NOW = new Date('2026-11-10T12:00:00Z');
const payload = { name: 'Blechbearbeitung Müller GmbH', plan: 'pro', exp: '2027-11-10', id: 'K-0001' };

test('gültiger Schlüssel wird akzeptiert und liefert die Lizenzdaten (inkl. Umlaute)', async () => {
  const token = await issueLicense(payload, keys.privateJwk);
  assert.match(token, /^KQ1\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/);
  const r = await verifyLicense(token, keys.publicJwk, NOW);
  assert.equal(r.valid, true);
  assert.equal(r.payload.name, 'Blechbearbeitung Müller GmbH');
  assert.equal(r.payload.exp, '2027-11-10');
});

test('Leerzeichen und Zeilenumbrüche im eingefügten Schlüssel stören nicht', async () => {
  const token = await issueLicense(payload, keys.privateJwk);
  const messy = `  ${token.slice(0, 20)}\n${token.slice(20, 60)} \r\n${token.slice(60)}  `;
  assert.equal((await verifyLicense(messy, keys.publicJwk, NOW)).valid, true);
});

test('manipulierte Lizenzdaten (anderes Ablaufdatum) scheitern an der Signatur', async () => {
  const token = await issueLicense(payload, keys.privateJwk);
  const [prefix, , sig] = token.split('.');
  const forged = Buffer.from(JSON.stringify({ ...payload, exp: '2099-01-01' })).toString('base64url');
  const r = await verifyLicense(`${prefix}.${forged}.${sig}`, keys.publicJwk, NOW);
  assert.deepEqual(r, { valid: false, reason: 'signature' });
});

test('Schlüssel eines fremden Schlüsselpaars wird abgelehnt', async () => {
  const other = await generateKeyPair();
  const token = await issueLicense(payload, other.privateJwk);
  assert.deepEqual(await verifyLicense(token, keys.publicJwk, NOW), { valid: false, reason: 'signature' });
});

test('abgelaufen: am Ablauftag noch gültig, am Folgetag nicht mehr', async () => {
  const token = await issueLicense({ ...payload, exp: '2026-11-10' }, keys.privateJwk);
  assert.equal((await verifyLicense(token, keys.publicJwk, new Date('2026-11-10T23:59:00Z'))).valid, true);
  const late = await verifyLicense(token, keys.publicJwk, new Date('2026-11-11T00:00:01Z'));
  assert.equal(late.valid, false);
  assert.equal(late.reason, 'expired');
  assert.equal(late.payload.name, payload.name);
});

test('Unsinn, leere Eingaben und falsches Präfix → Grund "format"', async () => {
  for (const bad of ['', '   ', 'hallo', 'KQ1.abc', 'KQ2.abc.def', 'KQ1..', 'KQ1.!!!.???', null, undefined, 42]) {
    assert.deepEqual(await verifyLicense(bad, keys.publicJwk, NOW), { valid: false, reason: 'format' }, String(bad));
  }
});

test('gültig signiert, aber ohne Plan "pro" oder mit kaputtem Datum → ungültig', async () => {
  const noPlan = await issueLicense({ ...payload, plan: 'free' }, keys.privateJwk);
  assert.deepEqual(await verifyLicense(noPlan, keys.publicJwk, NOW), { valid: false, reason: 'format' });
  const badDate = await issueLicense({ ...payload, exp: 'irgendwann' }, keys.privateJwk);
  assert.deepEqual(await verifyLicense(badDate, keys.publicJwk, NOW), { valid: false, reason: 'format' });
});

test('ohne hinterlegten öffentlichen Schlüssel → Grund "unconfigured"', async () => {
  const token = await issueLicense(payload, keys.privateJwk);
  assert.deepEqual(await verifyLicense(token, null, NOW), { valid: false, reason: 'unconfigured' });
});

test('der private Schlüssel steckt nicht im öffentlichen Schlüssel', () => {
  assert.equal('d' in keys.publicJwk, false);
  assert.equal(typeof keys.privateJwk.d, 'string');
});
