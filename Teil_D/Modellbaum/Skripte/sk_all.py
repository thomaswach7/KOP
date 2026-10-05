import math
from skizzen import SK
import replay as R

def r2(k, cx, cr, a_tip, rechts=True, lang=10.5):
    """Radiusmass R2 an einer Hohlkehle: Hinweislinie von aussen durch den Mittelpunkt auf den Bogen."""
    at = math.radians(a_tip)
    tip = k.T(cx + 2*math.cos(at), cr + 2*math.sin(at)); far = k.T(cx - lang*math.cos(at), cr - lang*math.sin(at))
    k.line([far, tip]); k.arrow(tip, far)
    k.line([far, (far[0] + (12 if rechts else -12), far[1])])
    k.text(far[0] + (2 if rechts else -10), far[1] + 0.9, "R2", 3.5)
S2 = math.sqrt(2)

def s_pos3():
    k = SK(-30, 100, -12, 100, 1.4)
    k.prof([(0, 68), (70, 68), (70, 85), (0, 85)]); k.axis(-5, 75)
    k.hdim(0, 70, 85, 85, 93, "70")
    k.ddim(70, 68, 78, "Ø136"); k.ddim(70, 85, 88, "Ø170")
    k.png("mb/pos3_s1.png")

def s_pos9():
    k = SK(-8, 60, -4, 16, 1.6)
    k.prof([(0, 0), (0, 4), (50, 4), (50, 0)], close=False); k.axis(-3, 53)
    k.hdim(0, 50, 4, 4, 10, "50"); k.ddim(50, 4, 55, "Ø8")
    k.png("mb/pos9_s1.png")
    k = SK(-4, 22, -6, 16, 6.0)
    k.prof([(0, 0), (0, 4), (14, 4)], close=False, lw=0.6)
    k.prof([(7, 3.5), (7, 4.6), (7.94, 4.6), (7.94, 3.5)])
    k.axis(-2, 16)
    k.hdim(0, 7, 4, 4.6, 7, "7"); k.hdim(7, 7.94, 4.6, 4.6, 10, "0,94", arrows_out=True, tpos=2.5)
    k.ddim(7.94, 3.5, 11, "Ø7")
    k.png("mb/pos9_s2.png")
    k = SK(-4, 14, -6, 16, 7.0)
    k.prof([(0, 0), (0, 4), (10, 4)], close=False, lw=0.6)
    k.prof([(2.4, 4), ("A", (3.0, 3.4), (3.6, 4)), (3.6, 4.4), (2.4, 4.4)])
    k.axis(-2, 12)
    k.hdim(0, 3.0, 4, 4, 7.5, "3", tpos=0.5); k.radius(k.T(3.0, 4.0), 0.6*7, -60, "R0,6", ext=8)
    k.png("mb/pos9_s4.png")

def s_pos6():
    import matplotlib.pyplot as plt
    k = SK(-14, 14, -14, 14, 4.0)
    for r in (8, 4.5): k.ax.add_patch(plt.Circle(k.T(0, 0), r*4, fill=False, lw=TH, color="k"))
    k.cl(k.T(-11, 0), k.T(11, 0)); k.cl(k.T(0, -11), k.T(0, 11))
    a = math.radians(40); p1, p2 = k.T(8*math.cos(a), 8*math.sin(a)), k.T(-8*math.cos(a), -8*math.sin(a))
    k.line([p1, p2]); k.arrow(p1, p2); k.arrow(p2, p1); k.text(*k.T(4.2, 5.6), "Ø16", 3.5, rot=40)
    a = math.radians(-30); p1, p2 = k.T(4.5*math.cos(a), 4.5*math.sin(a)), k.T(-4.5*math.cos(a), -4.5*math.sin(a))
    k.line([p1, p2]); k.arrow(p1, p2); k.arrow(p2, p1); k.text(*k.T(-3.6, 1.0), "Ø9", 3.5, rot=-30)
    k.png("mb/pos6_s1.png")

from dimlib import TH

