"""Zustand einer simulierten Creo-Sitzung für Tests und den Demo-Modus.

Die Demo-Daten bilden die Fliehkraftkupplung aus diesem Repo nach (Teil A/D):
Baugruppe mit Unterbaugruppe "Fliehgewicht" und der Abtriebsnabe (Pos. 2) mit KEs,
einer Gruppe und einem Muster. Werte (z. B. Volumen 350.370 mm³) stammen aus den Anleitungen.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from ..feattypes import DATUM_TYPES

WORK_DIR = "C:/Creo_MCP/arbeit"
TEMPLATE_DIR = "C:/Program Files/PTC/Creo 12.4.4.0/Common Files/templates"
FORMAT_DIR = "C:/PTC/admCreo12HTL/bibliothek/zeichnungsrahmen"  # Zeichnungsrahmen (.frm) des HTL-Pakets

STANDARD_VIEWS = ["BACK", "BOTTOM", "DEFAULT", "FRONT", "LEFT", "RIGHT", "TOP"]
# Gespeicherte Ansichten in Teilen aus der HTL-Vorlage (so von Creo 12 gemeldet)
HTL_VIEWS = ["DEFAULT", "GOODVIEW", "HINTEN - REAR", "LINKS - LEFT", "OBEN - TOP", "RECHTS - RIGHT", "UNTEN - BOTTOM", "VORNE - FRONT"]

__all__ = ["DATUM_TYPES", "FORMAT_DIR", "HTL_VIEWS", "STANDARD_VIEWS", "MDrawing", "MFeature", "MModel", "MView", "MockCreo", "norm_dir"]


def norm_dir(dirname: str) -> str:
    return dirname.replace("\\", "/").rstrip("/").lower()


@dataclass
class MFeature:
    feat_id: int
    name: str | None
    type: str
    status: str = "ACTIVE"
    component: str | None = None  # Dateiname bei COMPONENT-KEs
    group: str | None = None  # Name des Gruppenkopfs, zu dem das KE gehört
    pattern: str | None = None  # Name des Musterkopfs, zu dem das KE gehört
    params: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class MModel:
    file: str
    features: list[MFeature] = field(default_factory=list)
    params: dict[str, dict[str, Any]] = field(default_factory=dict)
    dims: dict[str, dict[str, Any]] = field(default_factory=dict)
    relations: list[str] = field(default_factory=list)
    volume: float = 0.0
    surface_area: float = 0.0
    density: float = 7.1e-6  # kg/mm³ (Gusseisen)
    material: str | None = None
    materials: list[str] = field(default_factory=list)
    length_units: str = "mm"
    mass_units: str = "kg"
    bbox: tuple[float, float, float, float, float, float] = (0, 0, 0, 0, 0, 0)
    views: list[str] = field(default_factory=lambda: list(STANDARD_VIEWS))
    dirname: str = WORK_DIR
    revision: int = 1
    modified: bool = False

    @property
    def is_assembly(self) -> bool:
        return self.file.endswith(".asm")

    def feature_by_id(self, feat_id: int) -> MFeature | None:
        return next((f for f in self.features if f.feat_id == feat_id), None)


@dataclass
class MView:
    name: str
    sheet: int
    model: str
    x: float
    y: float
    scale: float
    parent: str | None = None


@dataclass
class MDrawing:
    file: str
    models: list[str]
    sheets: int = 1
    cur_sheet: int = 1
    sheet_scale: dict[int, float] = field(default_factory=lambda: {1: 1.0})
    sheet_format: dict[int, str] = field(default_factory=dict)
    views: dict[str, MView] = field(default_factory=dict)
    broken: bool = False  # Vorlage konnte nicht angewendet werden (Creo: "Dwg Create Errors")
    dirname: str = WORK_DIR


class MockCreo:
    """Simulierte Creo-Sitzung + Dateisystem."""

    def __init__(self) -> None:
        self.sessions: set[str] = set()
        self.creo_versions: dict[str, int] = {}
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.working_dir = WORK_DIR
        self.disk: dict[str, dict[str, MModel | MDrawing]] = {}
        self.other_files: dict[str, set[str]] = {}
        self.formats_in_session: set[str] = set()  # geladene Blattformate (.frm), klein geschrieben
        self.session: dict[str, MModel | MDrawing] = {}
        self.active: str | None = None
        self.displayed: set[str] = set()
        self.mapkeys: list[str] = []
        self.exports: list[dict[str, Any]] = []
        self.selected: list[tuple[str, int]] = []
        self.config: dict[str, str] = {}
        self.creo_running = True
        self.double_drive_quirk = False  # echtes CREOSON meldet Verzeichnisse als "C:C:/…"
        self.fail_functions: dict[tuple[str, str], str] = {}
        self._next_id = 1000

    # -- Hilfen -------------------------------------------------------------
    def new_id(self) -> int:
        self._next_id += 1
        return self._next_id

    def put_on_disk(self, model: MModel | MDrawing, dirname: str | None = None) -> None:
        d = norm_dir(dirname or model.dirname)
        model.dirname = dirname or model.dirname
        self.disk.setdefault(d, {})[model.file.lower()] = copy.deepcopy(model)

    def from_disk(self, file: str, dirname: str | None = None) -> MModel | MDrawing | None:
        d = norm_dir(dirname or self.working_dir)
        m = self.disk.get(d, {}).get(file.lower())
        return copy.deepcopy(m) if m is not None else None

    def files_in_dir(self, dirname: str | None = None) -> list[str]:
        d = norm_dir(dirname or self.working_dir)
        names = set(self.disk.get(d, {})) | self.other_files.get(d, set())
        return sorted(names)

    # -- Demo-Daten -----------------------------------------------------------
    @classmethod
    def demo(cls) -> MockCreo:
        st = cls()
        for model in _demo_models():
            st.put_on_disk(model)
        for tpl in _template_models():
            st.put_on_disk(tpl, TEMPLATE_DIR)
        st.other_files[norm_dir(WORK_DIR)] = {"anleitung_abtriebsnabe.pdf", "config.pro"}
        st.other_files[norm_dir(FORMAT_DIR)] = {"a3_fertigung.frm", "a4_fertigung.frm"}
        return st


def _datums(prefix: str = "", start_id: int = 1) -> list[MFeature]:
    names = ["RIGHT", "TOP", "FRONT"]
    feats = [MFeature(start_id + 2 * i, f"{prefix}{n}", "DATUM PLANE") for i, n in enumerate(names)]
    csys = "ASM_DEF_CSYS" if prefix else "PRT_CSYS_DEF"
    feats.append(MFeature(start_id + 6, csys, "COORDINATE SYSTEM"))
    return feats


def _part(file: str, volume: float, body: list[MFeature], **kw: Any) -> MModel:
    m = MModel(file=file, features=_datums() + body, volume=volume, **kw)
    return m


def _demo_models() -> list[MModel]:
    abtrieb = _part(
        "abtriebsnabe.prt",
        350370.0,
        [
            MFeature(39, None, "DATUM AXIS"),
            MFeature(40, "Grundkörper", "PROTRUSION"),
            MFeature(60, "Passfedernut", "CUT"),
            MFeature(70, "Muster_Bohrungen", "PATTERN HEAD"),
            MFeature(71, "Bohrung_Stirnsenker", "HOLE", pattern="Muster_Bohrungen"),
            MFeature(72, "Bohrung_Stirnsenker", "HOLE", pattern="Muster_Bohrungen"),
            MFeature(73, "Bohrung_Stirnsenker", "HOLE", pattern="Muster_Bohrungen"),
            MFeature(74, "Bohrung_Stirnsenker", "HOLE", pattern="Muster_Bohrungen"),
            MFeature(80, "Fasen", "GROUP HEAD"),
            MFeature(81, "Fase_Bund", "CHAMFER", group="Fasen"),
            MFeature(82, "Fase_Bohrung", "CHAMFER", group="Fasen"),
            MFeature(90, "Freistich_DIN509", "CUT"),
        ],
        surface_area=61234.5,
        material="EN-GJS-700-2",
        materials=["EN-GJS-700-2"],
        bbox=(0.0, 72.0, -82.0, 82.0, -82.0, 82.0),
        dims={
            "d0": {"value": 72.0, "feat_id": 40},
            "d1": {"value": 164.0, "feat_id": 40},
            "d2": {"value": 75.0, "feat_id": 40},
            "d3": {"value": 14.0, "feat_id": 60},
            "d4": {"value": 3.8, "feat_id": 60},
            "d5": {"value": 9.0, "feat_id": 71},
            "d6": {"value": 4.0, "feat_id": 70},
        },
        params={
            "BENENNUNG": {"type": "STRING", "value": "Abtriebsnabe", "designate": True, "description": "Benennung"},
            "POSITION": {"type": "INTEGER", "value": 2, "designate": True, "description": "Positionsnummer"},
            "WERKSTOFF": {"type": "STRING", "value": "EN-GJS-700-2", "designate": True, "description": ""},
        },
        relations=["/* Lochkreis", "d6 = 4"],
    )
    deckel = _part("deckel.prt", 276284.0, [MFeature(40, "Grundkörper", "PROTRUSION")], material="EN-GJS-700-2")
    gehaeuse = _part("gehaeuse.prt", 559933.0, [MFeature(40, "Grundkörper", "PROTRUSION")], material="E295")
    antrieb = _part("antriebsnabe.prt", 180714.0, [MFeature(40, "Grundkörper", "PROTRUSION")])
    gewicht = _part("gewicht.prt", 82713.0, [MFeature(40, "Grundkörper", "PROTRUSION")])
    belag = _part("belag.prt", 16096.0, [MFeature(40, "Belag", "PROTRUSION")])
    scheibe = _part("scheibe.prt", 206.0, [MFeature(40, "Scheibe", "PROTRUSION")], material="S235JR")

    flieh = MModel(
        file="fliehgewicht.asm",
        features=_datums("ASM_")
        + [MFeature(30, "gewicht.prt", "COMPONENT", component="gewicht.prt"), MFeature(31, "belag.prt", "COMPONENT", component="belag.prt")],
    )
    top = MModel(
        file="fliehkraftkupplung.asm",
        features=_datums("ASM_")
        + [
            MFeature(41, "deckel.prt", "COMPONENT", component="deckel.prt"),
            MFeature(42, "gehaeuse.prt", "COMPONENT", component="gehaeuse.prt"),
            MFeature(43, "abtriebsnabe.prt", "COMPONENT", component="abtriebsnabe.prt"),
            MFeature(44, "antriebsnabe.prt", "COMPONENT", component="antriebsnabe.prt"),
            MFeature(45, "fliehgewicht.asm", "COMPONENT", component="fliehgewicht.asm"),
            MFeature(46, "fliehgewicht.asm", "COMPONENT", component="fliehgewicht.asm"),
            MFeature(47, "scheibe.prt", "COMPONENT", component="scheibe.prt"),
            MFeature(48, "scheibe.prt", "COMPONENT", component="scheibe.prt"),
        ],
        params={"BENENNUNG": {"type": "STRING", "value": "Fliehkraftkupplung", "designate": True, "description": ""}},
    )
    return [abtrieb, _htl_part(), _htl_deckel(), deckel, gehaeuse, antrieb, gewicht, belag, scheibe, flieh, top]


def _htl_part() -> MModel:
    """Abtriebsnabe wie aus deutschem Creo 12 mit HTL-Vorlage: deutsche Typen, KEs ohne Namen, Muster ohne Namen
    (Kopf vor dem Leit-KE, Kopien mit den IDs nach dem Kopf), Ansichten "VORNE - FRONT" usw."""
    datums = [
        MFeature(1, "BASIS", "KOORDINATENSYSTEM"),
        MFeature(4, "RECHTS", "BEZUGSEBENE"),
        MFeature(7, "OBEN", "BEZUGSEBENE"),
        MFeature(9, "VORNE", "BEZUGSEBENE"),
        MFeature(142, "A_X", "BEZUGSACHSE"),
        MFeature(146, "A_Y", "BEZUGSACHSE"),
        MFeature(150, "A_Z", "BEZUGSACHSE"),
    ]
    body = [
        MFeature(154, None, "KÖRPER"),
        MFeature(383, None, "KURVE"),
        MFeature(396, None, "MATERIALSCHNITT"),
        MFeature(569, None, "MUSTER"),
        MFeature(496, None, "BOHRUNG", pattern="#569"),
        *[MFeature(570 + i, None, "BOHRUNG", pattern="#569") for i in range(5)],
    ]
    return MModel(file="abtriebsnabe_htl.prt", features=datums + body, volume=350370.0, views=list(HTL_VIEWS))


def _htl_deckel() -> MModel:
    """Deckel Pos. 4 wie am 27.11.2026 im echten Creo 12 gebaut: Kontur als DXF importiert ("KURVE AUS DATEI"),
    Drehen um A_X, Senkbohrung im Muster 6 × 60°, Querschnitt A für den Zeichnungsschnitt (Typ "Querschnitt")."""
    datums = [
        MFeature(1, "BASIS", "KOORDINATENSYSTEM"),
        MFeature(4, "RECHTS", "BEZUGSEBENE"),
        MFeature(7, "OBEN", "BEZUGSEBENE"),
        MFeature(9, "VORNE", "BEZUGSEBENE"),
        MFeature(142, "A_X", "BEZUGSACHSE"),
        MFeature(146, "A_Y", "BEZUGSACHSE"),
        MFeature(150, "A_Z", "BEZUGSACHSE"),
    ]
    body = [
        MFeature(789, "KONTUR_DXF", "KURVE AUS DATEI"),
        MFeature(820, "GRUNDKOERPER", "KÖRPER"),
        MFeature(1126, "LOCHKREIS_6X60", "MUSTER"),
        MFeature(1055, "SENKBOHRUNG", "BOHRUNG", pattern="LOCHKREIS_6X60"),
        *[MFeature(1127 + i, None, "BOHRUNG", pattern="LOCHKREIS_6X60") for i in range(5)],
        MFeature(1613, "A", "Querschnitt"),
    ]
    return MModel(file="deckel_htl.prt", features=datums + body, volume=276253.6, views=list(HTL_VIEWS))


def _template_models() -> list[MModel]:
    part = MModel(
        file="mmns_part_solid_abs.prt",
        features=_datums(),
        params={
            "DESCRIPTION": {"type": "STRING", "value": "", "designate": True, "description": ""},
            "MODELED_BY": {"type": "STRING", "value": "", "designate": True, "description": ""},
        },
        dirname=TEMPLATE_DIR,
    )
    asm = MModel(file="mmns_asm_design_abs.asm", features=_datums("ASM_"), dirname=TEMPLATE_DIR)
    return [part, asm]
