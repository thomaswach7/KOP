"""Werkzeuge gegen ein Teil wie aus deutschem Creo 12 mit HTL-Vorlage (abtriebsnabe_htl.prt im Simulator).

Nachgestellt nach Tests am echten Creo 12.4.5.0 (24.11.2026):
- Die Vorlage a3_drawing braucht die Modellansichten FRONT, TOP und RIGHT. HTL-Teile heißen sie "VORNE - FRONT" usw.
  Ohne sie meldet Creo "Dwg Create Errors" und lässt eine halbe Zeichnung zurück ("Bad Inputs" bei jeder Ansicht).
- view.activate/view.save gehen nur im aktiven Fenster.
- Verzeichnisse kommen als "C:C:/…" zurück.
"""

import pytest
from mcp import Client

from creo_mcp.client import CreosonClient
from creo_mcp.config import Settings
from creo_mcp.mock.state import TEMPLATE_DIR
from creo_mcp.server import build_server
from creo_mcp.tools.common import clean_dirname, join_path
from creo_mcp.tools.drawing import resolve_view

HTL = "abtriebsnabe_htl.prt"


@pytest.fixture()
async def client(mock):
    settings = Settings(creoson_url=mock.url, timeout=10, template_dir=TEMPLATE_DIR)
    async with Client(build_server(settings, CreosonClient(settings))) as c:
        await c.call_tool("creo_open_model", {"file": "fliehkraftkupplung.asm"})
        yield c


def _text(result):
    return "\n".join(getattr(c, "text", "") for c in result.content)


# -- Modellbaum / KE-Liste --------------------------------------------------------

async def test_tree_of_htl_part_nests_unnamed_pattern_and_hides_german_datums(client):
    text = _text(await client.call_tool("creo_get_model_tree", {"file": HTL, "include_datums": False}))
    assert "BEZUGSEBENE" not in text and "KÖRPER" in text
    assert "▦ (ohne Namen)  [MUSTER]" in text
    assert text.count("[BOHRUNG]") == 6 and "Feature-IDs" in text


async def test_list_features_type_filter_works_with_german_creo(client, mock):
    for type_filter in ("HOLE", "BOHRUNG", "hole"):
        res = await client.call_tool("creo_list_features", {"file": HTL, "type": type_filter, "response_format": "json"})
        assert not res.is_error, _text(res)
        assert '"total": 6' in _text(res), type_filter
    # Filter läuft im Server, nicht in CREOSON (das würde nur den deutschen Namen kennen)
    assert all("type" not in c[2] for c in mock.state.calls if c[:2] == ("feature", "list"))


async def test_list_features_hides_german_datums(client):
    res = _text(await client.call_tool("creo_list_features", {"file": HTL, "include_datums": False}))
    assert "BEZUGSACHSE" not in res and "KOORDINATENSYSTEM" not in res and "MATERIALSCHNITT" in res


# -- Verzeichnisse ------------------------------------------------------------------

def test_clean_dirname_removes_doubled_drive():
    assert clean_dirname("C:C:/Users/User/Documents/Creo/") == "C:/Users/User/Documents/Creo/"
    assert clean_dirname("C:C:\\Users\\User\\") == "C:\\Users\\User\\"
    assert clean_dirname("D:/ok/") == "D:/ok/" and clean_dirname(None) is None


def test_join_path_keeps_one_separator():
    assert join_path("C:\\Users\\User\\Documents\\Creo\\", "teil.pdf") == "C:\\Users\\User\\Documents\\Creo\\teil.pdf"
    assert join_path("C:/Creo_MCP/arbeit", "teil.pdf") == "C:/Creo_MCP/arbeit/teil.pdf"
    assert join_path(None, "teil.pdf") == "teil.pdf"


async def test_open_model_message_has_clean_directory(client, mock):
    mock.state.double_drive_quirk = True
    text = _text(await client.call_tool("creo_open_model", {"file": HTL}))
    assert "C:C:" not in text and "C:/Creo_MCP/arbeit" in text
    info = _text(await client.call_tool("creo_get_model_info", {"file": HTL}))
    assert "C:C:" not in info


# -- Zeichnung --------------------------------------------------------------------

@pytest.mark.parametrize(
    ("wanted", "found"),
    [("FRONT", "VORNE - FRONT"), ("front", "VORNE - FRONT"), ("VORNE", "VORNE - FRONT"), ("BACK", "HINTEN - REAR"), ("DEFAULT", "DEFAULT"), ("SCHRAEG", None)],
)
def test_resolve_view_matches_htl_names(wanted, found):
    views = ["DEFAULT", "GOODVIEW", "HINTEN - REAR", "LINKS - LEFT", "OBEN - TOP", "RECHTS - RIGHT", "UNTEN - BOTTOM", "VORNE - FRONT"]
    assert resolve_view(wanted, views) == found


async def test_create_a3_drawing_for_htl_part_saves_missing_template_views(client, mock):
    res = await client.call_tool("creo_create_drawing", {"model": HTL, "scale": 0.5})
    text = _text(res)
    assert not res.is_error, text
    assert "FRONT ← VORNE - FRONT" in text and "RIGHT ← RECHTS - RIGHT" in text
    model = mock.state.session[HTL]
    assert {"FRONT", "TOP", "RIGHT"} <= set(model.views)
    drw = mock.state.session["abtriebsnabe_htl.drw"]
    assert not drw.broken and len(drw.views) == 3
    saves = [c[2]["name"] for c in mock.state.calls if c[:2] == ("view", "save")]
    assert saves == ["FRONT", "TOP", "RIGHT"]


async def test_create_drawing_explains_missing_template_views(client, mock):
    mock.state.session.pop(HTL, None)
    disk_model = mock.state.disk["c:/creo_mcp/arbeit"][HTL]
    disk_model.views = ["DEFAULT", "SCHRAEG"]  # keine Ansicht, aus der FRONT/TOP/RIGHT werden kann
    res = await client.call_tool("creo_create_drawing", {"model": HTL})
    text = _text(res)
    assert res.is_error
    assert "FRONT, TOP, RIGHT" in text and "SCHRAEG" in text
    assert "creo_close_model" in text and "abtriebsnabe_htl.drw" in text


async def test_add_view_resolves_english_name_on_htl_part(client, mock):
    await client.call_tool("creo_create_drawing", {"model": HTL})
    res = await client.call_tool(
        "creo_add_drawing_view", {"drawing": "abtriebsnabe_htl.drw", "view_name": "ISO", "model_view": "LEFT", "x": 300, "y": 200}
    )
    assert not res.is_error, _text(res)
    assert "LINKS - LEFT" in _text(res)
    data = [c[2] for c in mock.state.calls if c[:2] == ("drawing", "create_gen_view")][-1]
    assert data["model_view"] == "LINKS - LEFT"


async def test_add_view_lists_available_views_when_name_is_unknown(client):
    await client.call_tool("creo_create_drawing", {"model": HTL})
    res = await client.call_tool(
        "creo_add_drawing_view", {"drawing": "abtriebsnabe_htl.drw", "view_name": "X", "model_view": "SCHRAEG", "x": 1, "y": 1}
    )
    assert res.is_error and "VORNE - FRONT" in _text(res)
