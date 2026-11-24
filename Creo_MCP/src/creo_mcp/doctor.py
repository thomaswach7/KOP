"""Diagnose: Welche Verbindungswege zu Creo funktionieren auf diesem PC – und was ist zu tun?"""

from __future__ import annotations

import glob
import importlib.metadata
import os
import platform as _platform
import re
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass

from .client import CreosonClient
from .config import Settings
from .errors import CreoMCPError, CreosonConnectionError


@dataclass
class Check:
    name: str
    ok: bool | None
    detail: str
    hint: str = ""


JLINK_JAR = os.path.join("Common Files", "text", "java", "pfcasync.jar")


def _version_key(path: str) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", os.path.basename(path.rstrip("\\/"))))


class Probes:
    """Systemabfragen (Windows). In Tests ersetzbar."""

    def creo_installs(self) -> list[str]:
        """Creo-Installationen, älteste zuerst (Versionsnummern numerisch verglichen: 9 < 10 < 12)."""
        roots = glob.glob(r"C:\Program Files\PTC\Creo *") + glob.glob(r"C:\PTC\Creo *")
        return sorted((r for r in roots if os.path.isfile(os.path.join(r, "Parametric", "bin", "parametric.exe"))), key=_version_key)

    def creo_process_running(self) -> bool | None:
        try:
            out = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq xtop.exe", "/NH"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            return None
        return "xtop.exe" in out.lower()

    def com_registered(self) -> bool | None:
        try:
            import winreg  # type: ignore[import-not-found]
        except ImportError:
            return None
        try:
            winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "pfcls.pfcAsyncConnection"))
            return True
        except OSError:
            return False

    def pywin32_available(self) -> bool:
        try:
            import win32com.client  # type: ignore[import-not-found]  # noqa: F401
        except ImportError:
            return False
        return True

    def path_exists(self, path: str) -> bool:
        return os.path.exists(path)


def _version(pkg: str) -> str:
    try:
        return importlib.metadata.version(pkg)
    except importlib.metadata.PackageNotFoundError:
        return "?"


