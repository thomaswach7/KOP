"""Werkzeuge: Funktionskatalog und generischer Aufruf jeder CREOSON-Funktion ("volle Kontrolle")."""

from __future__ import annotations

from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from ..errors import SafetyError
from ..mapkeys import normalize_mapkey
from ..safety import check_mapkey, classify
from .common import DESTRUCTIVE, READ, ToolContext, md_table, to_json


def register(server: MCPServer, ctx: ToolContext) -> None:
    @server.tool(name="creo_list_functions", title="List all CREOSON functions", annotations=READ, structured_output=False)
    async def creo_list_functions(
        command: Annotated[str | None, Field(description="Only this command group, e.g. 'drawing', 'familytable', 'layer', 'windchill'.")] = None,
        search: Annotated[str | None, Field(description="Text search in names/descriptions, e.g. 'sheet' or 'material'.")] = None,
    ) -> str:
        """List the 175 CREOSON functions (grouped by command) that creo_call can run, with a safety category."""
        specs = ctx.catalog.search(search) if search else ctx.catalog.all()
        if command:
            specs = [s for s in specs if s.command == command]
        rows = [[s.qualified_name, classify(s.command, s.function), s.description] for s in specs]
        return f"{len(rows)} function(s). Details: creo_describe_function.\n\n" + md_table(["Function", "Category", "Description"], rows)

    @server.tool(name="creo_describe_function", title="Describe a CREOSON function", annotations=READ, structured_output=False)
    async def creo_describe_function(
        command: Annotated[str, Field(description="Command group, e.g. 'feature'.")],
        function: Annotated[str, Field(description="Function, e.g. 'list'.")],
    ) -> str:
        """Show parameters, response fields, notes and an example of a CREOSON function (for creo_call)."""
        return ctx.catalog.describe(command, function)

    @server.tool(name="creo_call", title="Call any CREOSON function", annotations=DESTRUCTIVE, structured_output=False)
    async def creo_call(
        command: Annotated[str, Field(description="Command group, e.g. 'familytable', 'layer', 'note', 'view'.")],
        function: Annotated[str, Field(description="Function name, e.g. 'list'.")],
        data: Annotated[dict[str, Any] | None, Field(description="Function parameters as in creo_describe_function.")] = None,
        skip_validation: Annotated[bool, Field(description="Send even if parameters do not match the bundled spec.")] = False,
    ) -> str:
        """Run ANY CREOSON function (full control): family tables, layers, notes, views, simplified reps,
        Windchill, units, drawing symbols, … Check the parameters with creo_describe_function first.
        Returns the raw JSON 'data' of CREOSON. Safety rules (read-only mode, dangerous functions) apply."""
        if not skip_validation:
            problems = ctx.catalog.validate(command, function, data)
            if problems:
                raise ToolError("Invalid call: " + " ".join(problems) + " (see creo_describe_function, or skip_validation=true)")
        payload = dict(data or {})
        if (command, function) == ("interface", "mapkey") and isinstance(payload.get("script"), str):
            payload["script"] = normalize_mapkey(payload["script"])
            try:
                check_mapkey(payload["script"], ctx.settings.allow_system_mapkeys)
            except SafetyError as exc:
                raise ToolError(str(exc)) from exc
        result = await ctx.call(command, function, payload)
        return to_json(result)
