import vtk, render_steps as rs
def render_detail(new, visible, fname, fp, d, dist, size=(900, 700)):
    ren = vtk.vtkRenderer(); ren.SetBackground(1, 1, 1)
    rw = vtk.vtkRenderWindow(); rw.SetOffScreenRendering(1); rw.SetSize(*size); rw.AddRenderer(ren); rw.SetMultiSamples(8)
    for pos in visible:
        for name, shape in rs.by[pos]:
            pd = rs.poly(pos, name, shape, False)
            m = vtk.vtkPolyDataMapper(); m.SetInputData(pd); a = vtk.vtkActor(); a.SetMapper(m); pr = a.GetProperty()
            if pos in new:
                col = {"6": (0.93, 0.45, 0.10), "9": (0.15, 0.40, 0.85), "8": (0.15, 0.40, 0.85), "7": (0.85, 0.15, 0.15)}.get(pos, (0.93, 0.45, 0.10))
            else:
                col = (0.80, 0.80, 0.82) if pos != "5.2" else (0.62, 0.58, 0.55)
            pr.SetColor(*col); pr.SetSpecular(0.25); pr.SetSpecularPower(25); pr.SetAmbient(0.25)
            ren.AddActor(a)
            fe = vtk.vtkFeatureEdges(); fe.SetInputData(pd); fe.BoundaryEdgesOn(); fe.FeatureEdgesOn(); fe.SetFeatureAngle(35)
            fe.ManifoldEdgesOff(); fe.NonManifoldEdgesOff(); fe.ColoringOff()
            em = vtk.vtkPolyDataMapper(); em.SetInputConnection(fe.GetOutputPort()); ea = vtk.vtkActor(); ea.SetMapper(em)
            ea.GetProperty().SetColor(0.15, 0.15, 0.15); ea.GetProperty().SetLineWidth(1.2); ren.AddActor(ea)
    c = ren.GetActiveCamera(); n = sum(x*x for x in d) ** 0.5
    c.SetFocalPoint(*fp); c.SetPosition(*(fp[i] + d[i]/n*dist for i in range(3))); c.SetViewUp(0, 0, 1); c.SetViewAngle(30)
    rw.Render(); w = vtk.vtkWindowToImageFilter(); w.SetInput(rw); w.Update()
    p = vtk.vtkPNGWriter(); p.SetFileName(fname); p.SetInputConnection(w.GetOutputPort()); p.Write()

if __name__ == "__main__":
    fp = (40, 10, 52); d = (-1.0, -0.9, 0.8)
    for i in (2, 3, 4, 5, 6):
        title, new, visible, cut = rs.STEPS[i-1]
        render_detail(new, visible, f"steps/schritt_{i:02d}_detail.png", fp, d, 120)
        print("Detail", i, flush=True)
