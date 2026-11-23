"""Werkzeuge: Modellbaum ("Stammbaum") und KE-Liste."""

from __future__ import annotations

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from ..tree import DATUM_TYPES, build_model_tree, render_tree_markdown, tree_to_dict
from .common import FILE_HELP, READ, ResponseFormat, ToolContext, md_table, paginate, to_json


async def model_tree_text(ctx: ToolContext, file: str | None, **options: object) -> str:
    name = await ctx.ensure_open(file)
    result = await build_model_tree(ctx.call, name, **options)  # type: ignore[arg-type]
    return render_tree_markdown(result)


def register(server: MCPServer, ctx: ToolContext) -> None:
    @server.tool(name="creo_get_model_tree", title="Model tree (Stammbaum)", annotations=READ, structured_output=False)
    async def creo_get_model_tree(
        file: Annotated[str | None, Field(description=FILE_HELP + " Unloaded files are opened in the background.")] = None,
        include_features: Annotated[bool, Field(description="Show features (KEs). False = assembly structure only.")] = True,
        include_datums: Annotated[bool, Field(description="Show datum planes/axes/points/CSYS/curves.")] = True,
        expand_components: Annotated[bool, Field(description="Expand the content of components.")] = True,
        max_depth: Annotated[int | None, Field(description="Max. assembly levels to expand (1 = only top-level components, no content).", ge=1, le=50)] = None,
        max_nodes: Annotated[int | None, Field(description="Node limit (default 400) to protect the context.", ge=5, le=5000)] = None,
        response_format: Annotated[ResponseFormat, Field(description="'markdown' (tree drawing) or 'json' (full data).")] = "markdown",
    ) -> str:
        """Return the Creo model tree of a part or assembly like in the Creo UI: components (sub-assemblies, parts)
        in assembly order, features (KEs) in regeneration order with number, ID, type and status, groups and
        patterns with their members. Suppressed features are marked ⊘. Use it to inspect how a model is built."""
        name = await ctx.ensure_open(file)
        result = await build_model_tree(
            ctx.call,
            name,
            include_features=include_features,
            include_datums=include_datums,
            expand_components=expand_components,
            max_depth=max_depth,
            max_nodes=max_nodes or ctx.settings.max_tree_nodes,
        )
        if response_format == "json":
            return to_json(tree_to_dict(result))
        return render_tree_markdown(result)

    @server.tool(name="creo_list_features", title="List features", annotations=READ, structured_output=False)
    async def creo_list_features(
        file: Annotated[str | None, Field(description=FILE_HELP)] = None,
        name: Annotated[str | None, Field(description="Feature name filter with * wildcards, e.g. 'Bohrung*'.")] = None,
        type: Annotated[str | None, Field(description="Feature type filter, e.g. 'HOLE', 'CUT', 'PROTRUSION', 'DATUM PLANE', 'COMPONENT'.")] = None,  # noqa: A002
        status: Annotated[str | None, Field(description="Status filter, e.g. 'ACTIVE' or 'SUPPRESSED'.")] = None,
        include_datums: Annotated[bool, Field(description="Include datum features.")] = True,
        include_unnamed: Annotated[bool, Field(description="Include features without a name.")] = True,
        limit: Annotated[int, Field(description="Max. rows to return.", ge=1, le=1000)] = 100,
        offset: Annotated[int, Field(description="Rows to skip (pagination).", ge=0)] = 0,
        response_format: Annotated[ResponseFormat, Field(description="'markdown' table or 'json'.")] = "markdown",
    ) -> str:
        """Flat list of the features (KEs) of one model in regeneration order with number, ID, type and status."""
        model = await ctx.ensure_open(file)
        data = await ctx.call(
            "feature",
            "list",
            {"file": model, "name": name, "type": type, "status": status, "inc_unnamed": include_unnamed, "paths": True},
        )
        feats = [f for f in data.get("featlist") or [] if include_datums or str(f.get("type", "")).upper() not in DATUM_TYPES]
        page = paginate(feats, limit, offset)
        if response_format == "json":
            return to_json(page)
        rows = [[f.get("feat_number"), f.get("feat_id"), f.get("name") or "(ohne Namen)", f.get("type"), f.get("status")] for f in page["items"]]
        more = f"\n\nMore rows: call again with offset={page['next_offset']}." if page["has_more"] else ""
        return f"**{model}** – {page['total']} features (showing {page['count']} from {offset})\n\n" + md_table(
            ["#", "ID", "Name", "Type", "Status"], rows
        ) + more
