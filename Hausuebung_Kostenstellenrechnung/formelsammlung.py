"""Formelsammlung Kostenstellenrechnung (BAB) und Zuschlagskalkulation – aus Ü 4.26 bis Ü 4.29.
Alle Beispielwerte werden hier aus den Angaben berechnet (nicht abgetippt).
Aufruf: python3 formelsammlung.py <ausgabe.html>   -> danach mit Chromium zu PDF drucken."""
import sys
from decimal import Decimal, ROUND_HALF_UP


def r2(x):
    return float(Decimal(str(x)).quantize(Decimal('0.01'), ROUND_HALF_UP))


def de(x, nk=2):
    s = f"{r2(x) if nk == 2 else x:,.{nk}f}"
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')


def de0(x):
    return de(x, 0)


def pct(x):
    return de(x) + ' %'


# ---------------------------------------------------------------- Ü 4.26
A = dict(FM=72000, FL1=28500, HL2=11000, GM=6500, GV=12000, LNK=85, GNK=45, MH=1300,
         E=dict(M=1000, F1=3500, F2=3300, V=700), R=dict(M=800, F1=500, F2=900, V=800),
         D=dict(M=16000, F1=63000, F2=32000, V=9000))
a_lnk1 = A['FL1'] * A['LNK'] / 100; a_lnk2 = A['HL2'] * A['LNK'] / 100
a_gnkM = A['GM'] * A['GNK'] / 100; a_gnkV = A['GV'] * A['GNK'] / 100
a_M = A['GM'] + a_gnkM + A['E']['M'] + A['R']['M'] + A['D']['M']
a_F1 = a_lnk1 + A['E']['F1'] + A['R']['F1'] + A['D']['F1']
a_F2 = A['HL2'] + a_lnk2 + A['E']['F2'] + A['R']['F2'] + A['D']['F2']
a_V = A['GV'] + a_gnkV + A['E']['V'] + A['R']['V'] + A['D']['V']
a_HK = A['FM'] + a_M + A['FL1'] + a_F1 + a_F2
a_mgk, a_fgk1, a_msh, a_vw = a_M / A['FM'] * 100, a_F1 / A['FL1'] * 100, a_F2 / A['MH'], a_V / a_HK * 100

# ---------------------------------------------------------------- Ü 4.27
B = dict(FM=980000, FL=790000, LNK=87, GNK=55, G=dict(M=95300, F=157800, V=265500),
         E=dict(M=120500, F=190000, V=75600), R=dict(M=76100, F=200500, V=55400),
         AfA=dict(M=35000, F=480700, V=115500), S=dict(M=85100, F=260000, V=115000))
b_lnk = B['FL'] * B['LNK'] / 100
b_gnk = {k: v * B['GNK'] / 100 for k, v in B['G'].items()}
b_S = {k: B['G'][k] + b_gnk[k] + B['E'][k] + B['R'][k] + B['AfA'][k] + B['S'][k] for k in 'MFV'}
b_S['F'] += b_lnk
b_HK = B['FM'] + b_S['M'] + B['FL'] + b_S['F']
b_mgk, b_fgk, b_vw = b_S['M'] / B['FM'] * 100, b_S['F'] / B['FL'] * 100, b_S['V'] / b_HK * 100

# ---------------------------------------------------------------- Ü 4.28
c_MEK = 25.0; c_MGK = c_MEK * 0.38; c_MK = c_MEK + c_MGK
c_FL = 13.30 * 195 / 60; c_FGK = c_FL * 3.20; c_FK = c_FL + c_FGK
c_HK = c_MK + c_FK; c_VW = c_HK * 0.07; c_VT = c_HK * 0.05; c_SK = c_HK + c_VW + c_VT

