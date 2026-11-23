"""Konfiguration des Creo-MCP-Servers über Umgebungsvariablen."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

_TRUE = {"1", "true", "yes", "ja", "on"}


def _flag(env: Mapping[str, str], key: str) -> bool:
    return env.get(key, "").strip().lower() in _TRUE


@dataclass(frozen=True)
class Settings:
    """Laufzeit-Einstellungen. Alle Werte kommen aus Umgebungsvariablen (siehe README)."""

    creoson_url: str = "http://localhost:9056/creoson"
    creo_version: int | None = 12
    timeout: float = 120.0
    read_only: bool = False
    allow_dangerous: bool = False
    allow_system_mapkeys: bool = False
    start_dir: str | None = None
    start_command: str = "nitro_proe_remote.bat"
    max_tree_nodes: int = 400

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if env is None else env
        version_raw = env.get("CREO_VERSION", "12").strip()
        version = int(version_raw) if version_raw else 12
        return cls(
            creoson_url=env.get("CREOSON_URL", cls.creoson_url).strip() or cls.creoson_url,
            creo_version=version if version > 0 else None,
            timeout=float(env.get("CREO_MCP_TIMEOUT", cls.timeout)),
            read_only=_flag(env, "CREO_MCP_READ_ONLY"),
            allow_dangerous=_flag(env, "CREO_MCP_ALLOW_DANGEROUS"),
            allow_system_mapkeys=_flag(env, "CREO_MCP_ALLOW_SYSTEM_MAPKEYS"),
            start_dir=env.get("CREO_START_DIR") or None,
            start_command=env.get("CREO_START_COMMAND", cls.start_command) or cls.start_command,
            max_tree_nodes=int(env.get("CREO_MCP_MAX_TREE_NODES", cls.max_tree_nodes)),
        )
