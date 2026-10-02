import math, pickle, datetime
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from shapely.geometry import LineString, MultiLineString, Polygon
from shapely import affinity
import build

MM = 72/25.4
TH, TN = 0.5*MM, 0.25*MM
FV = (112.0, 180.0); SV = (222.0, 180.0)
d = pickle.load(open("views.pkl","rb"))
HATCH = {"1":(45,3.0),"2":(135,3.0),"3":(45,2.0),"4":(135,2.5),"5.1":(45,1.6),"5.2":("x",1.4),"6":(135,0.9)}
FONT = dict(family="DejaVu Sans")

fig = plt.figure(figsize=(420/25.4, 297/25.4))
ax = fig.add_axes([0,0,1,1]); ax.set_xlim(0,420); ax.set_ylim(0,297); ax.set_aspect("equal"); ax.axis("off")

def line(pts, lw=TH, ls="-", **kw):
    a = np.array(pts); ax.plot(a[:,0], a[:,1], color="k", lw=lw, ls=ls, solid_capstyle="round", **kw)
def dashdot(p, q, lw=TN):
    ax.plot([p[0],q[0]],[p[1],q[1]], color="k", lw=lw, dashes=(12*MM/TN/4, 1.5*MM/TN/4, 0.5*MM/TN/4, 1.5*MM/TN/4)) 
def cl(p, q):   # Mittellinie (schmale Strich-Punkt-Linie)
    ax.plot([p[0],q[0]],[p[1],q[1]], color="k", lw=TN, dashes=(14,3,1.5,3))
def text(x,y,s,size=3.5,**kw):
    ax.text(x,y,s,fontsize=size*MM/0.72,**FONT,**kw)   # Schrifthoehe h ~ Versalhoehe

# ---------------- Ansichten --------------------------------------------------------------
for pl in d["fv_lines"]: line([(FV[0]+x, FV[1]+y) for x,y in pl])
for pl in d["sec_lines"]: line([(SV[0]+x, SV[1]+y) for x,y in pl])

def hatch(poly, ang, sp):
    if poly.is_empty: return
    minx,miny,maxx,maxy = poly.bounds; cx,cy=(minx+maxx)/2,(miny+maxy)/2
    R = math.hypot(maxx-minx, maxy-miny)
    angs = [45,135] if ang=="x" else [ang]
    for a in angs:
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        ls = []
        k = -R
        while k <= R:
            ox, oy = cx - sa*k, cy + ca*k
            ls.append(LineString([(ox-ca*R, oy-sa*R),(ox+ca*R, oy+sa*R)]))
            k += sp
        inter = MultiLineString(ls).intersection(poly)
        geoms = getattr(inter, "geoms", [inter])
        for g in geoms:
            if g.geom_type=="LineString" and not g.is_empty:
                xs,ys = g.xy; ax.plot(np.array(xs)+SV[0], np.array(ys)+SV[1], color="k", lw=TN)
            elif hasattr(g,"geoms"):
                for gg in g.geoms:
                    xs,ys = gg.xy; ax.plot(np.array(xs)+SV[0], np.array(ys)+SV[1], color="k", lw=TN)
for pos, poly in d["polys"]:
    a, sp = HATCH[pos]; hatch(poly, a, sp)

# Gewinde M8 im Gehaeuse (Pos. 3), Schnitt: Nenn-d schmal, Gewindeende breit
for zs in (75, -75):
    for x0, x1 in ((12, 32), (82, 62)):
        for dz in (4, -4):
            line([(SV[0]+x0, SV[1]+zs+dz), (SV[0]+x1, SV[1]+zs+dz)], lw=TN)
        line([(SV[0]+x1, SV[1]+zs-4), (SV[0]+x1, SV[1]+zs+4)])
# Mittellinien Schnitt
cl((SV[0]-6, SV[1]), (SV[0]+143, SV[1]))
for zs in (75,-75):
    cl((SV[0]+7, SV[1]+zs), (SV[0]+43, SV[1]+zs)); cl((SV[0]+51, SV[1]+zs), (SV[0]+87, SV[1]+zs))
for zs in (52,-52):
    cl((SV[0]+17, SV[1]+zs), (SV[0]+77, SV[1]+zs))
