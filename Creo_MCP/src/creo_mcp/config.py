"""Konfiguration des Creo-MCP-Servers über Umgebungsvariablen."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

_TRUE = {"1", "true", "yes", "ja", "on"}


def _flag(env: Mapping[str, str], key: str) -> bool:
    return env.get(key, "").strip().lower() in _TRUE


def _number(env: Mapping[str, str], key: str, default: float, cast: type) -> float:
    raw = (env.get(key) or "").strip()
    if not raw:
        return default
    try:
        return cast(raw)
    except ValueError:
        raise ValueError(f"Environment variable {key} must be a number, got {raw!r}.") from None


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
    template_dir: str | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if env is None else env
        version = int(_number(env, "CREO_VERSION", 12, int))
        return cls(
            creoson_url=env.get("CREOSON_URL", cls.creoson_url).strip() or cls.creoson_url,
            creo_version=version if version > 0 else None,
            timeout=float(_number(env, "CREO_MCP_TIMEOUT", cls.timeout, float)),
            read_only=_flag(env, "CREO_MCP_READ_ONLY"),
            allow_dangerous=_flag(env, "CREO_MCP_ALLOW_DANGEROUS"),
            allow_system_mapkeys=_flag(env, "CREO_MCP_ALLOW_SYSTEM_MAPKEYS"),
            start_dir=env.get("CREO_START_DIR") or None,
            start_command=env.get("CREO_START_COMMAND", cls.start_command) or cls.start_command,
            max_tree_nodes=int(_number(env, "CREO_MCP_MAX_TREE_NODES", cls.max_tree_nodes, int)),
            template_dir=env.get("CREO_TEMPLATE_DIR") or None,
        )
