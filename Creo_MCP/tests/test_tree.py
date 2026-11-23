import pytest

from creo_mcp.client import CreosonClient
from creo_mcp.tree import TreeNode, build_model_tree, render_tree_markdown, tree_to_dict


@pytest.fixture()
async def client(settings):
    c = CreosonClient(settings)
    await c.call("file", "open", {"file": "fliehkraftkupplung.asm", "activate": True})
    yield c
    await c.aclose()


def _find(node: TreeNode, pred):
    if pred(node):
        return node
    for child in node.children:
        hit = _find(child, pred)
        if hit:
            return hit
    return None


async def test_assembly_tree_nests_component_contents(client):
    result = await build_model_tree(client.call)
    root = result.root
    assert root.kind == "model" and root.name == "fliehkraftkupplung.asm"
    comp = _find(root, lambda n: n.kind == "component" and n.file == "abtriebsnabe.prt")
    assert comp is not None and comp.feat_id == 43
    assert _find(comp, lambda n: n.name == "Grundkörper") is not None
    sub = _find(root, lambda n: n.kind == "component" and n.file == "fliehgewicht.asm")
    assert {c.file for c in sub.children if c.kind == "component"} == {"gewicht.prt", "belag.prt"}


async def test_pattern_members_hang_under_pattern_head(client):
    result = await build_model_tree(client.call, "abtriebsnabe.prt")
    top_names = [n.name for n in result.root.children]
    pattern = next(n for n in result.root.children if n.kind == "pattern")
    assert pattern.name == "Muster_Bohrungen"
    assert len(pattern.children) == 4
    assert "Bohrung_Stirnsenker" not in top_names
    group = next(n for n in result.root.children if n.kind == "group")
    assert [c.name for c in group.children] == ["Fase_Bund", "Fase_Bohrung"]


async def test_suppressed_feature_is_marked(client):
    await client.call("feature", "suppress", {"file": "abtriebsnabe.prt", "name": "Passfedernut"})
    result = await build_model_tree(client.call, "abtriebsnabe.prt")
    nut = _find(result.root, lambda n: n.name == "Passfedernut")
    assert nut.status == "SUPPRESSED"
    assert "⊘ Passfedernut" in render_tree_markdown(result)


async def test_max_nodes_truncates_with_notice(client):
    result = await build_model_tree(client.call, max_nodes=5)
    assert result.truncated is True
    assert result.node_count <= 5
    assert "abgeschnitten" in render_tree_markdown(result)


async def test_datums_can_be_hidden(client):
    result = await build_model_tree(client.call, "abtriebsnabe.prt", include_datums=False)
    assert _find(result.root, lambda n: n.type == "DATUM PLANE") is None
    assert _find(result.root, lambda n: n.name == "Grundkörper") is not None


async def test_components_only_view(client):
    result = await build_model_tree(client.call, include_features=False)
    kinds = set()

    def walk(n):
        kinds.add(n.kind)
        for c in n.children:
            walk(c)

    walk(result.root)
    assert kinds == {"model", "component"}


async def test_max_depth_limits_component_expansion(client):
    result = await build_model_tree(client.call, max_depth=1)
    sub = _find(result.root, lambda n: n.kind == "component" and n.file == "fliehgewicht.asm")
    assert sub.children == []


async def test_unnamed_feature_is_listed_with_placeholder(client):
    result = await build_model_tree(client.call, "abtriebsnabe.prt")
    axis = _find(result.root, lambda n: n.type == "DATUM AXIS")
    assert axis is not None and axis.name == ""
    assert "(ohne Namen)" in render_tree_markdown(result)


async def test_tree_to_dict_is_json_ready(client):
    import json

    result = await build_model_tree(client.call, "abtriebsnabe.prt")
    d = tree_to_dict(result)
    json.dumps(d)
    assert d["root"]["name"] == "abtriebsnabe.prt"
    assert d["node_count"] == result.node_count
