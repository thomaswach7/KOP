from creo_mcp.config import Settings


def test_defaults():
    s = Settings.from_env({})
    assert s.creoson_url == "http://localhost:9056/creoson"
    assert s.creo_version == 12
    assert s.timeout == 120.0
    assert s.read_only is False
    assert s.allow_dangerous is False
    assert s.allow_system_mapkeys is False
    assert s.start_command == "nitro_proe_remote.bat"
    assert s.max_tree_nodes == 400


def test_flags_from_env():
    s = Settings.from_env({"CREO_MCP_READ_ONLY": "1", "CREO_VERSION": "11", "CREOSON_URL": "http://pc:9100/creoson"})
    assert s.read_only is True
    assert s.creo_version == 11
    assert s.creoson_url == "http://pc:9100/creoson"


def test_creo_version_zero_disables_version_call():
    assert Settings.from_env({"CREO_VERSION": "0"}).creo_version is None