def s_pos12():
    k = SK(-6, 16, -6, 36, 3.0)
    k.prof([(0, 22.5), (0, 23.0), (0.74, 29.0), (4.74, 29.0), (5.48, 23.0), (5.48, 22.5)])
    k.axis(-4, 14, 0)
    k.hdim(0.74, 4.74, 29, 29, 32, "4"); k.ddim(5.48, 22.5, 9, "Ø45"); k.ddim(4.74, 29, 12.5, "Ø58")
    k.text(*k.T(-5.5, 33.5), "7°", 3); k.text(*k.T(6.0, 33.5), "7°", 3)
    k.png("mb/pos12_s1.png")

def s_pos4():
    k = SK(-42, 75, -8, 106, 1.6)
    k.prof(R.DECKEL); k.axis(-5, 40)
    k.hdim(0, 12, 85, 85, 90, "12"); k.hdim(0, 19, 85, 68, 96, "19"); k.hdim(0, 29, 85, 42.01, 102, "29")
    k.hdim(0, 11, 23, 23, 15, "11", ext1=True); k.hdim(0, 13, 23, 37.5, 9, "13")
    k.hdim(0, 7.5, 23, 29, 3.5, "7,5")
    k.ddim(19, 68, 36, "Ø136"); k.ddim(19, 62.5, 42, "Ø125"); k.ddim(0, 85, -6, "Ø170")
    k.ddim(29, 42.01, 48, "Ø84"); k.ddim(29, 37.5, 54, "Ø75"); k.ddim(13, 35, 60, "Ø70")
    k.ddim(0, 23, -14, "Ø46"); k.ddim(3.5, 29, -22, "Ø58")
    k.text(*k.T(31, 46), "5° (Aushebeschräge)", 3)
    k.text(*k.T(-40, 34), "Nut: unten 4 breit,\nFlanken je 7°", 3)
    r2(k, 13, 33, 135, lang=9)
    k.png("mb/pos4_s1.png")

def s_pos2():
    k = SK(-30, 112, -8, 112, 1.5)
    k.prof(R.ABTRIEB); k.axis(-5, 80)
    k.hdim(0, 43, 25, 85, 90, "43"); k.hdim(0, 55, 25, 85, 96, "55"); k.hdim(0, 62, 25, 68, 102, "62")
    k.hdim(0, 72, 25, 42.63, 108, "72")
    k.hdim(0, 54, 15, 15, 9, "54"); k.hdim(0, 56, 15, 35, 4, "56")
    k.ddim(0, 15, -6, "Ø30"); k.ddim(0, 25, -13, "Ø50"); k.ddim(43, 85, -21, "Ø170")
    k.ddim(62, 68, 80, "Ø136"); k.ddim(62, 62.5, 86, "Ø125"); k.ddim(72, 42.63, 92, "Ø85,3")
    k.ddim(72, 37.5, 98, "Ø75"); k.ddim(56, 35, 104, "Ø70")
    k.text(*k.T(64, 46), "5°", 3)
    r2(k, 56, 33, 135, lang=9)
    k.png("mb/pos2_s1.png")

