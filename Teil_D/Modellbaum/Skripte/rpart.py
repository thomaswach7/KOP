import vtk, sys
def render_shapes(shapes, fname, d=(-1,-1.2,0.9), fp=None, dist=None, size=(900,700), up=(0,0,1)):
    ren = vtk.vtkRenderer(); ren.SetBackground(1,1,1)
    rw = vtk.vtkRenderWindow(); rw.SetOffScreenRendering(1); rw.SetSize(*size); rw.AddRenderer(ren); rw.SetMultiSamples(8)
    bbs = []
    for s, col in shapes:
        pd = s.toVtkPolyData(0.03, 0.1, normals=True); bbs.append(s.BoundingBox())
        m = vtk.vtkPolyDataMapper(); m.SetInputData(pd); a = vtk.vtkActor(); a.SetMapper(m)
        a.GetProperty().SetColor(*col); a.GetProperty().SetSpecular(0.2); a.GetProperty().SetAmbient(0.25); ren.AddActor(a)
        fe = vtk.vtkFeatureEdges(); fe.SetInputData(pd); fe.BoundaryEdgesOn(); fe.FeatureEdgesOn(); fe.SetFeatureAngle(30)
        fe.ManifoldEdgesOff(); fe.NonManifoldEdgesOff(); fe.ColoringOff()
        em = vtk.vtkPolyDataMapper(); em.SetInputConnection(fe.GetOutputPort()); ea = vtk.vtkActor(); ea.SetMapper(em)
        ea.GetProperty().SetColor(0.1,0.1,0.1); ea.GetProperty().SetLineWidth(1.0); ren.AddActor(ea)
    if fp is None:
        fp = ((min(b.xmin for b in bbs)+max(b.xmax for b in bbs))/2, (min(b.ymin for b in bbs)+max(b.ymax for b in bbs))/2, (min(b.zmin for b in bbs)+max(b.zmax for b in bbs))/2)
    if dist is None:
        dist = 3.2*max(max(b.xlen for b in bbs), max(b.ylen for b in bbs), max(b.zlen for b in bbs))
    c = ren.GetActiveCamera(); n = sum(x*x for x in d)**0.5
    c.SetFocalPoint(*fp); c.SetPosition(*(fp[i]+d[i]/n*dist for i in range(3))); c.SetViewUp(*up); c.SetViewAngle(25)
    rw.Render(); w = vtk.vtkWindowToImageFilter(); w.SetInput(rw); w.Update()
    p = vtk.vtkPNGWriter(); p.SetFileName(fname); p.SetInputConnection(w.GetOutputPort()); p.Write()
