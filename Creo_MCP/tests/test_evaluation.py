"""Prüft, dass die Antworten in evaluation.xml mit den Werkzeugen (Demo-Daten) tatsächlich herauskommen."""

import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import pytest
from mcp import Client

from creo_mcp.client import CreosonClient
from creo_mcp.config import Settings
from creo_mcp.server import build_server

EVAL = Path(__file__).resolve().parents[1] / "evaluation.xml"


def _answers():
    root = ET.parse(EVAL).getroot()
    return [qa.findtext("answer") for qa in root.findall("qa_pair")]


async def _json(client, tool, args):
    res = await client.call_tool(tool, {**args, "response_format": "json"})
    assert not res.is_error, res.content[0].text
    return json.loads(res.content[0].text)


@pytest.fixture()
async def c(mock):
    settings = Settings(creoson_url=mock.url, timeout=10)
    async with Client(build_server(settings, CreosonClient(settings))) as client:
        await client.call_tool("creo_open_model", {"file": "fliehkraftkupplung.asm"})
        yield client


async def test_evaluation_answers_are_reproducible(c):
    a = _answers()
    assert len(a) == 10
    tree = await _json(c, "creo_get_model_tree", {"file": "abtriebsnabe.prt"})
    nodes = tree["root"]["children"]
    pattern = next(n for n in nodes if n["kind"] == "pattern")
    assert str(len(pattern["children"])) == a[0]
    feats = (await _json(c, "creo_list_features", {"file": "abtriebsnabe.prt"}))["items"]
    assert next(f["name"] for f in feats if f["feat_id"] == 60) == a[1]
    bom = await _json(c, "creo_get_bom", {"file": "fliehkraftkupplung.asm"})
    counts = Counter()

    def walk(n):
        for ch in n.get("children") or []:
            counts[ch["file"]] += 1
            walk(ch)

    walk(bom["children"])
    assert str(counts["scheibe.prt"]) == a[2]
    dims = await _json(c, "creo_list_dimensions", {"file": "abtriebsnabe.prt", "name": "d3"})
    assert f"{dims[0]['value']:g}" == a[3]
    params = await _json(c, "creo_list_parameters", {"file": "abtriebsnabe.prt", "name": "WERKSTOFF"})
    assert params[0]["value"] == a[4]
    mp = await _json(c, "creo_mass_properties", {"file": "fliehgewicht.asm"})
    assert str(round(mp["volume"])) == a[5]
    volumes = {}
    for part in [f for f in counts if f.endswith(".prt")]:
        volumes[part] = (await _json(c, "creo_mass_properties", {"file": part}))["volume"]
    assert max(volumes, key=volumes.get) == a[6]
    assert str(len(feats)) == a[7]
    group = next(n for n in nodes if n["kind"] == "group")
    assert group["name"] == a[8]
    assert str(next(f["feat_number"] for f in feats if f["name"] == "Freistich_DIN509")) == a[9]