# ---------------------------------------------------------------- Ü 4.29
d_MEK = 31.0; d_MGK = d_MEK * 0.25; d_MK = d_MEK + d_MGK
d_FL1 = 13.00 * 110 / 60; d_FGK1 = d_FL1 * 3.40
d_FL2 = 11.40 * 75 / 60; d_FGK2 = d_FL2 * 4.24
d_FK = d_FL1 + d_FGK1 + d_FL2 + d_FGK2
d_HK = d_MK + d_FK; d_VW = d_HK * 0.06; d_VT = d_HK * 0.07; d_SK = d_HK + d_VW + d_VT
d_GW = d_SK * 0.20; d_NVP = d_SK + d_GW; d_UST = d_NVP * 0.20; d_BVP = d_NVP + d_UST
# zeilenweise gerundet (Vergleich)
z = {}
z['MK'] = r2(31) + r2(31 * .25); z['FL1'] = r2(d_FL1); z['FGK1'] = r2(z['FL1'] * 3.4); z['FL2'] = r2(d_FL2); z['FGK2'] = r2(z['FL2'] * 4.24)
z['HK'] = r2(z['MK'] + z['FL1'] + z['FGK1'] + z['FL2'] + z['FGK2']); z['SK'] = r2(z['HK'] + r2(z['HK'] * .06) + r2(z['HK'] * .07))
z['NVP'] = r2(z['SK'] + r2(z['SK'] * .2)); z['BVP'] = r2(z['NVP'] + r2(z['NVP'] * .2))

# Plausibilitätsprüfungen gegen die Werte auf den Heftseiten
assert (de0(a_M), de0(a_F1), de0(a_F2), de0(a_V), de0(a_HK)) == ('27.225', '91.225', '56.550', '27.900', '275.500')
assert (pct(a_mgk), pct(a_fgk1), de(a_msh), pct(a_vw)) == ('37,81 %', '320,09 %', '43,50', '10,13 %')
assert (de0(b_S['M']), de0(b_S['F']), de0(b_S['V']), de0(b_HK)) == ('464.415', '2.063.090', '773.025', '4.297.505')
assert (pct(b_mgk), pct(b_fgk), pct(b_vw)) == ('47,39 %', '261,15 %', '17,99 %')
assert de(c_SK) == '241,97' and de(d_BVP) == '355,20' and de(z['BVP']) == '355,18'


def frac(n, d):
    return f'<span class="frac"><span class="n">{n}</span><span class="d">{d}</span></span>'


def box(title, formula, text, examples, note=''):
    ex = ''.join(f'<li>{e}</li>' for e in examples)
    note = f'<p class="note">{note}</p>' if note else ''
    return f'''<div class="box"><h3>{title}</h3><div class="formula">{formula}</div>
<div class="desc">{text}</div>{note}<div class="ex"><b>Beispiel{"e" if len(examples) > 1 else ""}:</b><ul>{ex}</ul></div></div>'''


