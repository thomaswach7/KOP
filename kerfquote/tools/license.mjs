#!/usr/bin/env node
// Lizenzwerkzeug für den Anbieter (läuft nur lokal, nie im Browser):
//
//   node tools/license.mjs keygen                       Schlüsselpaar erzeugen (einmalig!)
//   node tools/license.mjs issue --name "Firma GmbH"    Lizenz für 12 Monate ausstellen
//                               [--months 12] [--id K-0001]
//   node tools/license.mjs verify <Lizenzschlüssel>     Lizenz prüfen
//
// Der private Schlüssel darf NIE ins Repository oder auf die Website: Wer ihn hat, kann beliebig
// viele Lizenzen ausstellen. Er liegt deshalb außerhalb des Website-Ordners unter
//   ~/.kerfquote/license-private-key.json
// (anderer Ort: Umgebungsvariable KERFQUOTE_PRIVATE_KEY). Sicher aufbewahren, Backup anlegen!

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { bytesToBase64Url, verifyLicense, LICENSE_PREFIX } from '../src/license.js';

const ALGORITHM = { name: 'ECDSA', namedCurve: 'P-256' };
/** Ablageort des privaten Schlüssels – bewusst nicht im Website-Ordner, damit er nie mit hochgeladen wird. */
export function privateKeyPath(env = process.env) {
  return env.KERFQUOTE_PRIVATE_KEY || join(homedir(), '.kerfquote', 'license-private-key.json');
}

const PRIVATE_KEY_FILE = privateKeyPath();
const PUBLIC_KEY_FILE = fileURLToPath(new URL('../src/license-public-key.js', import.meta.url));

export async function generateKeyPair() {
  const pair = await crypto.subtle.generateKey(ALGORITHM, true, ['sign', 'verify']);
  const privateJwk = await crypto.subtle.exportKey('jwk', pair.privateKey);
  const { kty, crv, x, y } = await crypto.subtle.exportKey('jwk', pair.publicKey);
  return { privateJwk, publicJwk: { kty, crv, x, y } };
}

/** @param {{name: string, plan: 'pro', exp: string, id?: string}} payload exp als JJJJ-MM-TT */
export async function issueLicense(payload, privateJwk) {
  const key = await crypto.subtle.importKey('jwk', privateJwk, ALGORITHM, false, ['sign']);
  const body = `${LICENSE_PREFIX}.${bytesToBase64Url(new TextEncoder().encode(JSON.stringify(payload)))}`;
  const sig = await crypto.subtle.sign({ name: 'ECDSA', hash: 'SHA-256' }, key, new TextEncoder().encode(body));
  return `${body}.${bytesToBase64Url(new Uint8Array(sig))}`;
}

export function publicKeyModule(publicJwk) {
  return `// Öffentlicher Schlüssel zur Lizenzprüfung. Wird von "node tools/license.mjs keygen" erzeugt.
// Dieser Schlüssel ist nicht geheim. null = noch kein Schlüsselpaar erzeugt (Pro nicht aktivierbar).
export const LICENSE_PUBLIC_KEY = ${publicJwk ? JSON.stringify(publicJwk, null, 2) : 'null'};
`;
}

function arg(args, name, fallback) {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && i + 1 < args.length ? args[i + 1] : fallback;
}

function addMonths(date, months) {
  const d = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + months, date.getUTCDate()));
  return d.toISOString().slice(0, 10);
}

async function main(args) {
  const [command] = args;
  if (command === 'keygen') {
    if (existsSync(PRIVATE_KEY_FILE) && !args.includes('--force')) {
      console.error('Es gibt bereits einen privaten Schlüssel. Ein neues Schlüsselpaar macht ALLE bisher\n'
        + 'verkauften Lizenzen ungültig. Nur mit --force überschreiben.');
      return 1;
    }
    const { privateJwk, publicJwk } = await generateKeyPair();
    mkdirSync(dirname(PRIVATE_KEY_FILE), { recursive: true, mode: 0o700 });
    writeFileSync(PRIVATE_KEY_FILE, `${JSON.stringify(privateJwk, null, 2)}\n`, { mode: 0o600 });
    writeFileSync(PUBLIC_KEY_FILE, publicKeyModule(publicJwk));
    console.log(`Privater Schlüssel:     ${PRIVATE_KEY_FILE}  (geheim halten, Backup anlegen!)`);
    console.log(`Öffentlicher Schlüssel: ${PUBLIC_KEY_FILE}  (committen und veröffentlichen)`);
    return 0;
  }
  if (command === 'issue') {
    const name = arg(args, 'name');
    const months = Number(arg(args, 'months', '12'));
    if (!name || !Number.isInteger(months) || months < 1 || months > 120) {
      console.error('Aufruf: node tools/license.mjs issue --name "Firma GmbH" [--months 12] [--id K-0001]');
      return 1;
    }
    if (!existsSync(PRIVATE_KEY_FILE)) {
      console.error(`Kein privater Schlüssel unter ${PRIVATE_KEY_FILE} gefunden.\n`
        + 'Vorhandenen Schlüssel dorthin kopieren oder (nur vor dem ersten Verkauf) neu erzeugen: node tools/license.mjs keygen');
      return 1;
    }
    const privateJwk = JSON.parse(readFileSync(PRIVATE_KEY_FILE, 'utf8'));
    const now = new Date();
    const payload = {
      name, plan: 'pro', exp: addMonths(now, months), iat: now.toISOString().slice(0, 10),
      id: arg(args, 'id', `K-${now.getTime().toString(36).toUpperCase()}`),
    };
    console.error(`Lizenz für "${payload.name}", gültig bis ${payload.exp} (Nr. ${payload.id}):`);
    console.log(await issueLicense(payload, privateJwk));
    return 0;
  }
  if (command === 'verify') {
    const { LICENSE_PUBLIC_KEY } = await import(pathToFileURL(PUBLIC_KEY_FILE).href);
    const result = await verifyLicense(args[1], LICENSE_PUBLIC_KEY);
    console.log(JSON.stringify(result, null, 2));
    return result.valid ? 0 : 1;
  }
  console.error('Befehle: keygen | issue --name "Firma" [--months 12] [--id X] | verify <Schlüssel>');
  return 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exitCode = await main(process.argv.slice(2));
}
