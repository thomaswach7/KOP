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


async def test_doctor_reports_missing_jlink_jar(mock):
    # So war es am echten PC: Creo 12 ohne "Java Objekt-Toolkit" → CREOSON startet nicht (NoClassDefFoundError)
    settings = Settings(creoson_url=mock.url)
    checks = await run_diagnostics(settings, CreosonClient(settings), platform="win32", probes=FakeProbes())
    jar = _by_name(checks, "J-Link")
    assert jar.ok is False and "Creo 12.4.4.0" in jar.detail
    assert "Java Object Toolkit" in jar.hint and "jxthrowable" in jar.hint


async def test_doctor_checks_jlink_jar_of_newest_creo(mock):
    class Probes12(FakeProbes):
        def creo_installs(self):
            return ["C:/Program Files/PTC/Creo 9.0.2.0", "C:/Program Files/PTC/Creo 10.0.4.0", "C:/Program Files/PTC/Creo 12.4.5.0"]

        def path_exists(self, path):
            return path.replace("\\", "/").endswith("Creo 12.4.5.0/Common Files/text/java/pfcasync.jar")

    settings = Settings(creoson_url=mock.url)
    checks = await run_diagnostics(settings, CreosonClient(settings), platform="win32", probes=Probes12())
    assert _by_name(checks, "J-Link").ok is True


def test_creo_installs_sorted_by_version_number():
    from creo_mcp.doctor import _version_key

    paths = ["C:/PTC/Creo 12.4.5.0", "C:/PTC/Creo 9.0.2.0", "C:/PTC/Creo 10.0.4.0"]
    assert sorted(paths, key=_version_key)[-1].endswith("12.4.5.0")


async def test_doctor_survives_failing_creo_call(mock):
    mock.state.fail_functions[("creo", "pwd")] = "XToolkitGeneralError"
    settings = Settings(creoson_url=mock.url)
    checks = await run_diagnostics(settings, CreosonClient(settings), platform="linux")
    check = _by_name(checks, "Creo connection")
    assert check.ok is False and "XToolkitGeneralError" in check.detail
