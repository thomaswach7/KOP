import json

import pytest
from mcp import Client

from creo_mcp.client import CreosonClient
from creo_mcp.config import Settings
from creo_mcp.mock.state import TEMPLATE_DIR
from creo_mcp.server import build_server


def _settings(mock, **kw):
    return Settings(creoson_url=mock.url, timeout=10, template_dir=TEMPLATE_DIR, **kw)


@pytest.fixture()
async def mcp_client(mock):
    server = build_server(_settings(mock), CreosonClient(_settings(mock)))
    async with Client(server) as c:
        await c.call_tool("creo_open_model", {"file": "fliehkraftkupplung.asm"})
        yield c


def _text(result):
    return "\n".join(getattr(c, "text", "") for c in result.content)


async def test_core_tools_are_listed(mcp_client):
    names = {t.name for t in (await mcp_client.list_tools()).tools}
    assert {"creo_get_model_tree", "creo_call", "creo_run_mapkey", "creo_status", "creo_new_model"} <= names
    for tool in (await mcp_client.list_tools()).tools:
        assert tool.name.startswith("creo_")
        assert tool.annotations is not None and tool.description


async def test_status_shows_working_dir_and_active_model(mcp_client):
    text = _text(await mcp_client.call_tool("creo_status", {}))
    assert "C:/Creo_MCP/arbeit" in text and "fliehkraftkupplung.asm" in text


async def test_model_tree_tool_returns_markdown(mcp_client):
    res = await mcp_client.call_tool("creo_get_model_tree", {})
    assert not res.is_error
    assert "abtriebsnabe.prt" in _text(res) and "Grundkörper" in _text(res)


async def test_model_tree_opens_unloaded_file(mcp_client, mock):
    mock.state.session.pop("deckel.prt", None)
    res = await mcp_client.call_tool("creo_get_model_tree", {"file": "deckel.prt"})
    assert not res.is_error and "Grundkörper" in _text(res)


async def test_set_dimension_and_regenerate(mcp_client, mock):
    res = await mcp_client.call_tool("creo_set_dimension", {"file": "abtriebsnabe.prt", "name": "d0", "value": 80})
    assert not res.is_error
    assert mock.state.session["abtriebsnabe.prt"].dims["d0"]["value"] == 80.0
    assert ("file", "regenerate") in [(c[0], c[1]) for c in mock.state.calls]


async def test_generic_call_rejects_unknown_parameter(mcp_client):
    res = await mcp_client.call_tool("creo_call", {"command": "file", "function": "open", "data": {"filex": "a.prt"}})
    assert res.is_error and "filex" in _text(res)


async def test_generic_call_returns_json(mcp_client):
    res = await mcp_client.call_tool("creo_call", {"command": "creo", "function": "pwd"})
    assert json.loads(_text(res))["dirname"] == "C:/Creo_MCP/arbeit"


async def test_generic_call_is_guarded(mcp_client):
    res = await mcp_client.call_tool("creo_call", {"command": "creo", "function": "delete_files", "data": {"filename": "*.prt"}})
    assert res.is_error and "CREO_MCP_ALLOW_DANGEROUS" in _text(res)


async def test_mapkey_with_system_is_rejected(mcp_client, mock):
    res = await mcp_client.call_tool("creo_run_mapkey", {"script": "@SYSTEMformat c:;"})
    assert res.is_error and "@SYSTEM" in _text(res)
    assert mock.state.mapkeys == []


async def test_mapkey_is_normalized_and_sent(mcp_client, mock):
    res = await mcp_client.call_tool("creo_run_mapkey", {"script": "mapkey sv ~ Command `ProCmdModelSave` ;"})
    assert not res.is_error
    assert mock.state.mapkeys[-1] == "~ Command `ProCmdModelSave` ;"


async def test_read_only_mode_blocks_changes(mock):
    server = build_server(_settings(mock, read_only=True), CreosonClient(_settings(mock)))
    async with Client(server) as c:
        await c.call_tool("creo_open_model", {"file": "abtriebsnabe.prt"})
        res = await c.call_tool("creo_suppress_features", {"file": "abtriebsnabe.prt", "names": ["Passfedernut"]})
        assert res.is_error and "read-only" in _text(res)
        ok = await c.call_tool("creo_list_features", {"file": "abtriebsnabe.prt"})
        assert not ok.is_error