X = '&nbsp;·&nbsp;'
H = []
H.append(f'''<!DOCTYPE html><html lang="de"><head><meta charset="utf-8"><title>Formelsammlung Kostenstellenrechnung und Zuschlagskalkulation</title>
<style>
@page {{ size: A4; margin: 16mm 15mm 16mm 15mm; }}
body {{ font-family: 'Carlito', sans-serif; font-size: 10.2pt; line-height: 1.32; color: #1d1d1f;
       font-feature-settings: 'tnum' 1; }}
h1 {{ font-size: 19pt; margin: 0 0 2mm 0; color: #14365d; letter-spacing: -0.2px; }}
.sub {{ color: #555; margin-bottom: 5mm; }}
h2 {{ font-size: 12.5pt; color: #14365d; border-bottom: 1.4px solid #14365d; padding-bottom: 1mm; margin: 5mm 0 2.5mm 0;
      break-after: avoid; }}
h3 {{ font-size: 10.5pt; margin: 0 0 2mm 0; color: #14365d; }}
.box {{ border: 1px solid #c9d3df; border-left: 4px solid #14365d; border-radius: 3px; padding: 2.6mm 4mm; margin: 0 0 3mm 0;
        break-inside: avoid; background: #fbfcfe; }}
.formula {{ font-size: 11.3pt; background: #eef2f7; border-radius: 3px; padding: 2mm 3mm; margin: 0 0 1.8mm 0;
            display: flex; align-items: center; flex-wrap: wrap; gap: 0 1.2mm; }}
.frac {{ display: inline-flex; flex-direction: column; text-align: center; vertical-align: middle; margin: 0 1mm; }}
.frac .n {{ border-bottom: 1.1px solid #1d1d1f; padding: 0 1.5mm 0.4mm; }}
.frac .d {{ padding: 0.4mm 1.5mm 0; }}
.desc p {{ margin: 0 0 1.4mm 0; }}
.ex ul {{ margin: 0.5mm 0 0 0; padding-left: 5mm; }} .ex li {{ margin: 0.3mm 0; }}
.note {{ background: #fff6e0; border-left: 3px solid #e0a100; padding: 1.5mm 2.5mm; margin: 1.5mm 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 1mm 0 3mm 0; font-size: 9.3pt; break-inside: avoid; }}
th, td {{ border: 1px solid #c9d3df; padding: 0.75mm 2mm; vertical-align: top; }}
th {{ background: #14365d; color: white; text-align: left; font-weight: 600; }}
td.r, th.r {{ text-align: right; white-space: nowrap; }}
tr.sum td {{ font-weight: 700; background: #eef2f7; }}
tr.end td {{ font-weight: 700; background: #dfe8f3; border-top: 2px solid #14365d; }}
.abk td:first-child {{ font-weight: 700; width: 17mm; white-space: nowrap; }}
.two {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 3.5mm; margin-bottom: 3mm; break-inside: avoid; }}
.two .box {{ margin: 0; }}
.two .formula {{ font-size: 9.7pt; padding: 2mm 2mm; gap: 0 0.6mm; }}
.small {{ font-size: 8.6pt; color: #444; }}
.op {{ width: 5mm; text-align: center; font-weight: 700; }}
</style></head><body>
<h1>Formelsammlung: Kostenstellenrechnung und Zuschlagskalkulation</h1>
<div class="sub">Betriebsabrechnungsbogen (BAB), Zuschlagssätze, Maschinenstundensatz und Kalkulationsschema –
mit Beispielen aus Ü 4.26 bis Ü 4.29.</div>

<h2>1&nbsp;&nbsp;Abkürzungen und Grundbegriffe</h2>
<div class="two"><table class="abk">
<tr><th colspan="2">Abkürzungen</th></tr>
<tr><td>MEK</td><td>Materialeinzelkosten (Fertigungsmaterial)</td></tr>
<tr><td>MGK</td><td>Materialgemeinkosten</td></tr>
<tr><td>MK</td><td>Materialkosten</td></tr>
<tr><td>FL</td><td>Fertigungslöhne (Fertigungseinzelkosten)</td></tr>
<tr><td>FGK</td><td>Fertigungsgemeinkosten</td></tr>
<tr><td>FK</td><td>Fertigungskosten</td></tr>
<tr><td>HK</td><td>Herstellkosten</td></tr>
<tr><td>VwGK</td><td>Verwaltungsgemeinkosten</td></tr>
<tr><td>VtGK</td><td>Vertriebsgemeinkosten</td></tr>
<tr><td>SK</td><td>Selbstkosten</td></tr>
<tr><td>NVP / BVP</td><td>Netto- / Bruttoverkaufspreis</td></tr>
<tr><td>USt</td><td>Umsatzsteuer</td></tr>
<tr><td>LNK / GNK</td><td>Lohn- / Gehaltsnebenkosten</td></tr>
<tr><td>BAB</td><td>Betriebsabrechnungsbogen</td></tr>
</table>
<div>
<div class="box"><h3>Einzelkosten</h3><div class="desc">Lassen sich <b>einem Produkt direkt zurechnen</b>:
Fertigungsmaterial (MEK) und Fertigungslöhne (FL). Sie stehen <b>nicht</b> im BAB, sind aber die
<b>Zuschlagsbasis</b> für Material- und Fertigungsgemeinkosten.</div></div>
<div class="box"><h3>Gemeinkosten</h3><div class="desc">Fallen für mehrere Produkte gemeinsam an
(Hilfslöhne, Gehälter, Energie, Reinigung, Raumkosten, Abschreibungen …). Sie werden im BAB auf die
<b>Kostenstellen</b> (Material, Fertigung, Verwaltung, Vertrieb) verteilt und über <b>Zuschlagssätze</b>
auf die Produkte umgelegt.</div></div>
</div></div>

<h2>2&nbsp;&nbsp;Lohn- und Gehaltsnebenkosten</h2>
''')

