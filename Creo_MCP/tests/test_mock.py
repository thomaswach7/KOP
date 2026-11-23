import httpx
import pytest

from creo_mcp.mock.server import start_mock_server


@pytest.fixture()
def mock():
    handle = start_mock_server()
    yield handle
    handle.stop()


def _post(url, payload):
    resp = httpx.post(url, json=payload, timeout=5)
    resp.raise_for_status()
    return resp.json()


def _session(url):
    return _post(url, {"command": "connection", "function": "connect"})["sessionId"]


def _call(url, sid, command, function, data=None):
    return _post(url, {"sessionId": sid, "command": command, "function": function, "data": data or {}})


def test_connect_returns_session_id(mock):
    res = _post(mock.url, {"command": "connection", "function": "connect"})
    assert res["status"]["error"] is False
    assert res["sessionId"]


def test_call_without_valid_session_reports_no_session_found(mock):
    res = _call(mock.url, "bogus", "file", "get_active")
    assert res["status"]["error"] is True
    assert "No session found" in res["status"]["message"]


def test_open_and_get_active(mock):
    sid = _session(mock.url)
    opened = _call(mock.url, sid, "file", "open", {"file": "abtriebsnabe.prt", "display": True, "activate": True})
    assert opened["data"]["files"] == ["abtriebsnabe.prt"]
    active = _call(mock.url, sid, "file", "get_active")
    assert active["data"]["file"] == "abtriebsnabe.prt"


def test_feature_list_returns_ids_numbers_types(mock):
    sid = _session(mock.url)
    _call(mock.url, sid, "file", "open", {"file": "abtriebsnabe.prt"})
    res = _call(mock.url, sid, "feature", "list", {"file": "abtriebsnabe.prt", "inc_unnamed": True, "paths": True})
    feats = res["data"]["featlist"]
    first = feats[0]
    assert {"name", "type", "status", "feat_id", "feat_number"} <= set(first)
    assert first["type"] == "DATUM PLANE"
    names = [f["name"] for f in feats]
    assert "Grundkörper" in names
    without_unnamed = _call(mock.url, sid, "feature", "list", {"file": "abtriebsnabe.prt"})["data"]["featlist"]
    assert len(without_unnamed) < len(feats)
    assert "feat_number" not in without_unnamed[0]


def test_bom_paths_match_component_feature_ids(mock):
    sid = _session(mock.url)
    _call(mock.url, sid, "file", "open", {"file": "fliehkraftkupplung.asm"})
    bom = _call(mock.url, sid, "bom", "get_paths", {"file": "fliehkraftkupplung.asm", "paths": True})["data"]
    root = bom["children"]
    assert root["file"] == "fliehkraftkupplung.asm" and root["seq_path"] == "root"
    comp_ids = {
        f["feat_id"]
        for f in _call(mock.url, sid, "feature", "list", {"file": "fliehkraftkupplung.asm", "inc_unnamed": True})["data"]["featlist"]
        if f["type"] == "COMPONENT"
    }
    assert {child["path"][-1] for child in root["children"]} == comp_ids
    sub = next(c for c in root["children"] if c["file"] == "fliehgewicht.asm")
    assert len(sub["children"]) == 2 and len(sub["children"][0]["path"]) == 2


def test_suppress_changes_status(mock):
    sid = _session(mock.url)
    _call(mock.url, sid, "file", "open", {"file": "abtriebsnabe.prt"})
    _call(mock.url, sid, "feature", "suppress", {"file": "abtriebsnabe.prt", "name": "Passfedernut"})
    feats = _call(mock.url, sid, "feature", "list", {"file": "abtriebsnabe.prt", "name": "Passfedernut"})["data"]["featlist"]
    assert feats[0]["status"] == "SUPPRESSED"


def test_rename_roundtrips_umlauts(mock):
    sid = _session(mock.url)
    _call(mock.url, sid, "file", "open", {"file": "abtriebsnabe.prt"})
    feats = _call(mock.url, sid, "feature", "list", {"file": "abtriebsnabe.prt", "name": "Passfedernut"})["data"]["featlist"]
    _call(mock.url, sid, "feature", "rename", {"file": "abtriebsnabe.prt", "feat_id": feats[0]["feat_id"], "new_name": "Nut_für_Passfeder_ÄÖÜß"})
    names = [f["name"] for f in _call(mock.url, sid, "feature", "list", {"file": "abtriebsnabe.prt"})["data"]["featlist"]]
    assert "Nut_für_Passfeder_ÄÖÜß" in names


def test_unsimulated_function_reports_error(mock):
    sid = _session(mock.url)
    res = _call(mock.url, sid, "windchill", "authorize", {"user": "x", "password": "y"})
    assert res["status"]["error"] is True
    assert "not simulated" in res["status"]["message"]


def test_calls_are_logged_for_assertions(mock):
    sid = _session(mock.url)
    _call(mock.url, sid, "creo", "set_creo_version", {"version": 12})
    assert ("creo", "set_creo_version") in [(c[0], c[1]) for c in mock.state.calls]
    assert mock.state.creo_versions[sid] == 12