async def test_suppress_defaults_to_no_clip(mcp_client, mock):
    await mcp_client.call_tool("creo_suppress_features", {"file": "abtriebsnabe.prt", "names": ["Passfedernut"]})
    data = [c[2] for c in mock.state.calls if (c[0], c[1]) == ("feature", "suppress")][-1]
    assert data["clip"] is False
    assert mock.state.session["abtriebsnabe.prt"].features[6].status == "SUPPRESSED"


async def test_mass_properties_json(mcp_client):
    res = await mcp_client.call_tool("creo_mass_properties", {"file": "abtriebsnabe.prt", "response_format": "json"})
    assert json.loads(_text(res))["volume"] == 350370.0


async def test_mass_properties_markdown_mentions_units(mcp_client):
    text = _text(await mcp_client.call_tool("creo_mass_properties", {"file": "abtriebsnabe.prt"}))
    assert "350" in text and "mm³" in text


async def test_new_model_from_template(mcp_client, mock):
    res = await mcp_client.call_tool("creo_new_model", {"name": "testteil"})
    assert not res.is_error, _text(res)
    assert "testteil.prt" in mock.state.files_in_dir()
    assert mock.state.active == "testteil.prt"
    names = [f.name for f in mock.state.session["testteil.prt"].features]
    assert names[:3] == ["RIGHT", "TOP", "FRONT"]


async def test_new_model_refuses_to_overwrite(mcp_client):
    res = await mcp_client.call_tool("creo_new_model", {"name": "abtriebsnabe"})
    assert res.is_error and "exists" in _text(res)


async def test_bom_counts_quantities(mcp_client):
    text = _text(await mcp_client.call_tool("creo_get_bom", {"file": "fliehkraftkupplung.asm"}))
    assert "| scheibe.prt | 2 |" in text
    assert "| gewicht.prt | 2 |" in text


async def test_list_features_paginates(mcp_client):
    res = await mcp_client.call_tool("creo_list_features", {"file": "abtriebsnabe.prt", "limit": 3, "response_format": "json"})
    data = json.loads(_text(res))
    assert data["count"] == 3 and data["has_more"] is True and data["next_offset"] == 3


async def test_export_step(mcp_client, mock):
    res = await mcp_client.call_tool("creo_export", {"file": "abtriebsnabe.prt", "format": "STEP"})
    assert not res.is_error
    assert mock.state.exports[-1]["kind"] == "STEP"


async def test_drawing_workflow(mcp_client, mock):
    res = await mcp_client.call_tool("creo_create_drawing", {"model": "abtriebsnabe.prt", "template": "a3_iso", "scale": 1.0})
    assert not res.is_error, _text(res)
    r1 = await mcp_client.call_tool("creo_add_drawing_view", {"drawing": "abtriebsnabe.drw", "view_name": "VORNE", "model_view": "FRONT", "x": 150, "y": 150})
    r2 = await mcp_client.call_tool("creo_add_drawing_view", {"drawing": "abtriebsnabe.drw", "view_name": "SEITE", "kind": "projection", "parent_view": "VORNE", "x": 300, "y": 150})
    assert not r1.is_error and not r2.is_error, _text(r2)
    info = _text(await mcp_client.call_tool("creo_get_drawing_info", {"drawing": "abtriebsnabe.drw"}))
    assert "VORNE" in info and "SEITE" in info
    edit = await mcp_client.call_tool("creo_edit_drawing", {"drawing": "abtriebsnabe.drw", "action": "scale_sheet", "sheet": 1, "scale": 0.5})
    assert not edit.is_error
    assert mock.state.session["abtriebsnabe.drw"].sheet_scale[1] == 0.5


async def test_describe_function(mcp_client):
    text = _text(await mcp_client.call_tool("creo_describe_function", {"command": "feature", "function": "list"}))
    assert "inc_unnamed" in text


async def test_resources_and_prompts(mcp_client):
    tree = await mcp_client.read_resource("creo://model-tree/abtriebsnabe.prt")
    assert "Grundkörper" in tree.contents[0].text
    prompts = {p.name for p in (await mcp_client.list_prompts()).prompts}
    assert {"pdf_zu_creo_modell", "modellbaum_pruefen"} <= prompts


async def test_doctor_tool(mcp_client):
    text = _text(await mcp_client.call_tool("creo_doctor", {}))
    assert "CREOSON server" in text and "✅" in text


async def test_feature_relations_needs_windows(mcp_client):
    res = await mcp_client.call_tool("creo_feature_relations", {"file": "abtriebsnabe.prt", "feat_id": 40})
    assert res.is_error and "Windows" in _text(res)
