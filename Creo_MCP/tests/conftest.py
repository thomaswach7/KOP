import pytest

from creo_mcp.config import Settings
from creo_mcp.mock.server import start_mock_server


@pytest.fixture()
def mock():
    handle = start_mock_server()
    yield handle
    handle.stop()


@pytest.fixture()
def settings(mock):
    return Settings(creoson_url=mock.url, timeout=10)
