"""Werkzeuge: Diagnose und VB-API-Zusatzfunktionen (Eltern/Kind-Beziehungen)."""

from __future__ import annotations

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from ..doctor import render_checks, run_diagnostics
from ..errors import CreoMCPError
from ..vbapi import VbApiSession
from .common import FILE_HELP, READ, ResponseFormat, ToolContext, md_table, to_json


def _vbapi(ctx: ToolContext) -> VbApiSession:
    if ctx.vbapi is None:
        try:
            ctx.vbapi = VbApiSession.connect()
        except CreoMCPError as exc:
            raise ToolError(str(exc)) from exc
    return ctx.vbapi


def register(server: MCPServer, ctx: ToolContext) -> None:
    @server.tool(name="creo_doctor", title="Diagnose connection paths", annotations=READ, structured_output=False)
    async def creo_doctor() -> str:
        """Check every connection path to Creo on this PC (CREOSON server, Creo session, Creo version setting,
        Creo installation, VB API registration, start script) and say exactly what to fix."""
        return render_checks(await run_diagnostics(ctx.settings, ctx.client))

    @server.tool(name="creo_feature_relations", title="Feature parents/children (VB API)", annotations=READ, structured_output=False)
    async def creo_feature_relations(
        file: Annotated[str | None, Field(description=FILE_HELP + " Must be open in Creo.")] = None,
        feat_id: Annotated[int | None, Field(description="Feature ID. Omit to get the dependency list of all features.")] = None,
        response_format: Annotated[ResponseFormat, Field(description="'markdown' or 'json'.")] = "markdown",
    ) -> str:
        """Parent/child references of features (which feature depends on which) – the genealogy part of the
        model tree. Needs the Creo VB API on Windows (see creo_doctor)."""
        api = _vbapi(ctx)
        try:
            if feat_id is not None:
                rel = api.feature_relations(file, feat_id)
                if response_format == "json":
                    return to_json(rel)
                f = rel["feature"]
                rows = [["parent", p["feat_id"], p["name"], p["type"], p["status"]] for p in rel["parents"]]
                rows += [["child", c["feat_id"], c["name"], c["type"], c["status"]] for c in rel["children"]]
                return f"**{f['name'] or '(ohne Namen)'}** (id {f['feat_id']}, {f['type']})\n\n" + md_table(["Relation", "ID", "Name", "Type", "Status"], rows)
            graph = api.dependency_graph(file)
        except CreoMCPError as exc:
            raise ToolError(str(exc)) from exc
        except Exception as exc:  # COM-Fehler → Verbindung neu aufbauen lassen
            ctx.vbapi = None
            raise ToolError(f"VB API call failed ({exc}); the connection will be re-established on the next call.") from exc
        if response_format == "json":
            return to_json(graph)
        rows = [[g["number"], g["feat_id"], g["name"] or "(ohne Namen)", g["type"], ", ".join(map(str, g["parents"]))] for g in graph]
        return md_table(["#", "ID", "Name", "Type", "Parent IDs"], rows)