H.append(box('2.1 Lohnnebenkosten',
             f'Lohnnebenkosten = Löhne{X}{frac("LNK-Satz in %", "100")}',
             '<p>LNK-Satz = Lohnnebenkostensatz. Zusätzliche Kosten des Arbeitgebers auf die Löhne (z. B. Arbeitgeberbeiträge zur Sozialversicherung, '
             'Sonderzahlungen), als Prozentsatz angegeben.</p>'
             '<p>Die Lohnnebenkosten auf die <b>Fertigungslöhne</b> sind <b>Gemeinkosten der Fertigungsstelle</b> '
             '(die Fertigungslöhne selbst sind Einzelkosten). Lohnnebenkosten auf <b>Hilfslöhne</b> gehören zur '
             'Kostenstelle, in der die Hilfslöhne anfallen.</p>',
             [f'Ü 4.26 Fertigung 1: {de0(A["FL1"])}{X}{A["LNK"]} % = <b>{de0(a_lnk1)}</b>',
              f'Ü 4.26 Fertigung 2 (Hilfslöhne): {de0(A["HL2"])}{X}{A["LNK"]} % = <b>{de0(a_lnk2)}</b>',
              f'Ü 4.27 Fertigung: {de0(B["FL"])}{X}{B["LNK"]} % = <b>{de0(b_lnk)}</b>']))

H.append(box('2.2 Gehaltsnebenkosten',
             f'Gehaltsnebenkosten = Gehälter{X}{frac("GNK-Satz in %", "100")}',
             '<p>GNK-Satz = Gehaltsnebenkostensatz. Wie die Lohnnebenkosten, aber auf die Gehälter der Angestellten. Sie werden in derselben '
             'Kostenstelle wie das zugehörige Gehalt erfasst.</p>',
             [f'Ü 4.26 Material: {de0(A["GM"])}{X}{A["GNK"]} % = <b>{de0(a_gnkM)}</b>; '
              f'Verwaltung: {de0(A["GV"])}{X}{A["GNK"]} % = <b>{de0(a_gnkV)}</b>',
              f'Ü 4.27 Material: {de0(B["G"]["M"])}{X}{B["GNK"]} % = <b>{de0(b_gnk["M"])}</b>; '
              f'Fertigung: {de0(B["G"]["F"])}{X}{B["GNK"]} % = <b>{de0(b_gnk["F"])}</b>; '
              f'Verwaltung: {de0(B["G"]["V"])}{X}{B["GNK"]} % = <b>{de0(b_gnk["V"])}</b>']))

H.append('<h2>3&nbsp;&nbsp;Betriebsabrechnungsbogen (BAB)</h2>')
H.append(box('3.1 Summe Gemeinkosten je Kostenstelle',
             'Gemeinkosten der Kostenstelle = Summe aller auf diese Kostenstelle verteilten Gemeinkostenarten',
             '<p>Zeilen des BAB = Kostenarten, Spalten = Kostenstellen. Jede Gemeinkostenart wird der Kostenstelle '
             'zugeordnet, in der sie anfällt; dann wird jede Spalte addiert. Darunter folgen die Zeilen '
             '<b>Zuschlagsbasis</b> und <b>Zuschlagssatz</b>.</p>',
             [f'Ü 4.26 Material: {de0(A["GM"])} + {de0(a_gnkM)} + {de0(A["E"]["M"])} + {de0(A["R"]["M"])} + '
              f'{de0(A["D"]["M"])} = <b>{de0(a_M)}</b>',
              f'Ü 4.26 Fertigung 1: {de0(a_lnk1)} + {de0(A["E"]["F1"])} + {de0(A["R"]["F1"])} + {de0(A["D"]["F1"])} = <b>{de0(a_F1)}</b>; '
              f'Fertigung 2: <b>{de0(a_F2)}</b>; Verwaltung: <b>{de0(a_V)}</b>',
              f'Ü 4.27 Material <b>{de0(b_S["M"])}</b>, Fertigung <b>{de0(b_S["F"])}</b>, Verwaltung <b>{de0(b_S["V"])}</b>']))

H.append('<h2>4&nbsp;&nbsp;Zuschlagssätze und Maschinenstundensatz</h2>')
H.append(box('4.1 Materialgemeinkosten-Zuschlagssatz',
             f'MGK-Satz in % = {frac("Materialgemeinkosten" + X + "100", "Materialeinzelkosten")}',
             '<p>Basis ist das <b>Fertigungsmaterial</b> (Materialeinzelkosten). Sagt aus, wie viel Prozent der '
             'Materialeinzelkosten als Materialgemeinkosten aufgeschlagen werden.</p>',
             [f'Ü 4.26: {frac(de0(a_M) + X + "100", de0(A["FM"]))} = <b>{pct(a_mgk)}</b>',
              f'Ü 4.27: {frac(de0(b_S["M"]) + X + "100", de0(B["FM"]))} = <b>{pct(b_mgk)}</b>']))

