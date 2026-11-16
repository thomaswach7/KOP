"""Lösung Ü 4.26 – Ü 4.29 (Kostenstellenrechnung), alle Werte nachgerechnet."""
from decimal import Decimal as D, ROUND_HALF_UP


def r2(x):
    return D(str(x)).quantize(D('0.01'), ROUND_HALF_UP)


def eur(x):
    """deutsches Format: 1.234,56"""
    s = f"{r2(x):,.2f}"
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')


# ------------------------------------------------------------------ Ü 4.26
print('=== Ü 4.26 ===')
LNK, GNK = 0.85, 0.45
FM = 72000.0
FL1 = 28500.0
HL2 = 11000.0                       # Hilfslöhne Fertigung 2
geh = dict(M=6500.0, V=12000.0)
lnk1 = FL1 * LNK                   # Lohnnebenkosten auf Fertigungslöhne F1
lnk2 = HL2 * LNK
gnkM = geh['M'] * GNK
gnkV = geh['V'] * GNK
print('LNK F1', lnk1, 'LNK F2', lnk2, 'GNK M', gnkM, 'GNK V', gnkV)
energie = dict(M=1000, F1=3500, F2=3300, V=700)
reinig = dict(M=800, F1=500, F2=900, V=800)
div = dict(M=16000, F1=63000, F2=32000, V=9000)
S = dict(
    M=geh['M'] + gnkM + energie['M'] + reinig['M'] + div['M'],
    F1=lnk1 + energie['F1'] + reinig['F1'] + div['F1'],
    F2=HL2 + lnk2 + energie['F2'] + reinig['F2'] + div['F2'],
    V=geh['V'] + gnkV + energie['V'] + reinig['V'] + div['V'],
)
print('Summen GK', S)
mgk = S['M'] / FM * 100
fgk1 = S['F1'] / FL1 * 100
msh = S['F2'] / 1300
HK = FM + S['M'] + FL1 + S['F1'] + S['F2']
vwgk = S['V'] / HK * 100
print(f'MGK {mgk:.6f} %  FGK1 {fgk1:.6f} %  MStdSatz {msh:.6f} €/h  HK {HK}  VwGK {vwgk:.6f} %')

# ------------------------------------------------------------------ Ü 4.27
print('=== Ü 4.27 ===')
LNK, GNK = 0.87, 0.55
FM, FL = 980000.0, 790000.0
G = dict(M=95300.0, F=157800.0, V=265500.0)
E = dict(M=120500, F=190000, V=75600)
R = dict(M=76100, F=200500, V=55400)
A = dict(M=35000, F=480700, V=115500)
So = dict(M=85100, F=260000, V=115000)
lnk = FL * LNK
gnk = {k: v * GNK for k, v in G.items()}
print('LNK', lnk, 'GNK', gnk)
S7 = {k: G[k] + gnk[k] + E[k] + R[k] + A[k] + So[k] for k in G}
S7['F'] += lnk
print('Summen GK', S7)
HK7 = FM + S7['M'] + FL + S7['F']
print(f"MGK {S7['M']/FM*100:.6f} %  FGK {S7['F']/FL*100:.6f} %  HK {HK7}  VwGK {S7['V']/HK7*100:.6f} %")

# ------------------------------------------------------------------ Ü 4.28
print('=== Ü 4.28 ===')
MEK = 25.0
MGK = MEK * 0.38
MK = MEK + MGK
FLs = 13.30 * 195 / 60
FGK = FLs * 3.20
FK = FLs + FGK
HK8 = MK + FK
VW = HK8 * 0.07
VT = HK8 * 0.05
SK = HK8 + VW + VT
for n, v in [('MEK', MEK), ('MGK', MGK), ('MK', MK), ('FL', FLs), ('FGK', FGK), ('FK', FK), ('HK', HK8),
             ('VwGK', VW), ('VtGK', VT), ('SK', SK)]:
    print(f'{n:5s} {v:12.5f}  -> {eur(v)}')

# ------------------------------------------------------------------ Ü 4.29
print('=== Ü 4.29 ===')
MEK = 31.0
MGK = MEK * 0.25
MK = MEK + MGK
FL1 = 13.00 * 110 / 60
FGK1 = FL1 * 3.40
FL2 = 11.40 * 75 / 60
FGK2 = FL2 * 4.24
HK9 = MK + FL1 + FGK1 + FL2 + FGK2
VW = HK9 * 0.06
VT = HK9 * 0.07
SK = HK9 + VW + VT
GW = SK * 0.20
NVP = SK + GW
UST = NVP * 0.20
BVP = NVP + UST
for n, v in [('MEK', MEK), ('MGK', MGK), ('MK', MK), ('FL1', FL1), ('FGK1', FGK1), ('FK1', FL1 + FGK1),
             ('FL2', FL2), ('FGK2', FGK2), ('FK2', FL2 + FGK2), ('HK', HK9), ('VwGK', VW), ('VtGK', VT),
             ('SK', SK), ('Gew', GW), ('NVP', NVP), ('USt', UST), ('BVP', BVP)]:
    print(f'{n:5s} {v:12.5f}  -> {eur(v)}')
