// Lizenzprüfung ohne Server: Ein Lizenzschlüssel ist ein signiertes Datenpaket
//   KQ1.<Daten als Base64URL-JSON>.<ECDSA-P256-Signatur als Base64URL>
// Die App kennt nur den öffentlichen Schlüssel und kann damit prüfen, aber keine Schlüssel
// erzeugen. Hinweis: Eine reine Browser-Prüfung hält ehrliche Kunden ehrlich; wer den
// Quelltext verändert, kann sie umgehen. Für B2B-Software ist das üblich und ausreichend.

export const LICENSE_PREFIX = 'KQ1';
/** Grenzen der kostenlosen Version */
export const FREE_LIMITS = { maxParts: 2 };

const ALGORITHM = { name: 'ECDSA', namedCurve: 'P-256' };
const SIGNING = { name: 'ECDSA', hash: 'SHA-256' };
const B64URL = /^[A-Za-z0-9_-]+$/;

export function bytesToBase64Url(bytes) {
  let bin = '';
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export function base64UrlToBytes(text) {
  const b64 = text.replace(/-/g, '+').replace(/_/g, '/');
  const bin = atob(b64 + '='.repeat((4 - (b64.length % 4)) % 4));
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

/**
 * @param {unknown} token eingefügter Lizenzschlüssel
 * @param {JsonWebKey|null} publicJwk öffentlicher Schlüssel des Anbieters
 * @param {Date} [now]
 * @returns {Promise<{valid: boolean, reason?: 'format'|'signature'|'expired'|'unconfigured', payload?: object}>}
 */
export async function verifyLicense(token, publicJwk, now = new Date()) {
  if (typeof token !== 'string') return { valid: false, reason: 'format' };
  const parts = token.replace(/\s+/g, '').split('.');
  if (parts.length !== 3 || parts[0] !== LICENSE_PREFIX || !B64URL.test(parts[1]) || !B64URL.test(parts[2])) {
    return { valid: false, reason: 'format' };
  }
  if (!publicJwk) return { valid: false, reason: 'unconfigured' };

  let ok = false;
  try {
    const key = await crypto.subtle.importKey('jwk', publicJwk, ALGORITHM, false, ['verify']);
    const signed = new TextEncoder().encode(`${parts[0]}.${parts[1]}`);
    ok = await crypto.subtle.verify(SIGNING, key, base64UrlToBytes(parts[2]), signed);
  } catch {
    ok = false;
  }
  if (!ok) return { valid: false, reason: 'signature' };

  let payload;
  try {
    payload = JSON.parse(new TextDecoder().decode(base64UrlToBytes(parts[1])));
  } catch {
    return { valid: false, reason: 'format' };
  }
  const expires = typeof payload?.exp === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(payload.exp)
    ? Date.parse(`${payload.exp}T23:59:59.999Z`) : NaN;
  if (payload?.plan !== 'pro' || Number.isNaN(expires)) return { valid: false, reason: 'format' };
  if (now.getTime() > expires) return { valid: false, reason: 'expired', payload };
  return { valid: true, payload };
}
