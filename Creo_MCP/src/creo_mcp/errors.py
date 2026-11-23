"""Fehlerklassen des Creo-MCP-Servers."""

from __future__ import annotations


class CreoMCPError(Exception):
    """Basisklasse aller erwarteten Fehler."""


class CreosonError(CreoMCPError):
    """CREOSON hat einen Fehlerstatus zurückgegeben (z. B. Modell nicht gefunden)."""

    def __init__(self, message: str, command: str | None = None, function: str | None = None):
        self.message = message
        self.command = command
        self.function = function
        where = f"{command}.{function}: " if command and function else ""
        super().__init__(f"{where}{message}")


class CreosonConnectionError(CreoMCPError):
    """CREOSON ist nicht erreichbar (nicht gestartet, falsche URL, Firewall)."""


class SafetyError(CreoMCPError):
    """Ein Aufruf wurde von der Sicherheitsschicht blockiert."""