H.append(box('4.2 Fertigungsgemeinkosten-Zuschlagssatz',
             f'FGK-Satz in % = {frac("Fertigungsgemeinkosten" + X + "100", "Fertigungslöhne")}',
             '<p>Basis sind die <b>Fertigungslöhne derselben Fertigungsstelle</b>. Bei mehreren Fertigungsstellen '
             'wird für jede Stelle ein eigener Satz berechnet.</p>',
             [f'Ü 4.26 Fertigung 1: {frac(de0(a_F1) + X + "100", de0(A["FL1"]))} = <b>{pct(a_fgk1)}</b>',
              f'Ü 4.27: {frac(de0(b_S["F"]) + X + "100", de0(B["FL"]))} = <b>{pct(b_fgk)}</b>']))

H.append(box('4.3 Maschinenstundensatz',
             f'Maschinenstundensatz = {frac("Fertigungsgemeinkosten der Maschinenstelle", "Maschinenstunden")}'
             f'&nbsp;&nbsp;in € je Stunde',
             '<p>Für Kostenstellen, deren Kosten hauptsächlich von den Maschinen verursacht werden (wenig Fertigungslohn). '
             'Ergebnis ist ein <b>Betrag je Stunde</b>, kein Prozentsatz – Einheit immer dazuschreiben.</p>'
             f'<p>In der Kalkulation: Maschinenkosten je Stück = Maschinenstundensatz{X}{frac("Maschinenzeit je Stück in Minuten", "60")}</p>',
             [f'Ü 4.26 Fertigung 2: {frac(de0(a_F2), de0(A["MH"]))} = <b>{de(a_msh)} € je Maschinenstunde</b>']))

H.append(box('4.4 Herstellkosten (Basis für Verwaltung und Vertrieb)',
             'Herstellkosten = MEK + MGK + FL + FGK&nbsp;&nbsp;(alle Fertigungsstellen, auch Maschinenstellen)',
             '<p>Summe aus Materialkosten und Fertigungskosten. Im BAB: Fertigungsmaterial + Summe Material-GK + '
             'Fertigungslöhne + Summe aller Fertigungs-GK.</p>',
             [f'Ü 4.26: {de0(A["FM"])} + {de0(a_M)} + {de0(A["FL1"])} + {de0(a_F1)} + {de0(a_F2)} = <b>{de0(a_HK)}</b>',
              f'Ü 4.27: {de0(B["FM"])} + {de0(b_S["M"])} + {de0(B["FL"])} + {de0(b_S["F"])} = <b>{de0(b_HK)}</b>'],
             note='Gibt es Bestandsveränderungen an fertigen und unfertigen Erzeugnissen, wird für Verwaltung und Vertrieb mit den '
                  '<b>Herstellkosten des Umsatzes</b> gerechnet: Herstellkosten − Bestandsmehrung + Bestandsminderung. '
                  'In Ü 4.26 und Ü 4.27 gab es keine, daher gelten die Herstellkosten direkt.'))

H.append(box('4.5 Verwaltungs- und Vertriebsgemeinkosten-Zuschlagssatz',
             f'<span style="width:100%">VwGK-Zuschlagssatz = {frac("Verwaltungsgemeinkosten" + X + "100", "Herstellkosten")}</span>'
             f'<span style="width:100%;margin-top:1.5mm">VtGK-Zuschlagssatz = {frac("Vertriebsgemeinkosten" + X + "100", "Herstellkosten")}</span>',
             '<p>Basis sind die <b>Herstellkosten</b> (nicht die Einzelkosten). Der Vertriebssatz wird gleich berechnet, '
             'kam in Ü 4.26/4.27 aber nicht vor.</p>',
             [f'Ü 4.26: {frac(de0(a_V) + X + "100", de0(a_HK))} = <b>{pct(a_vw)}</b>',
              f'Ü 4.27: {frac(de0(b_S["V"]) + X + "100", de0(b_HK))} = <b>{pct(b_vw)}</b>']))