def s_pos1():
    k = SK(-24, 96, -8, 54, 1.8)
    k.prof(R.ANTRIEB); k.axis(-5, 86)
    k.hdim(0, 81, 22.5, 22.5, 46, "81"); k.hdim(0, 29, 22.5, 25.5, 30, "29"); k.hdim(0, 31, 22.5, 38.5, 41, "31")
    k.hdim(81, 63, 22.5, 38.5, 41, "18") ; k.hdim(81, 65, 22.5, 25.5, 30, "16")
    k.ddim(0, 15, -6, "Ø30"); k.ddim(0, 22.5, -13, "Ø45"); k.ddim(29, 25.5, -20, "Ø51")
    k.ddim(47, 38.5, 47, "Ø77") if False else k.ddim(81, 38.5, 89, "Ø77")
    k.ddim(65, 25.5, 85, "Ø51")
    # R2 (Hohlkehle): Mittelpunkte (29|27,5) und (65|27,5); Hinweislinie von aussen durch den Mittelpunkt
    for (cx, cr), a_tip, txt_dx in (((29, 27.5), -45, -9.0), ((65, 27.5), 225, 2.0)):
        at = math.radians(a_tip)
        tip = k.T(cx + 2*math.cos(at), cr + 2*math.sin(at)); far = k.T(cx - 10.5*math.cos(at), cr - 10.5*math.sin(at))
        k.line([far, tip]); k.arrow(tip, far)
        k.line([far, (far[0] + txt_dx*1.8*0 + (12 if txt_dx > 0 else -12), far[1])])
        k.text(far[0] + (2 if txt_dx > 0 else -10), far[1] + 0.9, "R2", 3.5)
    k.png("mb/pos1_s1.png")
    import matplotlib.pyplot as plt
    k = SK(-40, 40, -70, 70, 1.6)
    th = [i/100*2*math.pi for i in range(101)]
    k.line([k.T(38.5*math.cos(t), 38.5*math.sin(t)) for t in th], lw=0.6)
    for sg in (1, -1):
        k.line([k.T(-9, sg*30), k.T(-9, sg*52), *[k.T(9*math.cos(t), sg*(52 + 9*math.sin(t))) for t in [math.pi - i/30*math.pi for i in range(31)]], k.T(9, sg*30), k.T(-9, sg*30)])
    k.cl(k.T(-30, 0), k.T(30, 0)); k.cl(k.T(0, -66), k.T(0, 66))
    k.dim(k.T(-9, 30), k.T(9, 30), k.T(0, 25)[1] if False else k.T(0, 66)[1], "18", "h")
    k.dim(k.T(9, 52), k.T(9, -52), k.T(22, 0)[0], "104", "v")
    k.radius(k.T(0, 52), 9*1.6, 35, "R9", ext=10)
    k.png("mb/pos1_s4.png")

def s_pos51():
    import numpy as np
    k = SK(-72, 72, -72, 8, 1.4)
    pol = R.pol
    def arc(r, a1, a2, n=60): return [k.T(*pol(r, a)) for a in np.linspace(a1, a2, n)]
    pts = arc(62, -51, 51) + [k.T(*pol(60, 51))] + arc(60, 51, 52.13, 4)
    c = pol(55.75, 52.13); ang0 = math.degrees(math.atan2(pol(60, 52.13)[1]-c[1], pol(60, 52.13)[0]-c[0]))
    pts += [k.T(c[0] + 4.25*math.cos(math.radians(ang0 + t)), c[1] + 4.25*math.sin(math.radians(ang0 + t))) for t in np.linspace(0, -180, 30)]
    pts += arc(51.5, 52.13, -52.13)
    c2 = pol(55.75, -52.13); a2 = math.degrees(math.atan2(pol(51.5, -52.13)[1]-c2[1], pol(51.5, -52.13)[0]-c2[0]))
    pts += [k.T(c2[0] + 4.25*math.cos(math.radians(a2 + t)), c2[1] + 4.25*math.sin(math.radians(a2 + t))) for t in np.linspace(0, -180, 30)]
    pts += arc(60, -52.13, -51, 4) + [k.T(*pol(62, -51))]
    k.line(pts)
    k.cl(k.T(0, 6), k.T(0, -68)); k.cl(k.T(-10, 0), k.T(10, 0))
    for a in (51, -51): k.line([k.T(0, 0), k.T(*pol(66, a))], lw=0.3)
    k.text(*k.T(-6, -40), "102°", 3.5)
    for r, a, t in ((62, 20, "R62"), (51.5, -15, "R51,5"), (60, 40, "R60")):
        p = k.T(*pol(r, a)); k.line([k.T(0, 0), p]); k.arrow(p, k.T(0, 0)); k.text(p[0]+1, p[1]+1, t, 3.2)
    k.radius(k.T(*pol(55.75, 52.13)), 4.25*1.4, 10, "R4,25", ext=8)
    k.png("mb/pos51_s1.png")
    k = SK(-72, 72, -72, 8, 1.4)
    pts = arc(60, -67.5, 67.5)
    c = pol(51.5, 67.5); a0 = math.degrees(math.atan2(pol(60, 67.5)[1]-c[1], pol(60, 67.5)[0]-c[0]))
    pts += [k.T(c[0] + 8.5*math.cos(math.radians(a0 + t)), c[1] + 8.5*math.sin(math.radians(a0 + t))) for t in np.linspace(0, -180, 30)]
    pts += arc(43, 67.5, -67.5)
    c = pol(51.5, -67.5); a0 = math.degrees(math.atan2(pol(43, -67.5)[1]-c[1], pol(43, -67.5)[0]-c[0]))
    pts += [k.T(c[0] + 8.5*math.cos(math.radians(a0 + t)), c[1] + 8.5*math.sin(math.radians(a0 + t))) for t in np.linspace(0, -180, 30)]
    pts.append(pts[0]); k.line(pts)
    for a in (67.5, -67.5): k.line([k.T(0, 0), k.T(*pol(51.5, a))], lw=0.3)
    k.cl(k.T(0, 6), k.T(0, -68))
    k.text(*k.T(-6, -30), "135°", 3.5)
    for r, a, t in ((60, 25, "R60"), (43, -20, "R43")):
        p = k.T(*pol(r, a)); k.line([k.T(0, 0), p]); k.arrow(p, k.T(0, 0)); k.text(p[0]+1, p[1]+1, t, 3.2)
    k.radius(k.T(*pol(51.5, 67.5)), 8.5*1.4, 20, "R8,5", ext=8)
    k.png("mb/pos51_s3.png")

