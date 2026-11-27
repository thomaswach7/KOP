import pytest

from creo_mcp.client import CreosonClient
from creo_mcp.config import Settings
from creo_mcp.errors import CreosonConnectionError, CreosonError


async def test_first_call_connects_and_sets_creo_version(mock, settings):
    client = CreosonClient(settings)
    data = await client.call("creo", "pwd")
    assert data["dirname"] == "C:/Creo_MCP/arbeit"
    names = [(c[0], c[1]) for c in mock.state.calls]
    assert names[:2] == [("connection", "connect"), ("creo", "set_creo_version")]
    assert mock.state.creo_versions[client.session_id] == 12
    await client.aclose()


async def test_creoson_error_is_raised_with_message(settings):
    client = CreosonClient(settings)
    with pytest.raises(CreosonError) as exc:
        await client.call("file", "open", {"file": "gibtsnicht.prt"})
    assert "gibtsnicht.prt" in str(exc.value)
    await client.aclose()


async def test_reconnects_once_when_session_was_lost(mock, settings):
    client = CreosonClient(settings)
    await client.call("creo", "pwd")
    old = client.session_id
    mock.state.sessions.clear()  # CREOSON neu gestartet
    data = await client.call("creo", "pwd")
    assert data["dirname"]
    assert client.session_id != old
    assert mock.state.creo_versions[client.session_id] == 12
    await client.aclose()


async def test_unreachable_creoson_gives_actionable_error():
    client = CreosonClient(Settings(creoson_url="http://127.0.0.1:9/creoson", timeout=2))
    with pytest.raises(CreosonConnectionError) as exc:
        await client.call("creo", "pwd")
    text = str(exc.value)
    assert "CREOSON" in text and "creo_doctor" in text
    await client.aclose()


async def test_creo_not_running_error_has_start_hint(mock, settings):
    mock.state.creo_running = False
    client = CreosonClient(settings)
    with pytest.raises(CreosonError) as exc:
        await client.call("file", "get_active")
    assert "Unable to connect to Creo" in str(exc.value)
    assert "nitro_proe_remote.bat" in str(exc.value)
    await client.aclose()


def test_two_creo_sessions_get_their_own_hint():
    # Echtes Creo 12 (27.11.2026) bei feature.delete mit zwei laufenden xtop.exe. Früher griff zuerst der Hinweis
    # "Unable to connect to Creo" (Creo starten) – falsch, Creo lief ja doppelt.
    from creo_mcp.client import with_hint

    text = with_hint("Error handling request: Unable to connect to Creo; more than one instance of Creo is running")
    assert "close the extra Creo session" in text
    assert "nitro_proe_remote.bat" not in text


def test_cant_access_hint_points_to_relations():
    from creo_mcp.client import with_hint

    text = with_hint("parameter.set: A Pro/TOOLKIT error has occurred: Can't Access.  Check your model/drawing for accuracy.")
    assert "relation" in text and "creo_set_material" in text


async def test_timeout_message_mentions_open_creo_dialog(settings):
    import httpx

    def hang(request):
        raise httpx.ReadTimeout("timed out", request=request)

    client = CreosonClient(settings, transport=httpx.MockTransport(hang))
    with pytest.raises(CreosonConnectionError) as exc:
        await client.call("creo", "pwd")
    assert "middle mouse button" in str(exc.value)
    await client.aclose()


async def test_version_call_skipped_when_disabled(mock):
    client = CreosonClient(Settings(creoson_url=mock.url, creo_version=None))
    await client.call("creo", "pwd")
    assert ("creo", "set_creo_version") not in [(c[0], c[1]) for c in mock.state.calls]
    await client.aclose()


async def test_version_failure_does_not_block_the_session(mock, settings):
    mock.state.fail_functions[("creo", "set_creo_version")] = "Invalid function: set_creo_version"
    client = CreosonClient(settings)
    assert (await client.call("creo", "pwd"))["dirname"]
    assert "set_creo_version" in (client.version_warning or "")
    connects = [c for c in mock.state.calls if c[:2] == ("connection", "connect")]
    await client.call("creo", "pwd")
    assert len([c for c in mock.state.calls if c[:2] == ("connection", "connect")]) == len(connects)
    await client.aclose()
