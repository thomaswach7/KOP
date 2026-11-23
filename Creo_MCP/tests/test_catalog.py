from creo_mcp.catalog import FunctionCatalog


def test_catalog_contains_all_creoson_functions():
    cat = FunctionCatalog.load()
    total = sum(len(fns) for fns in cat.commands().values())
    assert total == 175
    assert "get_paths" in cat.commands()["bom"]


def test_spec_exposes_request_parameters_with_types():
    spec = FunctionCatalog.load().get("bom", "get_paths")
    assert spec is not None
    params = {p.name: p.type for p in spec.request}
    assert params["paths"] == "boolean"


def test_validate_reports_unknown_parameter():
    problems = FunctionCatalog.load().validate("file", "open", {"filex": 1})
    assert any("filex" in p for p in problems)


def test_validate_reports_type_mismatch_for_boolean():
    problems = FunctionCatalog.load().validate("bom", "get_paths", {"paths": "yes"})
    assert any("paths" in p and "boolean" in p for p in problems)


def test_validate_accepts_correct_call():
    assert FunctionCatalog.load().validate("bom", "get_paths", {"file": "a.asm", "paths": True}) == []


def test_validate_unknown_function_suggests_alternative():
    problems = FunctionCatalog.load().validate("feature", "lst", {})
    assert problems and "list" in problems[0]


def test_describe_renders_markdown_with_parameters_and_example():
    text = FunctionCatalog.load().describe("feature", "list")
    assert "feature.list" in text
    assert "inc_unnamed" in text
    assert "Example" in text


def test_object_types_are_described():
    cat = FunctionCatalog.load()
    obj = cat.get_object("FeatureData")
    assert obj is not None
    assert "feat_id" in [f.name for f in obj.fields]
