"""Sicherheitsschicht: Einstufung von CREOSON-Funktionen, Read-only-Modus, Mapkey-Prüfung.

Kategorien:
- read:      liest nur (Listen, Infos, Masseneigenschaften)
- session:   ändert nur den Sitzungs-/Anzeigezustand oder schreibt neue Exportdateien (öffnen, anzeigen, cd, Export)
- write:     ändert Modelldaten oder Dateien (setzen, löschen, speichern, regenerieren, Mapkeys)
- dangerous: Datenverlust außerhalb des Modells möglich (Dateien/Ordner löschen, Creo beenden, Workspace leeren)
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, Literal

from .config import Settings
from .errors import SafetyError

Category = Literal["read", "session", "write", "dangerous"]

_DANGEROUS = {
    ("connection", "kill_creo"),
    ("connection", "stop_creo"),
    ("creo", "delete_files"),
    ("creo", "rmdir"),
    ("windchill", "clear_workspace"),
    ("windchill", "delete_workspace"),
}
_READ_PREFIXES = ("list", "get_", "is_", "has_", "exists", "user_select")
_READ_EXACT = {
    "pwd",
    "massprops",
    "bound_box",
    "get_edges",
    "get_surfaces",
    "relations_get",
    "postregen_relations_get",
    "param_exists",
    "open_errors",
    "view_bound_box",
    "server_exists",
    "workspace_exists",
    "file_checked_out",
    "get_paths",
}
_SESSION = {
    ("connection", "connect"),
    ("connection", "disconnect"),
    ("connection", "start_creo"),
    ("creo", "set_creo_version"),
    ("creo", "cd"),
    ("creo", "mkdir"),
    ("file", "open"),
    ("file", "display"),
    ("file", "close_window"),
    ("file", "refresh"),
    ("file", "repaint"),
    ("file", "erase_not_displayed"),
    ("file", "backup"),
    ("view", "activate"),
    ("drawing", "select_sheet"),
    ("interface", "export_file"),
    ("interface", "export_pdf"),
    ("interface", "export_3dpdf"),
    ("interface", "export_image"),
    ("interface", "export_program"),
    ("interface", "plot"),
    ("windchill", "authorize"),
    ("windchill", "set_server"),
    ("windchill", "set_workspace"),
}


def classify(command: str, function: str) -> Category:
    key = (command, function)
    if key in _DANGEROUS:
        return "dangerous"
    if key in _SESSION:
        return "session"
    if function in _READ_EXACT or function.startswith(_READ_PREFIXES):
        return "read"
    return "write"


def guard_call(settings: Settings, command: str, function: str, data: Mapping[str, Any] | None = None) -> None:
    """Wirft SafetyError, wenn der Aufruf in der aktuellen Konfiguration nicht erlaubt ist.

    Prüft auch den Inhalt: Mapkey-Skripte und Mapkey-Definitionen über set_config dürfen kein @SYSTEM enthalten.
    """
    data = data or {}
    if (command, function) == ("interface", "mapkey"):
        check_mapkey(str(data.get("script") or ""), settings.allow_system_mapkeys)
    if (command, function) == ("creo", "set_config") and "mapkey" in str(data.get("name") or "").lower():
        check_mapkey(str(data.get("value") or ""), settings.allow_system_mapkeys)
    category = classify(command, function)
    if settings.read_only and category in ("write", "dangerous"):
        raise SafetyError(
            f"{command}.{function} changes model data, but the server runs in read-only mode "
            "(CREO_MCP_READ_ONLY=1). Remove that variable to allow changes."
        )
    if category == "dangerous" and not settings.allow_dangerous:
        raise SafetyError(
            f"{command}.{function} can destroy data outside the model (files, folders, unsaved Creo work). "
            "It is blocked unless CREO_MCP_ALLOW_DANGEROUS=1 is set in the MCP server configuration."
        )


_SYSTEM = re.compile(r"@system", re.IGNORECASE)


def check_mapkey(script: str, allow_system: bool) -> None:
    """Mapkeys mit @SYSTEM führen Betriebssystem-Befehle aus – standardmäßig gesperrt."""
    if _SYSTEM.search(script) and not allow_system:
        raise SafetyError(
            "The mapkey contains @SYSTEM, which runs operating-system commands. This is blocked unless "
            "CREO_MCP_ALLOW_SYSTEM_MAPKEYS=1 is set. Remove the @SYSTEM part or ask the user to enable it."
        )
