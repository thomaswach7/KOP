from creo_mcp.client import CreosonClient
from creo_mcp.config import Settings
from creo_mcp.doctor import Probes, render_checks, run_diagnostics


class FakeProbes(Probes):
    def creo_installs(self):
        return ["C:/Program Files/PTC/Creo 12.4.4.0"]

    def creo_process_running(self):
        return True

    def com_registered(self):
        return False

    def pywin32_available(self):
        return True

    def path_exists(self, path):
        return False


def _by_name(checks, prefix):
    return next(c for c in checks if c.name.startswith(prefix))


async def test_doctor_against_mock_reports_ok(mock):
    settings = Settings(creoson_url=mock.url)
    checks = await run_diagnostics(settings, CreosonClient(settings), platform="linux")
    assert _by_name(checks, "CREOSON").ok is True
    assert _by_name(checks, "Creo connection").ok is True
    assert "✅" in render_checks(checks)


async def test_doctor_reports_unreachable_creoson():
    settings = Settings(creoson_url="http://127.0.0.1:9/creoson", timeout=2)
    checks = await run_diagnostics(settings, CreosonClient(settings), platform="linux")
    check = _by_name(checks, "CREOSON")
    assert check.ok is False and "CreosonSetup" in check.hint


async def test_doctor_reports_creo_not_running(mock):
    mock.state.creo_running = False
    settings = Settings(creoson_url=mock.url)
    checks = await run_diagnostics(settings, CreosonClient(settings), platform="linux")
    check = _by_name(checks, "Creo connection")
    assert check.ok is False and "creo_connect" in check.hint


async def test_doctor_windows_checks_use_probes(mock):
    settings = Settings(creoson_url=mock.url)
    checks = await run_diagnostics(settings, CreosonClient(settings), platform="win32", probes=FakeProbes())
    assert "Creo 12.4.4.0" in _by_name(checks, "Creo installation").detail
    vb = _by_name(checks, "VB API")
    assert vb.ok is False and "vb_api_register.bat" in vb.hint
