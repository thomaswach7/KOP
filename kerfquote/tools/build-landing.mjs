#!/usr/bin/env node
// Erzeugt die Startseiten index.html (Deutsch) und en/index.html (Englisch) sowie robots.txt
// und – sobald SITE_URL gesetzt ist – sitemap.xml.    Aufruf:  node tools/build-landing.mjs
//
// Texte und Preise stehen hier an EINER Stelle. Nach jeder Änderung neu erzeugen.

import { writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { CONFIG } from '../src/config.js';

/**
 * Öffentliche Adresse der Website ohne Schrägstrich am Ende, z. B. 'https://www.kerfquote.de'.
 * Leer lassen, solange es keine Domain gibt: dann entfallen canonical-/hreflang-Angaben und die Sitemap.
 */
const SITE_URL = '';

const PRICING = {
  de: { free: '0 €', pro: '39 €', proYear: 468, currency: 'EUR' },
  en: { free: '$0', pro: '$45', proYear: 540, currency: 'USD' },
};

const TEXT = {
  de: {
    title: 'Laserschneiden kalkulieren aus der DXF-Datei – KerfQuote',
    description: 'Laser-, Plasma- und Wasserstrahlzuschnitte direkt aus der DXF kalkulieren: Schnittlänge, Einstiche, Gewicht und Preis – im Browser, ohne Upload. Kostenlos testen.',
    nav: { features: 'Funktionen', calc: 'Rechenweg', pricing: 'Preise', faq: 'Fragen', app: 'App öffnen', other: 'English' },
    hero: {
      h1: ['Laserzuschnitte kalkulieren: vom DXF zum Angebot in ', '30 Sekunden', '.'],
      lead: 'KerfQuote kalkuliert Laser-, Plasma- und Wasserstrahlzuschnitte direkt aus der Zeichnung: Schnittlänge, Einstiche, Gewicht und Preis – mit Ihren eigenen Maschinensätzen.',
      cta: 'Kostenlos ausprobieren',
      cta2: 'So wird gerechnet',
      trust: 'Ohne Anmeldung, ohne Installation. Ihre Zeichnungen verlassen Ihren Rechner nicht.',
      mockLabel: 'Beispiel: Flansch mit sieben Innenkonturen, 672 mm Schnittlänge, 8 Einstiche',
      stats: [['Schnittlänge', '672,3 mm'], ['Einstiche', '8'], ['Stückpreis ab 100', '1,48 €']],
    },
    why: {
      eyebrow: 'Warum KerfQuote',
      h2: 'Wer zuerst anbietet, bekommt den Auftrag.',
      lead: 'Viele Anfragen bleiben liegen, weil das Kalkulieren von Hand zu lange dauert. KerfQuote nimmt Ihnen das Ausmessen ab.',
      cards: [
        ['Minuten statt Stunden', 'DXF hineinziehen, Material und Menge wählen, fertig. Schnittlänge und Einstiche werden exakt aus der Geometrie ermittelt.'],
        ['Nachvollziehbar statt Bauchgefühl', 'Jeder Preis ist aufgeschlüsselt: Material, Schneidzeit, Rüsten, Zuschlag. Sie sehen sofort, wo die Kosten entstehen.'],
        ['Vertraulich aus Prinzip', 'Die Zeichnung wird in Ihrem Browser ausgewertet und nicht hochgeladen. Das passt auch zu Geheimhaltungsvereinbarungen Ihrer Kunden.'],
      ],
    },
    how: {
      eyebrow: 'So funktioniert es',
      h2: 'Drei Schritte zum Angebot',
      steps: [
        ['DXF laden', 'Eine oder mehrere Dateien hineinziehen. KerfQuote erkennt die Einheit, löst Blöcke auf und blendet Bemaßungs- und Hilfslayer aus.'],
        ['Prüfen und einstellen', 'Offene Konturen und doppelte Linien werden markiert. Dann Material, Dicke, Menge und Biegungen wählen.'],
        ['Angebot ausgeben', 'Staffelpreise ansehen, Kundendaten ergänzen und das Angebot drucken oder als PDF speichern.'],
      ],
    },
    features: {
      eyebrow: 'Funktionen',
      h2: 'Alles, was die Zuschnittkalkulation braucht',
      cards: [
        ['Schnittlänge aus der DXF berechnen', 'Exakt aus Linien, Bögen, Kreisen, Polylinien, Ellipsen, Splines und Blöcken – in Millimetern oder Zoll.'],
        ['Fehler in der Zeichnung finden', 'Offene Konturen, doppelte Elemente und zu kleine Bohrungen fallen auf, bevor sie Geld kosten.'],
        ['Staffelpreise auf einen Blick', 'Die Rüstkosten verteilen sich automatisch auf die Stückzahl.'],
        ['Eigene Materialtabellen', 'Vorschub, Einstechzeit, Dichte und Preis je Material und Dicke – abgestimmt auf Ihre Maschine.'],
        ['Angebot als PDF', 'Mit Vorschaubild je Position, Mindestauftragswert und Mehrwertsteuer.'],
        ['Deutsch und Englisch', 'Oberfläche und Angebot in beiden Sprachen, Währung frei wählbar.'],
      ],
    },
    calc: {
      eyebrow: 'Transparenz',
      h2: 'Laserschneiden: So werden die Kosten berechnet',
      lead: 'Kein Preis aus der Blackbox: Das Modell ist bewusst einfach und entspricht der üblichen Kalkulation im Lohnzuschnitt.',
      rows: [
        ['Material', '(umschließendes Rechteck + Stegzugabe) × Dicke × Dichte × Preis je kg'],
        ['Schneiden', '(Schnittlänge ÷ Vorschub + Einstiche × Einstechzeit) × Maschinenstundensatz'],
        ['Rüsten', 'Rüstkosten je Position ÷ Menge'],
        ['Stückpreis', '(Material + Schneiden + Rüsten + Biegen + Zusatz) × (1 + Zuschlag)'],
      ],
      note: 'Die mitgelieferten Vorschübe und Materialpreise sind Startwerte für einen 4-kW-Faserlaser. Hinterlegen Sie Ihre eigenen Werte, dann stimmen auch die Preise. Eine Schachtelung mehrerer Teile auf einer Tafel (Nesting) wird nicht berechnet.',
    },
    pricing: {
      eyebrow: 'Preise',
      h2: 'Kostenlos starten, bei Bedarf erweitern',
      lead: 'Die Analyse Ihrer DXF-Dateien ist dauerhaft kostenlos. Pro lohnt sich, sobald Sie regelmäßig Angebote mit mehreren Positionen schreiben.',
      perMonth: 'pro Monat',
      free: ['Free', ['DXF-Analyse ohne Begrenzung', 'Kalkulation mit eigenen Sätzen', 'Bis zu 2 Positionen je Angebot', 'Angebot mit KerfQuote-Hinweis'], 'Jetzt starten'],
      pro: ['Pro', ['Unbegrenzt viele Positionen', 'Eigenes Logo im Angebot', 'Angebot ohne KerfQuote-Hinweis', 'CSV-Export für Excel und ERP'], 'Pro kaufen', 'In der App freischalten'],
      proNote: (year) => `jährlich abgerechnet, ${year} € pro Jahr`,
      vat: 'Alle Preise zuzüglich Mehrwertsteuer.',
    },
    faq: {
      eyebrow: 'Fragen und Antworten',
      h2: 'Häufige Fragen',
      items: [
        ['Welche DXF-Dateien werden unterstützt?', 'ASCII-DXF ab Version R12 mit Linien, Bögen, Kreisen, Polylinien, Ellipsen, Splines und Blockreferenzen. Binäres DXF und DWG werden nicht gelesen – speichern Sie die Zeichnung im CAD als ASCII-DXF.'],
        ['Werden meine Zeichnungen hochgeladen?', 'Nein. Die Datei wird ausschließlich in Ihrem Browser ausgewertet. Ihre Einstellungen bleiben ebenfalls lokal auf Ihrem Rechner gespeichert.'],
        ['Wie genau ist die Kalkulation?', 'Schnittlänge, Einstiche und Fläche werden exakt aus der Geometrie berechnet. Der Preis ist so genau wie die hinterlegten Werte: Vorschübe, Stundensatz und Materialpreise sollten Sie einmal auf Ihren Betrieb abstimmen.'],
        ['Funktioniert das auch für Plasma, Wasserstrahl oder Autogen?', 'Ja. Das Modell ist verfahrensunabhängig: Sie hinterlegen je Material und Dicke Vorschub und Einstechzeit Ihrer Maschine.'],
        ['Wird die Schachtelung (Nesting) berücksichtigt?', 'Nein. Der Materialbedarf wird über das kleinste umschließende Rechteck des Teils plus Stegzugabe angesetzt. Das ist für Angebote üblich und liegt auf der sicheren Seite.'],
        ['Wie erhalte ich die Pro-Version?', 'Nach dem Kauf bekommen Sie einen Lizenzschlüssel, den Sie in der App unter „Lizenz“ einfügen. Die Lizenz gilt für zwölf Monate.'],
        ['Brauche ich ein Benutzerkonto?', 'Nein. Sie öffnen die App und legen los.'],
      ],
    },
    final: { h2: 'Probieren Sie es mit Ihrer nächsten Anfrage aus.', lead: 'Die Beispielteile sind mit einem Klick geladen.', cta: 'App öffnen' },
    foot: { imprint: 'Impressum', privacy: 'Datenschutz', tagline: 'Zuschnitt-Kalkulation aus DXF' },
  },

  en: {
    title: 'Laser cutting quote calculator from DXF – KerfQuote',
    description: 'Quote laser, plasma and waterjet cut parts straight from the DXF: cut length, pierces, weight and price – in your browser, nothing uploaded. Try it free.',
    nav: { features: 'Features', calc: 'How it calculates', pricing: 'Pricing', faq: 'FAQ', app: 'Open app', other: 'Deutsch' },
    hero: {
      h1: ['Laser cutting quotes: from DXF to quote in ', '30 seconds', '.'],
      lead: 'KerfQuote prices laser, plasma and waterjet cut parts straight from the drawing: cut length, pierces, weight and price – using your own machine rates.',
      cta: 'Try it free',
      cta2: 'See how it calculates',
      trust: 'No sign-up, no installation. Your drawings never leave your computer.',
      mockLabel: 'Example: flange with seven inner contours, 672 mm cut length, 8 pierces',
      stats: [['Cut length', '672.3 mm'], ['Pierces', '8'], ['Unit price at 100', '€1.48']],
    },
    why: {
      eyebrow: 'Why KerfQuote',
      h2: 'The first quote in the inbox usually wins the job.',
      lead: 'Many requests go unanswered because quoting by hand takes too long. KerfQuote does the measuring for you.',
      cards: [
        ['Minutes instead of hours', 'Drop in the DXF, pick material and quantity, done. Cut length and pierces are measured exactly from the geometry.'],
        ['Traceable instead of gut feeling', 'Every price is broken down: material, cutting time, setup, markup. You see at once where the cost comes from.'],
        ['Confidential by design', 'The drawing is analysed in your browser and never uploaded. That also fits the NDAs you have with your customers.'],
      ],
    },
    how: {
      eyebrow: 'How it works',
      h2: 'Three steps to a quote',
      steps: [
        ['Add the DXF', 'Drop in one or more files. KerfQuote detects the units, resolves blocks and hides dimension and construction layers.'],
        ['Check and configure', 'Open contours and duplicate lines are flagged. Then choose material, thickness, quantity and bends.'],
        ['Send the quote', 'Review the quantity breaks, add the customer details and print the quote or save it as PDF.'],
      ],
    },
    features: {
      eyebrow: 'Features',
      h2: 'Everything cut-part quoting needs',
      cards: [
        ['Cut length straight from the DXF', 'Measured exactly from lines, arcs, circles, polylines, ellipses, splines and blocks – in millimetres or inches.'],
        ['Catch drawing errors', 'Open contours, duplicate entities and undersized holes show up before they cost money.'],
        ['Quantity breaks at a glance', 'Setup cost is spread across the quantity automatically.'],
        ['Your own material tables', 'Feed rate, pierce time, density and price per material and thickness – tuned to your machine.'],
        ['Quote as PDF', 'With a thumbnail per item, minimum order value and VAT.'],
        ['English and German', 'Interface and quote in both languages, currency of your choice.'],
      ],
    },
    calc: {
      eyebrow: 'Transparency',
      h2: 'How laser cutting cost is calculated',
      lead: 'No black-box pricing: the model is deliberately simple and follows the usual job-shop costing.',
      rows: [
        ['Material', '(bounding rectangle + allowance) × thickness × density × price per kg'],
        ['Cutting', '(cut length ÷ feed rate + pierces × pierce time) × machine hourly rate'],
        ['Setup', 'setup cost per item ÷ quantity'],
        ['Unit price', '(material + cutting + setup + bending + extras) × (1 + markup)'],
      ],
      note: 'The bundled feed rates and material prices are starting values for a 4 kW fiber laser. Enter your own figures and the prices will be right. Nesting several parts on one sheet is not calculated.',
    },
    pricing: {
      eyebrow: 'Pricing',
      h2: 'Start free, upgrade when you need it',
      lead: 'Analysing your DXF files is free for good. Pro pays off as soon as you regularly write quotes with several items.',
      perMonth: 'per month',
      free: ['Free', ['Unlimited DXF analysis', 'Costing with your own rates', 'Up to 2 items per quote', 'Quote carries a KerfQuote note'], 'Get started'],
      pro: ['Pro', ['Unlimited items per quote', 'Your own logo on quotes', 'Quotes without the KerfQuote note', 'CSV export for Excel and ERP'], 'Buy Pro', 'Unlock in the app'],
      proNote: (year) => `billed annually, $${year} per year`,
      vat: 'All prices exclude applicable taxes.',
    },
    faq: {
      eyebrow: 'Questions and answers',
      h2: 'Frequently asked questions',
      items: [
        ['Which DXF files are supported?', 'ASCII DXF from release R12 onwards with lines, arcs, circles, polylines, ellipses, splines and block references. Binary DXF and DWG are not read – save the drawing as ASCII DXF in your CAD system.'],
        ['Are my drawings uploaded?', 'No. The file is analysed entirely in your browser. Your settings are stored locally on your computer as well.'],
        ['How accurate is the calculation?', 'Cut length, pierces and area are computed exactly from the geometry. The price is as accurate as the figures behind it: tune feed rates, hourly rate and material prices to your shop once.'],
        ['Does it work for plasma, waterjet or oxy-fuel too?', 'Yes. The model is process-independent: you enter the feed rate and pierce time of your machine per material and thickness.'],
        ['Does it take nesting into account?', 'No. Material is charged by the smallest bounding rectangle of the part plus an allowance. That is common practice for quoting and errs on the safe side.'],
        ['How do I get the Pro version?', 'After purchase you receive a license key that you paste into the app under “License”. The license is valid for twelve months.'],
        ['Do I need an account?', 'No. Open the app and start.'],
      ],
    },
    final: { h2: 'Try it on your next request for quote.', lead: 'The sample parts load with one click.', cta: 'Open app' },
    foot: { imprint: 'Legal notice (German)', privacy: 'Privacy (German)', tagline: 'Cut-part quoting from DXF' },
  },
};

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const jsonLd = (data) => `<script type="application/ld+json">${JSON.stringify(data).replace(/<\//g, '<\\/')}</script>`;

const LOGO = '<svg viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="7" fill="#c2410c"/><path d="M8 23 L17 9" stroke="#fff" stroke-width="3" stroke-linecap="round"/><path d="M19.5 23 L24 16" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".55"/><circle cx="17" cy="9" r="2.6" fill="#ffd9c2"/></svg>';

function heroMock(t) {
  const holes = [0, 60, 120, 180, 240, 300].map((deg) => {
    const a = (deg * Math.PI) / 180;
    return `<circle class="m-inner" cx="${(200 + 67.5 * Math.cos(a)).toFixed(1)}" cy="${(130 - 67.5 * Math.sin(a)).toFixed(1)}" r="6.75"/>`;
  }).join('');
  return `<figure class="mock" role="img" aria-label="${esc(t.hero.mockLabel)}">
        <div class="mock-bar" aria-hidden="true"><i></i><i></i><i></i></div>
        <svg viewBox="0 0 400 260" aria-hidden="true">
          <circle class="m-fill" cx="200" cy="130" r="90"/>
          <circle class="m-outer" cx="200" cy="130" r="90"/>
          <circle class="m-inner" cx="200" cy="130" r="30"/>
          ${holes}
          <path class="m-kerf" d="M290 130 A90 90 0 0 0 200 40"/>
          <circle class="m-spark" cx="200" cy="40" r="5"/>
        </svg>
        <dl class="mock-stats" aria-hidden="true">
          ${t.hero.stats.map(([k, v], i) => `<div${i === 2 ? ' class="is-price"' : ''}><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('\n          ')}
        </dl>
      </figure>`;
}

function page(lang) {
  const t = TEXT[lang];
  const price = PRICING[lang];
  const root = lang === 'de' ? './' : '../';
  const app = `${root}app/${lang === 'en' ? '?lang=en' : ''}`;
  const other = lang === 'de' ? 'en/' : '../';
  const otherLang = lang === 'de' ? 'en' : 'de';
  const url = (l) => `${SITE_URL}/${l === 'de' ? '' : 'en/'}`;
  const hasCheckout = /^https:\/\//.test(CONFIG.checkoutUrl);
  const proHref = hasCheckout ? esc(CONFIG.checkoutUrl) : app;
  const proLabel = hasCheckout ? t.pricing.pro[2] : t.pricing.pro[3];

  const seo = SITE_URL ? `
  <link rel="canonical" href="${url(lang)}">
  <link rel="alternate" hreflang="de" href="${url('de')}">
  <link rel="alternate" hreflang="en" href="${url('en')}">
  <link rel="alternate" hreflang="x-default" href="${url('en')}">
  <meta property="og:url" content="${url(lang)}">
  <meta property="og:image" content="${SITE_URL}/assets/og.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">` : '';

  const software = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'KerfQuote',
    applicationCategory: 'BusinessApplication',
    operatingSystem: 'Web',
    inLanguage: ['de', 'en'],
    description: t.description,
    offers: [
      { '@type': 'Offer', name: 'Free', price: '0', priceCurrency: price.currency },
      { '@type': 'Offer', name: 'Pro', price: String(price.proYear), priceCurrency: price.currency },
    ],
  };
  const faq = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: t.faq.items.map(([q, a]) => ({ '@type': 'Question', name: q, acceptedAnswer: { '@type': 'Answer', text: a } })),
  };

  const cards = (list, numbered = false) => list.map(([title, text], i) => `<article class="card">
          ${numbered ? `<span class="num-badge" aria-hidden="true">${i + 1}</span>\n          ` : ''}<h3>${esc(title)}</h3>
          <p>${esc(text)}</p>
        </article>`).join('\n        ');
  const bullets = (list) => list.map((item) => `<li>${esc(item)}</li>`).join('\n            ');

  return `<!doctype html>
<html lang="${lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'">
  <title>${esc(t.title)}</title>
  <meta name="description" content="${esc(t.description)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="KerfQuote">
  <meta property="og:title" content="${esc(t.title)}">
  <meta property="og:description" content="${esc(t.description)}">
  <meta property="og:locale" content="${lang === 'de' ? 'de_DE' : 'en_US'}">${seo}
  <link rel="icon" href="${root}assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="${root}assets/base.css">
  <link rel="stylesheet" href="${root}assets/landing.css">
  ${jsonLd(software)}
  ${jsonLd(faq)}
</head>
<body>
  <header class="site-head">
    <div class="wrap">
      <a class="brand" href="${root}">${LOGO}<span>KerfQuote</span></a>
      <nav class="site-nav" aria-label="${lang === 'de' ? 'Hauptnavigation' : 'Main navigation'}">
        <a class="nav-link" href="#features">${esc(t.nav.features)}</a>
        <a class="nav-link" href="#calc">${esc(t.nav.calc)}</a>
        <a class="nav-link" href="#pricing">${esc(t.nav.pricing)}</a>
        <a class="nav-link" href="#faq">${esc(t.nav.faq)}</a>
        <a href="${other}" lang="${otherLang}" hreflang="${otherLang}">${esc(t.nav.other)}</a>
        <a class="btn btn-primary" href="${app}">${esc(t.nav.app)}</a>
      </nav>
    </div>
  </header>

  <main>
    <section class="hero">
      <div class="wrap">
        <div>
          <h1>${esc(t.hero.h1[0])}<em>${esc(t.hero.h1[1])}</em>${esc(t.hero.h1[2])}</h1>
          <p class="lead">${esc(t.hero.lead)}</p>
          <div class="cta-row">
            <a class="btn btn-primary btn-lg" href="${app}">${esc(t.hero.cta)}</a>
            <a class="btn btn-lg" href="#calc">${esc(t.hero.cta2)}</a>
          </div>
          <p class="trust">${esc(t.hero.trust)}</p>
        </div>
        ${heroMock(t)}
      </div>
    </section>

    <section class="band" aria-labelledby="why-h">
      <div class="wrap">
        <p class="eyebrow">${esc(t.why.eyebrow)}</p>
        <h2 id="why-h">${esc(t.why.h2)}</h2>
        <p class="lead">${esc(t.why.lead)}</p>
        <div class="cards">
        ${cards(t.why.cards)}
        </div>
      </div>
    </section>

    <section aria-labelledby="how-h">
      <div class="wrap">
        <p class="eyebrow">${esc(t.how.eyebrow)}</p>
        <h2 id="how-h">${esc(t.how.h2)}</h2>
        <div class="cards">
        ${cards(t.how.steps, true)}
        </div>
      </div>
    </section>

    <section class="band" id="features" aria-labelledby="features-h">
      <div class="wrap">
        <p class="eyebrow">${esc(t.features.eyebrow)}</p>
        <h2 id="features-h">${esc(t.features.h2)}</h2>
        <div class="cards">
        ${cards(t.features.cards)}
        </div>
      </div>
    </section>

    <section id="calc" aria-labelledby="calc-h">
      <div class="wrap">
        <p class="eyebrow">${esc(t.calc.eyebrow)}</p>
        <h2 id="calc-h">${esc(t.calc.h2)}</h2>
        <p class="lead">${esc(t.calc.lead)}</p>
        <div class="formula" tabindex="0" role="group" aria-labelledby="calc-h">
          ${t.calc.rows.map(([k, v]) => `<div><b>${esc(k)}</b> = ${esc(v)}</div>`).join('\n          ')}
        </div>
        <p class="note">${esc(t.calc.note)}</p>
      </div>
    </section>

    <section class="band" id="pricing" aria-labelledby="pricing-h">
      <div class="wrap">
        <p class="eyebrow">${esc(t.pricing.eyebrow)}</p>
        <h2 id="pricing-h">${esc(t.pricing.h2)}</h2>
        <p class="lead">${esc(t.pricing.lead)}</p>
        <div class="plans">
          <article class="plan">
            <h3>${esc(t.pricing.free[0])}</h3>
            <p class="price">${esc(price.free)}</p>
            <ul>
            ${bullets(t.pricing.free[1])}
            </ul>
            <a class="btn" href="${app}">${esc(t.pricing.free[2])}</a>
          </article>
          <article class="plan is-pro">
            <h3>${esc(t.pricing.pro[0])}</h3>
            <p class="price">${esc(price.pro)} <small>${esc(t.pricing.perMonth)}</small></p>
            <p class="muted">${esc(t.pricing.proNote(price.proYear))}</p>
            <ul>
            ${bullets(t.pricing.pro[1])}
            </ul>
            <a class="btn btn-primary" href="${proHref}">${esc(proLabel)}</a>
          </article>
        </div>
        <p class="note">${esc(t.pricing.vat)}</p>
      </div>
    </section>

    <section id="faq" aria-labelledby="faq-h">
      <div class="wrap">
        <p class="eyebrow">${esc(t.faq.eyebrow)}</p>
        <h2 id="faq-h">${esc(t.faq.h2)}</h2>
        <div class="faq">
          ${t.faq.items.map(([q, a]) => `<details>
            <summary>${esc(q)}</summary>
            <p>${esc(a)}</p>
          </details>`).join('\n          ')}
        </div>
      </div>
    </section>

    <section class="band final" aria-labelledby="final-h">
      <div class="wrap">
        <h2 id="final-h">${esc(t.final.h2)}</h2>
        <p class="lead">${esc(t.final.lead)}</p>
        <div class="cta-row">
          <a class="btn btn-primary btn-lg" href="${app}">${esc(t.final.cta)}</a>
        </div>
      </div>
    </section>
  </main>

  <footer class="site-foot">
    <div class="wrap">
      <span>KerfQuote · ${esc(t.foot.tagline)}</span>
      <nav aria-label="${lang === 'de' ? 'Rechtliches' : 'Legal'}">
        <a href="${root}impressum.html">${esc(t.foot.imprint)}</a>
        <a href="${root}datenschutz.html">${esc(t.foot.privacy)}</a>
        <a href="${other}" lang="${otherLang}" hreflang="${otherLang}">${esc(t.nav.other)}</a>
      </nav>
    </div>
  </footer>
</body>
</html>
`;
}

const out = (rel) => fileURLToPath(new URL(`../${rel}`, import.meta.url));
mkdirSync(out('en'), { recursive: true });
writeFileSync(out('index.html'), page('de'));
writeFileSync(out('en/index.html'), page('en'));
writeFileSync(out('robots.txt'), `User-agent: *\nAllow: /\n${SITE_URL ? `Sitemap: ${SITE_URL}/sitemap.xml\n` : ''}`);
if (SITE_URL) {
  writeFileSync(out('sitemap.xml'), `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>${SITE_URL}/</loc></url>
  <url><loc>${SITE_URL}/en/</loc></url>
</urlset>
`);
}
console.log(`Startseiten erzeugt (index.html, en/index.html, robots.txt${SITE_URL ? ', sitemap.xml' : ''}).`);
