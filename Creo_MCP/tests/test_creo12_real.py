"""Abweichungen echtes Creo 12.4.5.0 (deutsche Oberfläche) ↔ simulierter CREOSON.

Die Antworten unten sind am 24.11.2026 mit CREOSON 3.0.2 an einem echten Creo 12.4.5.0 aufgezeichnet
(Teile aus der HTL-Vorlage). Gefunden wurden:
- KE-Typen kommen auf Deutsch (BEZUGSEBENE, MUSTER, KOMPONENTE, KÖRPER = Körper/Protrusion …).
- KEs ohne eigenen Namen haben name "" – auch der Musterkopf. list_pattern_features braucht aber einen Namen.
- Der Musterkopf steht vor dem Leit-KE; die Kopien haben die IDs direkt nach dem Musterkopf.
- Komponenten im Stücklistenbaum (bom.get_paths) heißen in Großbuchstaben ("ANTRIEBSNABE.PRT").
- file.open/get_active melden das Verzeichnis als "C:C:/…".
"""

from __future__ import annotations

from typing import Any

import pytest

from creo_mcp.errors import CreoMCPError
from creo_mcp.feattypes import canonical_type, head_kind, is_component, is_datum, same_type
from creo_mcp.tree import build_model_tree, render_tree_markdown


def _f(number: int, feat_id: int, type_: str, name: str = "") -> dict[str, Any]:
    return {"status": "ACTIVE", "feat_number": number, "name": name, "type": type_, "feat_id": feat_id}


# feature.list (inc_unnamed, paths) von abtriebsnaben.prt – unverändert aus Creo 12.4.5.0
NABE = [
    _f(1, 1, "KOORDINATENSYSTEM", "BASIS"),
    _f(2, 4, "BEZUGSEBENE", "RECHTS"),
    _f(3, 7, "BEZUGSEBENE", "OBEN"),
    _f(4, 9, "BEZUGSEBENE", "VORNE"),
    _f(5, 142, "BEZUGSACHSE", "A_X"),
    _f(6, 146, "BEZUGSACHSE", "A_Y"),
    _f(7, 150, "BEZUGSACHSE", "A_Z"),
    _f(8, 154, "KÖRPER"),
    _f(9, 383, "KURVE"),
    _f(10, 396, "MATERIALSCHNITT"),
    _f(11, 569, "MUSTER"),
    _f(12, 496, "BOHRUNG"),
    *[_f(13 + i, 570 + i, "BOHRUNG") for i in range(5)],
]
# feature.list_pattern_features, nachdem der Musterkopf in der Sitzung "MUSTER_TEST" hieß
PATTERN_MEMBERS = [{k: v for k, v in f.items() if k != "name"} for f in NABE[11:]]

ASM = [
    _f(1, 1, "KOORDINATENSYSTEM", "BG-BASIS"),
    _f(2, 4, "BEZUGSEBENE", "BG-RECHTS"),
    _f(3, 7, "BEZUGSEBENE", "BG-OBEN"),
    _f(4, 9, "BEZUGSEBENE", "BG-VORNE"),
    _f(5, 35, "BEZUGSACHSE", "A_X"),
    _f(6, 39, "BEZUGSACHSE", "A_Y"),
    _f(7, 43, "BEZUGSACHSE", "A_Z"),
    _f(8, 47, "KOMPONENTE", "ANTRIEBSNABE.prt"),
]
BOM = {
    "children": {
        "children": [{"file": "ANTRIEBSNABE.PRT", "seq_path": "root.1", "path": [47]}],
        "file": "fliehkraftjupplung.asm",
        "seq_path": "root",
    },
    "generic": "",
    "file": "fliehkraftjupplung.asm",
}


def recorded(features: dict[str, list[dict[str, Any]]], patterns: dict[str, list[dict[str, Any]]] | None = None):
    """Nachbau von CREOSON mit den aufgezeichneten Antworten (Dateinamen ohne Groß-/Kleinschreibung)."""
    patterns = patterns or {}
    calls: list[tuple[str, str, dict[str, Any]]] = []

    async def call(command: str, function: str, data: dict[str, Any] | None) -> dict[str, Any]:
        data = data or {}
        calls.append((command, function, data))
        file = str(data.get("file", "")).lower()
        if (command, function) == ("feature", "list"):
            return {"featlist": features[file]}
        if (command, function) == ("feature", "list_pattern_features"):
            name = data.get("pattern_name")
            if name not in patterns:
                raise CreoMCPError(f"feature.list_pattern_features: Feature '{name}' not found")
            return {"featlist": patterns[name]}
        if (command, function) == ("bom", "get_paths"):
            return BOM
        raise AssertionError(f"unerwarteter Aufruf {command}.{function}")

    call.calls = calls  # type: ignore[attr-defined]
    return call


def _top(result):
    return result.root.children