H.append(box('4.6 Umkehrung (zum Kontrollieren)',
             f'Gemeinkosten = Zuschlagsbasis{X}{frac("Zuschlagssatz", "100")}&nbsp;&nbsp;&nbsp;&nbsp;'
             f'Zuschlagsbasis = {frac("Gemeinkosten" + X + "100", "Zuschlagssatz")}',
             '<p>Damit lässt sich jeder berechnete Zuschlagssatz schnell gegenprüfen.</p>',
             [f'Ü 4.26: {de0(A["FM"])}{X}{pct(a_mgk)} = {de0(A["FM"] * r2(a_mgk) / 100)} ≈ {de0(a_M)} – passt '
              '(kleine Abweichung nur durch den gerundeten Satz)']))

# ------------------------------------------------ Kalkulationsschema
H.append('<h2>5&nbsp;&nbsp;Zuschlagskalkulation (Kalkulation je Stück)</h2>')
H.append(box('5.1 Fertigungslohn je Stück aus Stundenlohn und Fertigungszeit',
             f'Fertigungslohn je Stück = Stundenlohn{X}{frac("Fertigungszeit in Minuten", "60")}',
             '<p>Die Fertigungszeit ist meist in Minuten angegeben, der Lohn in € je Stunde – deshalb durch 60 teilen.</p>',
             [f'Ü 4.28: 13,30{X}{frac("195", "60")} = {de(c_FL, 3)} ≈ <b>{de(c_FL)} €</b>',
              f'Ü 4.29: 13,00{X}{frac("110", "60")} = <b>{de(d_FL1)} €</b>&nbsp;&nbsp;und&nbsp;&nbsp;11,40{X}{frac("75", "60")} = <b>{de(d_FL2)} €</b>']))


def row(op, lab, form, v1, v2, cls=''):
    return (f'<tr class="{cls}"><td class="op">{op}</td><td>{lab}</td><td>{form}</td>'
            f'<td class="r">{v1}</td><td class="r">{v2}</td></tr>')


T = ['<div class="box"><h3>5.2 Kalkulationsschema</h3><table><tr><th></th><th>Position</th><th>Berechnung</th>'
     '<th class="r">Ü 4.28</th><th class="r">Ü 4.29</th></tr>']
T += [row('', 'Materialeinzelkosten', 'aus der Angabe', de(c_MEK), de(d_MEK)),
      row('+', 'Materialgemeinkosten', 'MEK · MGK-Zuschlagssatz', f'38 % &nbsp; {de(c_MGK)}', f'25 % &nbsp; {de(d_MGK)}'),
      row('=', 'Materialkosten', 'MEK + MGK', de(c_MK), de(d_MK), 'sum'),
      row('', 'Fertigungslöhne (1)', 'Stundenlohn · Minuten : 60', de(c_FL), de(d_FL1)),
      row('+', 'Fertigungsgemeinkosten (1)', 'FL · FGK-Zuschlagssatz', f'320 % &nbsp; {de(c_FGK)}', f'340 % &nbsp; {de(d_FGK1)}'),
      row('', 'Fertigungslöhne 2', 'Stundenlohn · Minuten : 60', '–', de(d_FL2)),
      row('+', 'Fertigungsgemeinkosten 2', 'FL 2 · FGK-Zuschlagssatz 2', '–', f'424 % &nbsp; {de(d_FGK2)}'),
      row('=', 'Fertigungskosten', 'Summe aller FL + FGK', de(c_FK), de(d_FK), 'sum'),
      row('=', 'Herstellkosten', 'Materialkosten + Fertigungskosten', de(c_HK), de(d_HK), 'sum'),
      row('+', 'Verwaltungsgemeinkosten', 'HK · VwGK-Zuschlagssatz', f'7 % &nbsp; {de(c_VW)}', f'6 % &nbsp; {de(d_VW)}'),
      row('+', 'Vertriebsgemeinkosten', 'HK · VtGK-Zuschlagssatz', f'5 % &nbsp; {de(c_VT)}', f'7 % &nbsp; {de(d_VT)}'),
      row('=', 'Selbstkosten', 'HK + VwGK + VtGK', de(c_SK), de(d_SK), 'end' if False else 'sum'),
      row('+', 'Gewinnaufschlag', 'SK · Gewinnsatz', '–', f'20 % &nbsp; {de(d_GW)}'),
      row('=', 'Nettoverkaufspreis', 'SK + Gewinn', '–', de(d_NVP), 'sum'),
      row('+', 'Umsatzsteuer', 'NVP · USt-Satz', '–', f'20 % &nbsp; {de(d_UST)}'),
      row('=', 'Bruttoverkaufspreis', 'NVP + USt', '–', de(d_BVP), 'end')]
