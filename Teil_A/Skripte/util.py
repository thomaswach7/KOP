import cadquery as cq, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D='../Fliehkraftkupplung/'
F={1:'14.2.2.1_Modell_Antriebsnabe_V1_Pos_01.stp',2:'14.2.2.2_Modell_Abtriebsnabe_V1_Pos_02.stp',4:'14.2.2.3_Modell_Deckel_Pos_04.stp',5:'14.2.2.4_Modell_Fliehgewicht_Pos5.stp',7:'14.2.2.5_Modell_Feder_ungespannt_Pos_07.stp'}
def load(p): return cq.importers.importStep(D+F[p]).val()
def section(shape, normal=(0,0,1), origin=(0,0,0)):
    f=cq.Face.makePlane(1000,1000,basePnt=origin,dir=normal)
    return shape.intersect(f)
def pts(edge,n=60):
    return [edge.positionAt(i/n) for i in range(n+1)]
def plot_edges(ax, edges, ij=(0,1), **kw):
    for e in edges:
        p=pts(e)
        ax.plot([q.toTuple()[ij[0]] for q in p],[q.toTuple()[ij[1]] for q in p],**kw)
