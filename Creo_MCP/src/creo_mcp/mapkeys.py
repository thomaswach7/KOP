"""Mapkey-Hilfen: Normalisierung für CREOSON und kleine Bausteine.

Creo speichert Mapkeys in config.pro so:
    mapkey $F2 @MAPKEY_NAMEText;@MAPKEY_LABELText;\
    mapkey(continued) ~ Command `ProCmdModelSave` ;
CREOSON (interface.mapkey) erwartet nur den Makro-Teil, ohne "mapkey(continued)", in einer Zeile.
"""

from __future__ import annotations

import re

_DEFINITION = re.compile(r"^mapkey\s+\S+\s*", re.IGNORECASE)
_CONTINUED = re.compile(r"^mapkey\(continued\)\s*", re.IGNORECASE)
_META = re.compile(r"@MAPKEY_(?:NAME|LABEL)[^;]*;", re.IGNORECASE)


def normalize_mapkey(script: str) -> str:
    pieces = []
    for raw_line in script.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if line.endswith("\\"):
            line = line[:-1].rstrip()
        if not line:
            continue
        if _CONTINUED.match(line):
            line = _CONTINUED.sub("", line, count=1)
        elif _DEFINITION.match(line):
            line = _DEFINITION.sub("", line, count=1)
        line = _META.sub("", line).strip()
        if line:
            pieces.append(line)
    return "".join(pieces)


_ANY_DEFINITION = re.compile(r"^mapkey\s+(\S+)", re.IGNORECASE)


def parse_config_mapkeys(text: str) -> dict[str, str]:
    """Alle Mapkeys aus einer config.pro: {Tastenfolge: Makro für CREOSON}.

    Eine Definition beginnt mit 'mapkey <taste> …' und geht mit 'mapkey(continued) …' weiter. Kommt eine Taste
    mehrfach vor, gilt wie in Creo die letzte Definition.
    """
    blocks: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in text.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if _CONTINUED.match(line):
            if current is not None:
                blocks[current].append(line)
            continue
        match = _ANY_DEFINITION.match(line)
        if match:
            current = match.group(1)
            blocks[current] = [line]
        else:
            current = None
    return {key: normalize_mapkey("\n".join(lines)) for key, lines in blocks.items()}


def command(name: str, *args: str) -> str:
    """Baustein für einen Creo-Befehl, z. B. command("ProCmdModelSave")."""
    if not args:
        return f"~ Command `{name}` ;"
    return f"~ Command `{name}` " + " ".join(f"`{a}`" for a in args) + ";"
