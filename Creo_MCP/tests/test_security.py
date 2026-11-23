"""Sicherheitsfunde aus dem security-review: start_creo darf nur das konfigurierte Startskript ausführen."""

import pytest
from mcp import Client

from creo_mcp.client import CreosonClient
from creo_mcp.config import Settings
from creo_mcp.errors import SafetyError
from creo_mcp.safety import guard_call
from creo_mcp.server import build_server

TRUSTED = "C:/CreosonServer"


def test_start_creo_from_foreign_folder_is_blocked():
    s = Settings(start_dir=TRUSTED)
    with pytest.raises(SafetyError):
        guard_call(s, "connection", "start_creo", {"start_dir": "C:/Users/x/Downloads/evil", "start_command": "nitro_proe_remote.bat"})


def test_start_creo_from_unc_share_is_blocked():
    s = Settings(start_dir=TRUSTED)
    with pytest.raises(SafetyError):
        guard_call(s, "connection", "start_creo", {"start_dir": "\\\\attacker\\share", "start_command": "nitro_proe_remote.bat"})


def test_start_creo_without_configured_folder_is_blocked():
    with pytest.raises(SafetyError):
        guard_call(Settings(), "connection", "start_creo", {"start_dir": TRUSTED, "start_command": "nitro_proe_remote.bat"})


def test_start_creo_with_trusted_folder_is_allowed_in_any_spelling():
    s = Settings(start_dir=TRUSTED, read_only=True)
    guard_call(s, "connection", "start_creo", {"start_dir": "c:\\creosonserver\\", "start_command": "nitro_proe_remote.bat"})


def test_read_only_mode_does_not_discard_unsaved_work():
    with pytest.raises(SafetyError):
        guard_call(Settings(read_only=True), "file", "erase_not_displayed", {})


async def test_creo_call_cannot_start_foreign_batch_file(mock):
    settings = Settings(creoson_url=mock.url, start_dir=TRUSTED)
    async with Client(build_server(settings, CreosonClient(settings))) as c:
        res = await c.call_tool(
            "creo_call",
            {"command": "connection", "function": "start_creo", "data": {"start_dir": "D:/evil", "start_command": "nitro_proe_remote.bat"}},
        )
    assert res.is_error and "CREO_START_DIR" in res.content[0].text
    assert ("connection", "start_creo") not in [c[:2] for c in mock.state.calls]


async def test_creo_connect_has_no_start_dir_argument(mock):
    settings = Settings(creoson_url=mock.url, start_dir=TRUSTED)
    async with Client(build_server(settings, CreosonClient(settings))) as c:
        tool = next(t for t in (await c.list_tools()).tools if t.name == "creo_connect")
    assert "start_dir" not in tool.input_schema.get("properties", {})
