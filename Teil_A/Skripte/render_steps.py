"""Rendert die Montageschritte der Fliehkraftkupplung (VTK, offscreen)."""
import vtk, cadquery as cq, pickle, sys
import build2

parts = build2.build_all()
by = {}
for p, n, s in parts: by.setdefault(p, []).append((n, s))

# Montagefolge: (Titel, neue Positionen, Liste aller sichtbaren Positionen, Viertelschnitt?)
HUB = ["1", "6", "5.1", "5.2", "9", "8", "7", "11"]
STEPS = [
    ("Antriebsnabe (1) bereitlegen", ["1"], ["1"], False),
    ("Scheiben (6) beidseitig an die Nabenarme", ["6"], ["1", "6"], False),
    ("Fliehgewichte (5.1 + Belag 5.2) über die Arme schieben", ["5.1", "5.2"], ["1", "6", "5.1", "5.2"], False),
    ("Zylinderstifte (9) einstecken", ["9"], ["1", "6", "5.1", "5.2", "9"], False),
    ("Sicherungsscheiben (8) in die Stiftnuten", ["8"], ["1", "6", "5.1", "5.2", "9", "8"], False),
    ("Zugfedern (7) in die Einstiche einhängen", ["7"], ["1", "6", "5.1", "5.2", "9", "8", "7"], False),
    ("Rillenkugellager (11) auf die Lagersitze Ø45k6 pressen", ["11"], HUB, False),
    ("Gehäuse (3) auf die Abtriebsnabe (2) zentrieren und verschrauben (10)", ["2", "3", "10b"], ["2", "3", "10b"], True),
    ("Vormontierte Antriebsnabe in den Lagersitz Ø75H7 schieben", HUB, HUB + ["2", "3", "10b"], True),
    ("Filzring (12) in die Nut des Deckels (4) einlegen", ["12"], ["4", "12"], True),
    ("Deckel aufsetzen und verschrauben (10) – fertig", ["4", "10a"], HUB + ["2", "3", "4", "12", "10a", "10b"], True),
    ("Fertige Fliehkraftkupplung", [], HUB + ["2", "3", "4", "12", "10a", "10b"], False),
]
# Schrauben aufteilen: Deckelseite (X<40) / Abtriebsseite
by["10a"] = [(n, s) for n, s in by["10"] if s.Center().x < 40]
by["10b"] = [(n, s) for n, s in by["10"] if s.Center().x > 40]

CUT = cq.Solid.makeBox(300, 200, 200, cq.Vector(-50, -200, 0))     # Viertel y<0, z>0 entfernen
CUT_POS = {"2", "3", "4", "12", "10a", "10b", "11"}

_cache = {}
def poly(pos, name, shape, cut):
    key = (name, cut)
    if key not in _cache:
        s = shape.cut(CUT) if cut else shape
        _cache[key] = s.toVtkPolyData(0.05, 0.15, normals=True)
    return _cache[key]

def render(idx, title, new, visible, cut, fname, cam=None, size=(1600, 1100)):
    ren = vtk.vtkRenderer(); ren.SetBackground(1, 1, 1)
    rw = vtk.vtkRenderWindow(); rw.SetOffScreenRendering(1); rw.SetSize(*size); rw.AddRenderer(ren)
    rw.SetMultiSamples(8)
    for pos in visible:
        for name, shape in by[pos]:
            pd = poly(pos, name, shape, cut and pos in CUT_POS)
            m = vtk.vtkPolyDataMapper(); m.SetInputData(pd)
            a = vtk.vtkActor(); a.SetMapper(m)
            pr = a.GetProperty()
            if pos in new:
                col = (0.93, 0.45, 0.10) if pos not in ("5.2", "12") else ((0.95, 0.78, 0.15) if pos == "12" else (0.55, 0.30, 0.15))
                if pos in ("10a", "10b", "8", "9"): col = (0.15, 0.40, 0.85)
                if pos == "11": col = (0.20, 0.60, 0.35)
                if pos == "7": col = (0.85, 0.15, 0.15)
            else:
                col = (0.80, 0.80, 0.82) if pos not in ("5.2", "12") else (0.62, 0.58, 0.55)
            pr.SetColor(*col); pr.SetSpecular(0.25); pr.SetSpecularPower(25); pr.SetAmbient(0.25); pr.SetDiffuse(0.75)
            ren.AddActor(a)
            fe = vtk.vtkFeatureEdges(); fe.SetInputData(pd); fe.BoundaryEdgesOn(); fe.FeatureEdgesOn()
            fe.SetFeatureAngle(35); fe.ManifoldEdgesOff(); fe.NonManifoldEdgesOff(); fe.ColoringOff()
            em = vtk.vtkPolyDataMapper(); em.SetInputConnection(fe.GetOutputPort())
            ea = vtk.vtkActor(); ea.SetMapper(em); ea.GetProperty().SetColor(0.15, 0.15, 0.15); ea.GetProperty().SetLineWidth(1.2)
            ren.AddActor(ea)
    cam_ = ren.GetActiveCamera()
    fp = (47, 0, 0) if not any(p in visible for p in ("2", "3", "4")) else ((10, 0, 0) if visible == ["4", "12"] else (65, 0, 0))
    d = cam or (-1.0, -1.25, 0.9)
    dist = 330 if fp[0] == 47 else (300 if fp[0] == 10 else 470)
    n = (d[0]**2 + d[1]**2 + d[2]**2) ** 0.5
    cam_.SetFocalPoint(*fp); cam_.SetPosition(fp[0] + d[0]/n*dist, fp[1] + d[1]/n*dist, fp[2] + d[2]/n*dist)
    cam_.SetViewUp(0, 0, 1); cam_.SetViewAngle(30)
    light = vtk.vtkLight(); light.SetLightTypeToCameraLight(); light.SetPosition(0.3, 0.6, 1); ren.AddLight(light)
    rw.Render()
    w = vtk.vtkWindowToImageFilter(); w.SetInput(rw); w.Update()
    p = vtk.vtkPNGWriter(); p.SetFileName(fname); p.SetInputConnection(w.GetOutputPort()); p.Write()

if __name__ == "__main__":
    only = [int(a) for a in sys.argv[1:]]
    for i, (title, new, visible, cut) in enumerate(STEPS, 1):
        if only and i not in only: continue
        cam = (1.0, -1.25, 0.9) if i == 10 else None
        render(i, title, new, visible, cut, f"steps/schritt_{i:02d}.png", cam=cam)
        print("Schritt", i, "ok", flush=True)