# Mittellinien Vorderansicht
cl((FV[0]-91, FV[1]), (FV[0]+91, FV[1])); cl((FV[0], FV[1]-91), (FV[0], FV[1]+91))
th = np.linspace(0, 2*math.pi, 400)
ax.plot(FV[0]+75*np.cos(th), FV[1]+75*np.sin(th), color="k", lw=TN, dashes=(14,3,1.5,3))
for k in range(6):
    a = math.radians(30+60*k); x, y = FV[0]+75*math.cos(a), FV[1]+75*math.sin(a)
    cl((x-7*math.cos(a), y-7*math.sin(a)), (x+7*math.cos(a), y+7*math.sin(a)))
for (yy, zz) in build.PINS:
    x, y = FV[0]+yy, FV[1]+zz
    cl((x-11, y), (x+11, y)); cl((x, y-11), (x, y+11))

# Schnittverlauf A-A in Vorderansicht (Blick in +Y -> Pfeile nach rechts)
for sgn in (1,-1):
    y0 = FV[1]+sgn*91; y1 = FV[1]+sgn*97
    ax.plot([FV[0],FV[0]],[y0,y1], color="k", lw=2*TH)
    ax.annotate("", xy=(FV[0]+8, y1-sgn*1.5), xytext=(FV[0]-0.3, y1-sgn*1.5),
                arrowprops=dict(arrowstyle="-|>", lw=TN, color="k", mutation_scale=9))
    text(FV[0]+9.5, y1-sgn*1.5-2.5, "A", size=5)
text(SV[0]+100, SV[1]+94, "A–A", size=5, ha="center")
text(FV[0], FV[1]-104, "(ohne Pos. 2 gezeichnet)", size=3.5, ha="center")

# ---------------- Positionsnummern (im Uhrzeigersinn) ------------------------------------
POS = [  # (Nr, Textpos (X,Z), Ziel (X,Z)) in Koordinaten der Schnittansicht
    ("4", (-22, -40), (6, -50)),
    ("5", (-22,  70), (33.5, 59.5)),
    ("6", ( 40,  94), (37.75, 59.5)),
    ("7", (152,  84), (72.5, 50.5)),
    ("8", (152,  68), (64.65, 46)),
    ("1", (152,  36), (75, 19)),
    ("2", (152,  10), (118, 18)),
    ("3", (152, -60), (47, -77)),
]
for nr, (tx,tz), (px,pz) in POS:
    T = (SV[0]+tx, SV[1]+tz); P = (SV[0]+px, SV[1]+pz)
    # Hinweislinie endet am Ziffernrand
    dx, dy = P[0]-T[0], P[1]-T[1]; L = math.hypot(dx,dy)
    start = (T[0]+dx/L*3.2, T[1]+dy/L*3.2)
    ax.plot([start[0],P[0]],[start[1],P[1]], color="k", lw=TN)
    ax.add_patch(Circle(P, 0.6, color="k"))
    text(T[0], T[1], nr, size=5, ha="center", va="center")