def s_pos52():
    import numpy as np
    k = SK(-72, 72, -72, 8, 1.4)
    pol = R.pol
    a5 = 46 - math.degrees(5/65)
    pts = [k.T(*pol(62, a)) for a in np.linspace(-46, 46, 80)] + [k.T(*pol(63.5, 46))] + [k.T(*pol(65, a)) for a in np.linspace(a5, -a5, 80)] + [k.T(*pol(63.5, -46)), k.T(*pol(62, -46))]
    k.line(pts)
    for a in (46, -46): k.line([k.T(0, 0), k.T(*pol(66, a))], lw=0.3)
    k.cl(k.T(0, 6), k.T(0, -68)); k.text(*k.T(-5, -40), "92°", 3.5)
    for r, a, t in ((62, 10, "R62"), (65, -20, "R65")):
        p = k.T(*pol(r, a)); k.line([k.T(0, 0), p]); k.arrow(p, k.T(0, 0)); k.text(p[0]+1, p[1]+1, t, 3.2)
    k.png("mb/pos52_s1.png")

def s_pos7():
    import numpy as np
    k = SK(-12, 30, -10, 12, 4.0)
    k.line([k.T(0.55, 3.45), k.T(14.85, 3.45)]); k.axis(-2, 17)
    k.hdim(0.55, 14.85, 3.45, 3.45, 7, "14,3"); k.ddim(14.85, 3.45, 19, "Ø6,9")
    k.ax.add_patch(__import__("matplotlib").patches.Circle(k.T(0.55, 3.45), 0.55*4, fill=False, lw=0.8, color="k"))
    k.png("mb/pos7_s1.png")
    k = SK(-12, 12, -10, 10, 4.0)
    gap = math.degrees(2/3.45)
    pts = [k.T(3.45*math.cos(math.radians(t)), 3.45*math.sin(math.radians(t))) for t in np.linspace(90 - gap/2 + 0, -270 + gap/2 + 0, 80)]
    k.line(pts); k.cl(k.T(-6, 0), k.T(6, 0)); k.cl(k.T(0, -6), k.T(0, 6))
    k.radius(k.T(0, 0), 3.45*4, -40, "R3,45", outside=False)
    k.png("mb/pos7_s2.png")

if __name__ == "__main__":
    for f in (s_pos3, s_pos9, s_pos6, s_pos12, s_pos4, s_pos2, s_pos1, s_pos51, s_pos52, s_pos7):
        f(); print(f.__name__, "ok")
