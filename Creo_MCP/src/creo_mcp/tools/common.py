"""Gemeinsame Bausteine der MCP-Werkzeuge."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

from mcp.server.mcpserver.exceptions import ToolError
from mcp_types import ToolAnnotations

from ..catalog import FunctionCatalog
from ..client import CreosonClient
from ..config import Settings
from ..errors import CreoMCPError
from ..safety import guard_call

ResponseFormat = Literal["markdown", "json"]

READ = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
SESSION = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)
DESTRUCTIVE = ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=False, open_world_hint=False)

FILE_HELP = "Model name incl. extension, e.g. 'abtriebsnabe.prt' or 'kupplung.asm'. Default: the active model in Creo."


def clean(data: dict[str, Any] | None) -> dict[str, Any]:
    """Entfernt None-Werte: CREOSON nimmt dann seine Standardwerte."""
    return {k: v for k, v in (data or {}).items() if v is not None}


def to_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    def cell(v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, float):
            return f"{v:.6g}"
        return str(v).replace("|", "\\|").replace("\n", " ")

    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows]
    return "\n".join(out)


def paginate(items: list[Any], limit: int, offset: int) -> dict[str, Any]:
    page = items[offset : offset + limit]
    more = offset + len(page) < len(items)
    return {
        "total": len(items),
        "count": len(page),
        "offset": offset,
        "items": page,
        "has_more": more,
        "next_offset": offset + len(page) if more else None,
    }


def ext_name(name: str, ext: str) -> str:
    name = name.strip()
    return name if name.lower().endswith(f".{ext}") else f"{name}.{ext}"


@dataclass
class ToolContext:
    settings: Settings
    client: CreosonClient
    catalog: FunctionCatalog
    vbapi: Any = None  # VbApiSession, wird bei Bedarf verbunden

    async def call(self, command: str, function: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """CREOSON-Aufruf mit Sicherheitsprüfung; erwartete Fehler werden zu ToolError (für das Modell lesbar)."""
        payload = clean(data)
        try:
            guard_call(self.settings, command, function, payload)
            return await self.client.call(command, function, payload)
        except CreoMCPError as exc:
            raise ToolError(str(exc)) from exc

    async def try_call(self, command: str, function: str, data: dict[str, Any] | None = None) -> dict[str, Any] | None:
        try:
            return await self.call(command, function, data)
        except ToolError:
            return None

    async def ensure_open(self, file: str | None) -> str:
        """Stellt sicher, dass `file` in der Sitzung ist (öffnet es sonst ohne Anzeige); gibt den Namen zurück."""
        if not file:
            active = await self.call("file", "get_active")
            return str(active.get("file") or "")
        exists = await self.call("file", "exists", {"file": file})
        if not exists.get("exists"):
            await self.call("file", "open", {"file": file, "display": False})
        return file
