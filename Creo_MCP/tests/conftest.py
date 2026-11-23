import inspect

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


@pytest.fixture()
def anyio_backend():
    return "asyncio"


def pytest_collection_modifyitems(items):
    # Alle async-Tests laufen über das anyio-Plugin (Fixture und Test im selben Task – nötig für mcp.Client).
    for item in items:
        if inspect.iscoroutinefunction(getattr(item, "function", None)):
            item.add_marker(pytest.mark.anyio)
