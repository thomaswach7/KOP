import pytest

from creo_mcp.config import Settings
from creo_mcp.errors import SafetyError
from creo_mcp.mapkeys import command, normalize_mapkey
from creo_mcp.safety import check_mapkey, classify, guard_call


@pytest.mark.parametrize(
    ("command_", "function", "expected"),
    [
        ("feature", "list", "read"),
        ("file", "massprops", "read"),
        ("bom", "get_paths", "read"),
        ("file", "open", "session"),
        ("interface", "export_pdf", "session"),
        ("feature", "delete", "write"),
        ("dimension", "set", "write"),
        ("file", "save", "write"),
        ("interface", "mapkey", "write"),
        ("creo", "delete_files", "dangerous"),
        ("creo", "rmdir", "dangerous"),
        ("connection", "kill_creo", "dangerous"),
        ("connection", "stop_creo", "dangerous"),
        ("windchill", "clear_workspace", "dangerous"),
    ],
)
def test_classify(command_, function, expected):
    assert classify(command_, function) == expected


def test_read_only_blocks_writes_but_allows_reads():
    s = Settings(read_only=True)
    guard_call(s, "feature", "list")
    guard_call(s, "file", "open")
    with pytest.raises(SafetyError):
        guard_call(s, "feature", "suppress")


def test_dangerous_needs_explicit_permission():
    with pytest.raises(SafetyError) as exc:
        guard_call(Settings(), "creo", "delete_files")
    assert "CREO_MCP_ALLOW_DANGEROUS" in str(exc.value)
    guard_call(Settings(allow_dangerous=True), "creo", "delete_files")


def test_system_mapkey_is_blocked_by_default():
    with pytest.raises(SafetyError) as exc:
        check_mapkey("~ Command `ProCmdModelSave` ;@SYSTEMdel /q C:\\\\*;", allow_system=False)
    assert "@SYSTEM" in str(exc.value)
    check_mapkey("@system dir;", allow_system=True)


def test_normalize_mapkey_strips_definition_and_continuations():
    raw = "mapkey $F2 ~ Command `A`;\\\nmapkey(continued) ~ Command `B`;"
    assert normalize_mapkey(raw) == "~ Command `A`;~ Command `B`;"


def test_normalize_mapkey_removes_label_metadata():
    raw = "mapkey sv @MAPKEY_NAMESpeichern;@MAPKEY_LABELSpeichern;\\\nmapkey(continued) ~ Command `ProCmdModelSave` ;"
    assert normalize_mapkey(raw) == "~ Command `ProCmdModelSave` ;"


def test_normalize_mapkey_keeps_plain_macro():
    assert normalize_mapkey("~ Command `ProCmdRegenPart` ;") == "~ Command `ProCmdRegenPart` ;"


def test_command_builder():
    assert command("ProCmdModelSave") == "~ Command `ProCmdModelSave` ;"
    assert command("ProCmdNamedViewsGalSelect", "FRONT") == "~ Command `ProCmdNamedViewsGalSelect` `FRONT`;"