# ---------------- Rahmen, Schriftfeld, Stueckliste ---------------------------------------
def rect(x,y,w,h,lw=TH): ax.add_patch(plt.Rectangle((x,y),w,h,fill=False,lw=lw,color="k"))
rect(20,10,390,277, lw=0.7*MM)
for x in (210,): ax.plot([x,x],[287,292],color="k",lw=TH); ax.plot([x,x],[5,10],color="k",lw=TH)
ax.plot([0+10,20],[148.5,148.5],color="k",lw=TH)   # Lochmarke
# Schriftfeld DIN EN ISO 7200 (180 x 36)
X0, Y0, W = 230, 10, 180
rect(X0,Y0,W,36)
ax.plot([X0,X0+W],[Y0+18,Y0+18],color="k",lw=TN)
ax.plot([X0,X0+W],[Y0+27,Y0+27],color="k",lw=TN)
for x in (X0+40, X0+90, X0+135): ax.plot([x,x],[Y0+27,Y0+36],color="k",lw=TN)
ax.plot([X0+60,X0+60],[Y0,Y0+27],color="k",lw=TN)
ax.plot([X0+130,X0+130],[Y0,Y0+27],color="k",lw=TN)
ax.plot([X0+130,X0+W],[Y0+9,Y0+9],color="k",lw=TN)
for x in (X0+138,X0+163,X0+171): ax.plot([x,x],[Y0,Y0+9],color="k",lw=TN)
small=1.8
text(X0+1,Y0+34,"Verantwortl. Abt.",small); text(X0+41,Y0+34,"Technische Referenz",small)
text(X0+91,Y0+34,"Erstellt durch",small);   text(X0+136,Y0+34,"Genehmigt von",small)
text(X0+41,Y0+29,"Projekt Fliehkraftkupplung",2.5)
text(X0+91,Y0+29,"",2.5)
text(X0+61,Y0+25,"Dokumentenart",small); text(X0+64,Y0+20,"Gesamtzeichnung",3.5)
text(X0+131,Y0+25,"Dokumentenstatus",small); text(X0+133,Y0+20,"in Bearbeitung",2.5)
text(X0+61,Y0+16,"Titel, Zusätzlicher Titel",small)
text(X0+95,Y0+8.5,"Fliehkraftkupplung",5,ha="center")
text(X0+95,Y0+2.5,"mit Passfederverbindung – Pos. 1 bis 8",2.5,ha="center")
text(X0+131,Y0+16,"Sachnummer",small); text(X0+133,Y0+11,"14.2.3",3.5)
text(X0+131,Y0+7,"Änd.",small); text(X0+139,Y0+7,"Ausgabedatum",small); text(X0+164,Y0+7,"Spr.",small); text(X0+172,Y0+7,"Blatt",small)
text(X0+132,Y0+2,"A",2.5); text(X0+140,Y0+2,datetime.date.today().isoformat(),2.5); text(X0+165,Y0+2,"de",2.5); text(X0+173,Y0+2,"1/1",2.5)
text(X0+3,Y0+20,"5. Jg. Mechatronik",3.5); text(X0+3,Y0+12,"Maßstab 1:1",3.5); text(X0+3,Y0+5,"Format A3",3.5)
# Projektionssymbol (Methode 1)
px, py = X0+48, Y0+5.5
ax.add_patch(plt.Polygon([(px-7,py-1.5),(px-7,py+1.5),(px-1.5,py+3),(px-1.5,py-3)],fill=False,lw=TN,color="k"))
ax.add_patch(Circle((px+4,py),3,fill=False,lw=TN,color="k")); ax.add_patch(Circle((px+4,py),1.5,fill=False,lw=TN,color="k"))
ax.plot([px-8.5,px+8.5],[py,py],color="k",lw=TN,dashes=(6,2,1,2)); ax.plot([px+4,px+4],[py-4.5,py+4.5],color="k",lw=TN,dashes=(6,2,1,2))

# Stueckliste (von unten nach oben, Kopf unten, direkt auf dem Schriftfeld)
ROWS = [("1","1","Stk","Antriebsnabe","","EN-GJS-700-2"),
        ("2","1","Stk","Abtriebsnabe","","EN-GJS-700-2"),
        ("3","1","Stk","Gehäuse","","E295"),
        ("4","1","Stk","Deckel","","EN-GJS-700-2"),
        ("5","2","Stk","Fliehgewicht (komplett)","",""),
        ("5.1","2","Stk","Gewicht","","EN-GJS-700-2"),
        ("5.2","2","Stk","Belag","","geklebt"),
        ("6","4","Stk","Scheibe","","S235JR"),
        ("7","4","Stk","Zugfeder","","Federstahl"),
        ("8","8","Stk","Sicherungsscheibe","DIN 6799 – 7","")]
COLS = [0,12,24,36,88,145,180]
HDR = ["Pos.","Menge","Einh.","Benennung","Sachnummer/Norm – Kurzbezeichnung","Werkstoff/Bemerkung"]
rh = 4.0; yb = Y0+36
rect(X0, yb, W, rh*(len(ROWS)+1))
for i in range(len(ROWS)+1): ax.plot([X0,X0+W],[yb+rh*i,yb+rh*i],color="k",lw=TN)
ax.plot([X0,X0+W],[yb+rh,yb+rh],color="k",lw=TH)
for c in COLS[1:-1]: ax.plot([X0+c,X0+c],[yb,yb+rh*(len(ROWS)+1)],color="k",lw=TN)
for c,h in zip(COLS,HDR): text(X0+c+0.8, yb+1.0, h, 2.0)
for i,row in enumerate(ROWS):
    y = yb+rh*(i+1)+0.9
    for c,v in zip(COLS,row): text(X0+c+1, y, v, 2.4)

text(25, 19, "Hinweis: Stand Pos. 1 bis 8. Die Normteile Pos. 9 bis 12 (Zylinderstifte, Zylinderschrauben,", 2.5)
text(25, 14, "Rillenkugellager, Filzring) sind noch nicht eingebaut.", 2.5)

fig.savefig("Gesamtzeichnung_Fliehkraftkupplung_Pos1-8.pdf")
fig.savefig("preview.png", dpi=110)
fig.savefig("preview_hi.png", dpi=300)
print("ok")
