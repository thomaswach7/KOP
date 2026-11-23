"""Asynchroner Client für CREOSON (JSON über HTTP).

- Baut die CREOSON-Sitzung bei Bedarf auf und setzt danach `creo.set_creo_version`
  (ohne das schlagen in Creo 7+ suppress/resume/delete/regenerate/assemble fehl).
- Verbindet genau einmal neu, wenn CREOSON "No session found" meldet (CREOSON neu gestartet).
- Serialisiert alle Aufrufe: Creo/J-Link ist single-threaded.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

from .config import Settings
from .errors import CreosonConnectionError, CreosonError

log = logging.getLogger(__name__)

_NO_SESSION = "No session found"

# Bekannte CREOSON-/Creo-Fehlertexte → Hinweis, was zu tun ist.
_HINTS: list[tuple[str, str]] = [
    (
        "Unable to connect to Creo",
        "Creo is not running or was not started with CREOSON support. Start Creo via CREOSON "
        "(CreosonSetup → 'Start Creo', or tool creo_connect with start_creo=true, which runs "
        "nitro_proe_remote.bat and sets PRO_COMM_MSG_EXE). Then retry.",
    ),
    ("more than one instance of Creo", "Close all but one Creo session, then retry."),
    ("No active model", "Open a model first (creo_open_model with activate=true) or pass 'file'."),
    ("is not in session", "Open the model first with creo_open_model (use the full name incl. extension, e.g. teil.prt)."),
    ("not found", "Check the name (incl. extension .prt/.asm/.drw) and the working directory (creo_set_working_dir)."),
    ("Obsolete Function", "CREOSON needs the right Creo version: set CREO_VERSION (default 12)."),
    ("XToolkitBadContext", "Creo is busy in a dialog/mode. Close open dialogs in Creo and retry."),
    ("XToolkitCantModify", "The model is read-only (e.g. checked in to Windchill or a template). Save a copy first."),
]


def with_hint(message: str) -> str:
    for needle, hint in _HINTS:
        if needle.lower() in message.lower():
            return f"{message} — Hint: {hint}"
    return message


class CreosonClient:
    """Dünner, robuster Client für CREOSON."""

    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.session_id: str | None = None
        self.version_warning: str | None = None
        self._http = httpx.AsyncClient(timeout=settings.timeout, transport=transport)
        self._lock = asyncio.Lock()

    async def call(self, command: str, function: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Führt eine CREOSON-Funktion aus und gibt deren `data`-Teil zurück ({} wenn leer)."""
        async with self._lock:
            if self.session_id is None:
                await self._connect()
            try:
                return await self._request(command, function, data)
            except CreosonError as exc:
                if _NO_SESSION not in exc.message:
                    raise
                log.info("CREOSON-Sitzung verloren, verbinde neu")
                self.session_id = None
                await self._connect()
                return await self._request(command, function, data)

    async def reset(self) -> None:
        async with self._lock:
            self.session_id = None

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _connect(self) -> None:
        resp = await self._post({"command": "connection", "function": "connect"})
        status = resp.get("status") or {}
        if status.get("error") or not resp.get("sessionId"):
            raise CreosonError(with_hint(status.get("message") or "connect returned no sessionId"), "connection", "connect")
        self.session_id = resp["sessionId"]
        self.version_warning = None
        if self.settings.creo_version:
            try:
                await self._request("creo", "set_creo_version", {"version": self.settings.creo_version})
            except CreosonError as exc:
                # Sitzung trotzdem nutzen; nur Funktionen wie suppress/regenerate können dann scheitern.
                self.version_warning = f"set_creo_version({self.settings.creo_version}) failed: {exc.message}"
                log.warning(self.version_warning)

    async def _request(self, command: str, function: str, data: dict[str, Any] | None) -> dict[str, Any]:
        payload: dict[str, Any] = {"command": command, "function": function}
        if self.session_id:
            payload["sessionId"] = self.session_id
        if data:
            payload["data"] = data
        resp = await self._post(payload)
        status = resp.get("status") or {}
        if status.get("error"):
            message = status.get("message") or "unknown CREOSON error"
            if _NO_SESSION in message:
                raise CreosonError(message, command, function)
            raise CreosonError(with_hint(message), command, function)
        return resp.get("data") or {}

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = self.settings.creoson_url
        try:
            resp = await self._http.post(url, content=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            resp.raise_for_status()
        except httpx.TimeoutException as exc:
            raise CreosonConnectionError(
                f"CREOSON at {url} did not answer within {self.settings.timeout:.0f} s "
                f"({payload.get('command')}.{payload.get('function')}). Creo may still be working; "
                "raise CREO_MCP_TIMEOUT for long operations, or run creo_doctor."
            ) from exc
        except httpx.HTTPError as exc:
            raise CreosonConnectionError(
                f"Cannot reach CREOSON at {url} ({type(exc).__name__}). Start the CREOSON server "
                "(CreosonSetup.exe → 'Start CREOSON', port 9056) and check CREOSON_URL; run creo_doctor for a full check."
            ) from exc
        try:
            parsed = json.loads(resp.content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CreosonConnectionError(f"CREOSON at {url} returned invalid JSON; is CREOSON_URL correct?") from exc
        if not isinstance(parsed, dict):
            raise CreosonConnectionError(f"CREOSON at {url} returned an unexpected response")
        return parsed
