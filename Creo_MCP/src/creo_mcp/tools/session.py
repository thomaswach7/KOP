"""Werkzeuge: Sitzung, Verbindung, Arbeitsverzeichnis."""

from __future__ import annotations

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from .common import READ, SESSION, ToolContext, md_table


async def status_markdown(ctx: ToolContext) -> str:
    s = ctx.settings
    running = await ctx.try_call("connection", "is_creo_running")
    pwd = await ctx.try_call("creo", "pwd")
    active = await ctx.try_call("file", "get_active")
    models = await ctx.try_call("file", "list")
    if running is None:
        creo_state = "?"
    elif running.get("running"):
        creo_state = "yes"
    else:
        creo_state = "NO – use creo_connect(start_creo=true)"
    rows = [
        ["CREOSON", s.creoson_url],
        ["CREOSON reachable", "yes" if running is not None else "NO – start CREOSON, then run creo_doctor"],
        ["Creo running", creo_state],
        ["Creo version setting", s.creo_version or "not set"],
        ["Working directory", (pwd or {}).get("dirname", "?")],
        ["Active model", (active or {}).get("file", "(none)")],
        ["Models in session", ", ".join((models or {}).get("files") or []) or "(none)"],
        ["Read-only mode", "on" if s.read_only else "off"],
        ["Dangerous functions", "allowed" if s.allow_dangerous else "blocked"],
        ["@SYSTEM mapkeys", "allowed" if s.allow_system_mapkeys else "blocked"],
    ]
    return "## Creo-Status\n\n" + md_table(["Item", "Value"], rows)


def register(server: MCPServer, ctx: ToolContext) -> None:
    @server.tool(name="creo_status", title="Creo status", annotations=READ, structured_output=False)
    async def creo_status() -> str:
        """Show the connection state: CREOSON reachable?, Creo running?, working directory, active model,
        models in session and safety settings. Call this first in every Creo conversation."""
        return await status_markdown(ctx)

    @server.tool(name="creo_connect", title="Connect / start Creo", annotations=SESSION, structured_output=False)
    async def creo_connect(
        start_creo: Annotated[bool, Field(description="Start Creo via CREOSON's nitro_proe_remote.bat if it is not running.")] = False,
        start_dir: Annotated[str | None, Field(description="Folder containing nitro_proe_remote.bat (default: CREO_START_DIR).")] = None,
        retries: Annotated[int, Field(description="Connection retries after starting (10 s each).", ge=0, le=30)] = 5,
    ) -> str:
        """Connect to the running Creo session through CREOSON, optionally starting Creo first.
        Creo must have been started with CREOSON support (nitro_proe_remote.bat sets PRO_COMM_MSG_EXE)."""
        running = await ctx.call("connection", "is_creo_running")
        if not running.get("running") and start_creo:
            directory = start_dir or ctx.settings.start_dir
            if not directory:
                return (
                    "Creo is not running and no start folder is configured. Set CREO_START_DIR to the CREOSON folder "
                    "that contains nitro_proe_remote.bat (CreosonSetup creates it), or pass start_dir."
                )
            await ctx.call(
                "connection",
                "start_creo",
                {"start_dir": directory, "start_command": ctx.settings.start_command, "retries": retries},
            )
            running = await ctx.call("connection", "is_creo_running")
        if not running.get("running"):
            return "CREOSON is reachable, but Creo is not running/connected. Use creo_connect(start_creo=true) or start Creo via CreosonSetup."
        return await status_markdown(ctx)

    @server.tool(name="creo_working_dir", title="Get/set working directory", annotations=SESSION, structured_output=False)
    async def creo_working_dir(
        dirname: Annotated[str | None, Field(description="New working directory (absolute path). Omit to only read it.")] = None,
    ) -> str:
        """Read or change Creo's working directory (Arbeitsverzeichnis), where models are opened and saved."""
        if dirname:
            data = await ctx.call("creo", "cd", {"dirname": dirname})
        else:
            data = await ctx.call("creo", "pwd")
        return f"Working directory: {data.get('dirname')}"
