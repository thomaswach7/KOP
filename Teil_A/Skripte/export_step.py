"""Exportiert die komplette Baugruppe (CAD/Baugruppe_Fliehkraftkupplung_komplett.step) und das Lager Pos. 11
(CAD/Einzelteile_neu/... und CAD/Einzelteile_alle/...) aus build2.py. Aufruf im Ordner Skripte (Datensatz unter ../Fliehkraftkupplung)."""
import sys, cadquery as cq
import build2
ziel = sys.argv[1] if len(sys.argv) > 1 else "../CAD"
FARBE = {"7": (1.0, 0.843, 0.0), "11": (0.0, 0.392, 0.0)}
asm = cq.Assembly(name="Fliehkraftkupplung")
for pos, name, s in build2.build_all():
    form = cq.Compound.makeCompound(list(s)) if isinstance(s, list) else s
    asm.add(form, name=f"Pos{pos}_{name}", color=cq.Color(*FARBE.get(pos, (0.827, 0.827, 0.827))))
asm.save(f"{ziel}/Baugruppe_Fliehkraftkupplung_komplett.step")
lager = cq.Compound.makeCompound(build2.lager_lokal())
for pfad in (f"{ziel}/Einzelteile_neu/Pos11_Rillenkugellager_6009-2Z_vereinfacht.step", f"{ziel}/Einzelteile_alle/Pos11_Rillenkugellager_6009-2Z.stp"):
    cq.exporters.export(lager, pfad, "STEP")
print("ok")
