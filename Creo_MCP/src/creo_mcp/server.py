"""Aufbau des MCP-Servers."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from . import __version__, prompts
from .catalog import FunctionCatalog
from .client import CreosonClient
from .config import Settings
from .tools import MODULES
from .tools.common import ToolContext, md_table
from .tools.session import status_markdown
from .tools.tree_tools import model_tree_text

INSTRUCTIONS = """Controls PTC Creo Parametric (Creo 12) through CREOSON.
Start with creo_status. Models are addressed by file name incl. extension (teil.prt, baugruppe.asm, zeichnung.drw);
omit 'file' to use the active model. creo_get_model_tree shows the model tree (Stammbaum).
After changes, verify (creo_get_model_tree, creo_mass_properties). Anything without a dedicated tool:
creo_list_functions → creo_describe_function → creo_call. UI commands without API: creo_run_mapkey.
The free Creo API cannot create sketch-based features directly; use mapkeys or creo_import_geometry and say so."""


def build_server(settings: Settings | None = None, client: CreosonClient | None = None) -> MCPServer:
    settings = settings or Settings.from_env()
    client = client or CreosonClient(settings)
    ctx = ToolContext(settings=settings, client=client, catalog=FunctionCatalog.load())
    server = MCPServer("creo_mcp", title="Creo Parametric", instructions=INSTRUCTIONS, version=__version__)
    for module in MODULES:
        module.register(server, ctx)
    _register_resources(server, ctx)
    prompts.register(server)
    return server


def _register_resources(server: MCPServer, ctx: ToolContext) -> None:
    @server.resource("creo://session", name="session", title="Creo-Sitzung", mime_type="text/markdown")
    async def session_resource() -> str:
        """Verbindungs- und Sitzungsstatus."""
        return await status_markdown(ctx)

    @server.resource("creo://model-tree/{file}", name="model-tree", title="Modellbaum", mime_type="text/markdown")
    async def model_tree_resource(file: str) -> str:
        """Modellbaum eines Modells (z. B. creo://model-tree/abtriebsnabe.prt)."""
        return await model_tree_text(ctx, file, max_nodes=ctx.settings.max_tree_nodes)

    @server.resource("creo://functions", name="functions", title="CREOSON-Funktionen", mime_type="text/markdown")
    async def functions_resource() -> str:
        """Alle CREOSON-Funktionen."""
        rows = [[s.qualified_name, s.description] for s in ctx.catalog.all()]
        return md_table(["Function", "Description"], rows)