T.append('</table><p class="small">Ü 4.28 endet bei den Selbstkosten (<b>' + de(c_SK) + ' €</b>), Ü 4.29 beim '
         'Bruttoverkaufspreis (<b>' + de(d_BVP) + ' €</b>). Alle Beträge in € je Stück.</p></div>')
H.append(''.join(T))

H.append('''<div class="box"><h3>5.3 Merkregel: Worauf bezieht sich welcher Prozentsatz?</h3><table>
<tr><th>Zuschlag</th><th>Basis (= 100 %)</th></tr>
<tr><td>Materialgemeinkosten</td><td>Materialeinzelkosten</td></tr>
<tr><td>Fertigungsgemeinkosten</td><td>Fertigungslöhne <b>derselben</b> Fertigungsstelle</td></tr>
<tr><td>Maschinenkosten</td><td>Maschinenzeit (Maschinenstundensatz · Stunden)</td></tr>
<tr><td>Verwaltungs- und Vertriebsgemeinkosten</td><td>Herstellkosten</td></tr>
<tr><td>Gewinnaufschlag</td><td>Selbstkosten</td></tr>
<tr><td>Umsatzsteuer</td><td>Nettoverkaufspreis</td></tr>
</table></div>''')

H.append(f'''<h2>6&nbsp;&nbsp;Runden und typische Fehler</h2>
<div class="two"><div class="box"><h3>6.1 Runden</h3><div class="desc">
<p>Zwischenergebnisse <b>ungerundet</b> weiterrechnen, angeschriebene Beträge kaufmännisch auf <b>2 Nachkommastellen</b>
(Prozentsätze ebenfalls auf 2 Nachkommastellen).</p>
<p>Dadurch können die angeschriebenen Zeilen um 1 Cent von ihrer Summe abweichen. Beispiel Ü 4.29:
{de(d_HK)} + {de(d_VW)} + {de(d_VT)} = {de(r2(d_HK) + r2(d_VW) + r2(d_VT))}, angeschrieben sind {de(d_SK)} (genauer Wert {de(d_SK, 4)}).</p>
<p>Wird stattdessen jede Zeile sofort gerundet und mit dem gerundeten Wert weitergerechnet, ergibt Ü 4.29 einen
Bruttoverkaufspreis von <b>{de(z["BVP"])} €</b> statt {de(d_BVP)} €. Welche Variante verlangt ist, gibt die Lehrkraft vor.</p>
</div></div>
<div class="box"><h3>6.2 Typische Fehler</h3><div class="desc"><ul style="margin:0;padding-left:5mm">
<li><b>Fertigungslöhne oder Fertigungsmaterial im BAB als Gemeinkosten eintragen</b> – sie sind Einzelkosten und nur Zuschlagsbasis.
Nur ihre Lohnnebenkosten gehören in den BAB.</li>
<li><b>Zeile „Zuschlagsbasis“ vergessen</b> – ohne sie ist der Zuschlagssatz im BAB nicht nachvollziehbar.</li>
<li><b>Falsche Basis</b> – Verwaltung und Vertrieb immer auf die Herstellkosten, nicht auf die Einzelkosten.</li>
<li><b>Maschinenstundensatz ohne Einheit</b> – richtig: „43,50 € je Maschinenstunde“, kein Prozentzeichen.</li>
<li><b>Minuten nicht in Stunden umrechnen</b> – Fertigungszeit in Minuten immer durch 60 teilen.</li>
<li><b>Mehrere Fertigungsstellen mit einem Satz rechnen</b> – jede Stelle hat ihren eigenen Zuschlagssatz (Ü 4.29: 340 % und 424 %).</li>
</ul></div></div></div>
</body></html>''')



def pair(ta, tb):
    """Zwei aufeinanderfolgende Kästen nebeneinander setzen (spart Platz)."""
    i = next(k for k, e in enumerate(H) if e.startswith('<div class="box"><h3>' + ta))
    assert H[i + 1].startswith('<div class="box"><h3>' + tb)
    H[i] = '<div class="two">' + H[i] + H[i + 1] + '</div>'; del H[i + 1]


pair('2.1', '2.2'); pair('4.1', '4.2')
open(sys.argv[1] if len(sys.argv) > 1 else 'formelsammlung.html', 'w', encoding='utf-8').write(''.join(H))
print('ok')