async def run_diagnostics(
    settings: Settings,
    client: CreosonClient,
    *,
    platform: str = sys.platform,
    probes: Probes | None = None,
    env: Mapping[str, str] | None = None,
) -> list[Check]:
    env = os.environ if env is None else env
    probes = probes or Probes()
    checks = [
        Check("Python / MCP", None, f"Python {_platform.python_version()}, mcp {_version('mcp')}, creo-mcp {_version('creo-mcp')}"),
        Check("Settings", None, f"CREOSON_URL={settings.creoson_url}, CREO_VERSION={settings.creo_version}, read-only={settings.read_only}"),
    ]

    running: bool | None = None
    try:
        data = await client.call("connection", "is_creo_running")
        running = bool(data.get("running"))
        checks.append(Check("CREOSON server", True, f"reachable at {settings.creoson_url}"))
    except CreosonConnectionError as exc:
        checks.append(
            Check(
                "CREOSON server",
                False,
                str(exc).split(" (")[0],
                "Download CREOSON 3.0.x (github.com/SimplifiedLogic/creoson/releases, CreosonServerWithSetup-*.zip), "
                "unzip, run CreosonSetup.exe, select the Creo 12 'Common Files' folder, click 'Start CREOSON'. "
                "Default port 9056 (CREOSON_URL).",
            )
        )
    except CreoMCPError as exc:
        checks.append(Check("CREOSON server", False, str(exc), "Check CREOSON_URL."))

    if running is not None:
        if running:
            try:
                pwd = await client.call("creo", "pwd")
                checks.append(Check("Creo connection", True, f"Creo connected, working directory {pwd.get('dirname')}"))
            except CreoMCPError as exc:
                checks.append(
                    Check(
                        "Creo connection",
                        False,
                        f"Creo is running but does not answer properly: {exc}",
                        "Close open dialogs in Creo; if it persists, restart Creo via nitro_proe_remote.bat.",
                    )
                )
        else:
            checks.append(
                Check(
                    "Creo connection",
                    False,
                    "CREOSON runs, but no Creo session is connected.",
                    "Start Creo through CREOSON: CreosonSetup → 'Start Creo', or tool creo_connect(start_creo=true) with "
                    "CREO_START_DIR pointing to the folder with nitro_proe_remote.bat. A Creo started from the desktop icon "
                    "cannot be reached (PRO_COMM_MSG_EXE missing).",
                )
            )
    if client.version_warning:
        checks.append(Check("Creo version", False, client.version_warning, "Update CREOSON to 3.0.x or set CREO_VERSION=0 to skip."))
    checks.append(
        Check(
            "Creo version setting",
            settings.creo_version is not None,
            f"set_creo_version({settings.creo_version})" if settings.creo_version else "not set",
            "" if settings.creo_version else "Set CREO_VERSION=12, otherwise suppress/resume/delete/regenerate can fail.",
        )
    )

    if platform != "win32":
        checks.append(Check("Platform", None, f"{platform}: Creo runs only on Windows; only CREOSON connectivity was checked."))
        return checks

    installs = probes.creo_installs()
    checks.append(
        Check(
            "Creo installation",
            bool(installs),
            ", ".join(os.path.basename(p.rstrip("\\/")) for p in installs) or "none found under C:\\Program Files\\PTC",
            "" if installs else "Install Creo Parametric or set CREO_TEMPLATE_DIR/CREO_START_DIR manually.",
        )
    )
    if installs:
        newest = installs[-1]
        jar = os.path.join(newest, JLINK_JAR)
        has_jar = probes.path_exists(jar)
        label = os.path.basename(newest.rstrip("\\/"))
        checks.append(
            Check(
                "J-Link for CREOSON (pfcasync.jar)",
                has_jar,
                jar if has_jar else f"missing in {label}",
                ""
                if has_jar
                else "CREOSON stops with 'NoClassDefFoundError: com/ptc/cipjava/jxthrowable'. Add the Creo component "
                "'Java Object Toolkit' (Creo setup.exe → Reconfigure → Creo Parametric → API Toolkits). It installs "
                "Common Files\\text\\java\\pfcasync.jar and otk.jar.",
            )
        )
    proc = probes.creo_process_running()
    checks.append(Check("Creo process (xtop.exe)", proc, {True: "running", False: "not running", None: "unknown"}[proc]))
    msg_exe = env.get("PRO_COMM_MSG_EXE")
    checks.append(
        Check(
            "PRO_COMM_MSG_EXE",
            None,
            msg_exe or "not set in the MCP server environment (normal – nitro_proe_remote.bat sets it for Creo)",
        )
    )
    com = probes.com_registered()
    pyw = probes.pywin32_available()
    vb_ok = bool(com) and pyw
    hint = []
    if not com:
        hint.append("run '<Creo>\\Parametric\\bin\\vb_api_register.bat' once as administrator")
    if not pyw:
        hint.append("pip install pywin32")
    checks.append(
        Check(
            "VB API (optional, parent/child relations)",
            vb_ok,
            f"COM registered: {com}, pywin32: {pyw}",
            ("To enable: " + "; ".join(hint)) if hint else "",
        )
    )
    if settings.start_dir:
        bat = os.path.join(settings.start_dir, settings.start_command)
        exists = probes.path_exists(bat)
        checks.append(Check("Start script", exists, bat, "" if exists else "Create it with CreosonSetup (it writes nitro_proe_remote.bat)."))
    return checks


def render_checks(checks: list[Check]) -> str:
    icon = {True: "✅", False: "❌", None: "ℹ️"}
    lines = ["## Creo-MCP Diagnose", "", "| | Check | Result |", "|---|---|---|"]
    for c in checks:
        lines.append(f"| {icon[c.ok]} | {c.name} | {c.detail.replace('|', '/')} |")
    todo = [c for c in checks if c.ok is False and c.hint]
    if todo:
        lines += ["", "### What to do"]
        lines += [f"- **{c.name}:** {c.hint}" for c in todo]
    return "\n".join(lines)