# -- Typnamen -------------------------------------------------------------------

@pytest.mark.parametrize(
    ("creo", "english"),
    [
        ("BEZUGSEBENE", "DATUM PLANE"),
        ("Bezugsachse", "DATUM AXIS"),
        ("KOORDINATENSYSTEM", "COORDINATE SYSTEM"),
        ("KÖRPER", "PROTRUSION"),
        ("MATERIALSCHNITT", "CUT"),
        ("BOHRUNG", "HOLE"),
        ("RUNDUNG", "ROUND"),
        ("FASE", "CHAMFER"),
        ("MUSTER", "PATTERN"),
        ("PATTERN HEAD", "PATTERN"),
        ("GRUPPENKOPF", "GROUP"),
        ("KOMPONENTE", "COMPONENT"),
        ("DATUM_PLANE", "DATUM PLANE"),
        ("UNBEKANNT", "UNBEKANNT"),
    ],
)
def test_canonical_type_maps_german_creo_names(creo, english):
    assert canonical_type(creo) == english


def test_type_helpers_work_for_both_languages():
    assert is_datum("BEZUGSEBENE") and is_datum("DATUM PLANE") and is_datum("KURVE")
    assert not is_datum("KÖRPER")  # Körper = Drehen/Extrudieren, kein Bezug
    assert is_component("KOMPONENTE") and is_component("COMPONENT")
    assert head_kind("MUSTER") == "pattern" and head_kind("PATTERN HEAD") == "pattern"
    assert head_kind("GRUPPENKOPF") == "group" and head_kind("GROUP HEAD") == "group"
    assert head_kind("BOHRUNG") is None
    assert same_type("HOLE", "Bohrung") and not same_type("HOLE", "CUT")


# -- Modellbaum mit echten Daten ---------------------------------------------------

async def test_german_datums_are_hidden_but_koerper_stays():
    result = await build_model_tree(recorded({"abtriebsnaben.prt": NABE}), "abtriebsnaben.prt", include_datums=False)
    types = [n.type for n in _top(result)]
    assert "BEZUGSEBENE" not in types and "BEZUGSACHSE" not in types and "KOORDINATENSYSTEM" not in types
    assert "KURVE" not in types  # Skizze
    assert types[0] == "KÖRPER" and "MATERIALSCHNITT" in types


async def test_unnamed_german_pattern_members_are_found_by_feature_ids():
    result = await build_model_tree(recorded({"abtriebsnaben.prt": NABE}), "abtriebsnaben.prt", include_datums=False)
    pattern = next(n for n in _top(result) if n.kind == "pattern")
    assert pattern.feat_id == 569 and pattern.type == "MUSTER"
    assert [c.feat_id for c in pattern.children] == [496, 570, 571, 572, 573, 574]
    assert not any(n.type == "BOHRUNG" for n in _top(result))  # keine Bohrung mehr lose oben
    text = render_tree_markdown(result)
    assert "▦ (ohne Namen)  [MUSTER]" in text
    assert "Feature-IDs" in text  # Hinweis, wie die Mitglieder bestimmt wurden


async def test_named_german_pattern_uses_creoson_member_list():
    feats = [dict(f) for f in NABE]
    feats[10]["name"] = "MUSTER_TEST"
    call = recorded({"abtriebsnaben.prt": feats}, {"MUSTER_TEST": PATTERN_MEMBERS})
    result = await build_model_tree(call, "abtriebsnaben.prt", include_datums=False)
    pattern = next(n for n in _top(result) if n.kind == "pattern")
    assert pattern.name == "MUSTER_TEST" and len(pattern.children) == 6
    assert ("feature", "list_pattern_features", {"file": "abtriebsnaben.prt", "pattern_name": "MUSTER_TEST"}) in call.calls
    assert not result.warnings


async def test_pattern_id_fallback_stops_at_gap_and_needs_two_members():
    feats = [_f(1, 50, "MUSTER"), _f(2, 40, "BOHRUNG"), _f(3, 70, "BOHRUNG")]  # 70 ≠ 51: keine Kopie
    result = await build_model_tree(recorded({"teil.prt": feats}), "teil.prt")
    assert not any(n.kind == "pattern" for n in _top(result))
    assert any("flach" in w for w in result.warnings)


async def test_german_assembly_component_is_recognised_and_expanded():
    call = recorded({"fliehkraftjupplung.asm": ASM, "antriebsnabe.prt": NABE})
    result = await build_model_tree(call, "fliehkraftjupplung.asm", include_datums=False)
    comp = next(n for n in _top(result) if n.type == "KOMPONENTE")
    assert comp.kind == "component" and comp.feat_id == 47
    assert comp.file.lower() == "antriebsnabe.prt"
    assert any(c.type == "KÖRPER" for c in comp.children)
    assert "▣ ANTRIEBSNABE.prt" in render_tree_markdown(result)
