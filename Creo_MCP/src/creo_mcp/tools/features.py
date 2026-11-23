"""Werkzeuge: KEs unterdrücken, fortsetzen, löschen, umbenennen."""

from __future__ import annotations

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from .common import DESTRUCTIVE, FILE_HELP, WRITE, ToolContext

NAMES_HELP = "Feature names (exact or with * wildcards), e.g. ['Passfedernut']."
IDS_HELP = "Feature IDs (see creo_list_features / creo_get_model_tree)."


def _require(names: list[str] | None, ids: list[int] | None) -> None:
    if not names and not ids:
        raise ToolError("Give 'names' or 'feat_ids'. Without them CREOSON would affect ALL features.")


def register(server: MCPServer, ctx: ToolContext) -> None:
    @server.tool(name="creo_suppress_features", title="Suppress features", annotations=WRITE, structured_output=False)
    async def creo_suppress_features(
        file: Annotated[str | None, Field(description=FILE_HELP)] = None,
        names: Annotated[list[str] | None, Field(description=NAMES_HELP)] = None,
        feat_ids: Annotated[list[int] | None, Field(description=IDS_HELP)] = None,
        clip: Annotated[bool, Field(description="Also suppress ALL features after the selected ones (Creo 'clip'). Usually false.")] = False,
        with_children: Annotated[bool, Field(description="Also suppress dependent child features.")] = True,
    ) -> str:
        """Suppress (unterdrücken) features. They stay in the model tree, marked suppressed, and can be resumed."""
        _require(names, feat_ids)
        model = await ctx.ensure_open(file)
        if names:
            await ctx.call("feature", "suppress", {"file": model, "names": names, "clip": clip, "with_children": with_children})
        for fid in feat_ids or []:
            await ctx.call("feature", "suppress", {"file": model, "feat_id": fid, "clip": clip, "with_children": with_children})
        return f"Suppressed in {model}: {', '.join([*(names or []), *map(str, feat_ids or [])])}."

    @server.tool(name="creo_resume_features", title="Resume features", annotations=WRITE, structured_output=False)
    async def creo_resume_features(
        file: Annotated[str | None, Field(description=FILE_HELP)] = None,
        names: Annotated[list[str] | None, Field(description=NAMES_HELP)] = None,
        feat_ids: Annotated[list[int] | None, Field(description=IDS_HELP)] = None,
        with_children: Annotated[bool, Field(description="Also resume child features.")] = True,
    ) -> str:
        """Resume (fortsetzen) suppressed features."""
        _require(names, feat_ids)
        model = await ctx.ensure_open(file)
        if names:
            await ctx.call("feature", "resume", {"file": model, "names": names, "with_children": with_children})
        for fid in feat_ids or []:
            await ctx.call("feature", "resume", {"file": model, "feat_id": fid, "with_children": with_children})
        return f"Resumed in {model}: {', '.join([*(names or []), *map(str, feat_ids or [])])}."

    @server.tool(name="creo_delete_features", title="Delete features", annotations=DESTRUCTIVE, structured_output=False)
    async def creo_delete_features(
        names: Annotated[list[str], Field(description=NAMES_HELP, min_length=1)],
        file: Annotated[str | None, Field(description=FILE_HELP)] = None,
        clip: Annotated[bool, Field(description="Also delete ALL features after the selected ones.")] = False,
    ) -> str:
        """Delete features permanently from the model (children may be deleted too). Prefer suppressing if unsure."""
        model = await ctx.ensure_open(file)
        await ctx.call("feature", "delete", {"file": model, "names": names, "clip": clip})
        return f"Deleted in {model}: {', '.join(names)}."

    @server.tool(name="creo_rename_feature", title="Rename feature", annotations=WRITE, structured_output=False)
    async def creo_rename_feature(
        new_name: Annotated[str, Field(description="New feature name, e.g. 'Grundkörper'.", min_length=1, max_length=80)],
        file: Annotated[str | None, Field(description=FILE_HELP)] = None,
        feat_id: Annotated[int | None, Field(description="ID of the feature (preferred, unique).")] = None,
        name: Annotated[str | None, Field(description="Current name of the feature (if no feat_id).")] = None,
    ) -> str:
        """Rename a feature (KE) in the model tree, e.g. 'Extrudieren 1' → 'Grundkörper'."""
        if feat_id is None and not name:
            raise ToolError("Give feat_id (preferred) or the current name.")
        model = await ctx.ensure_open(file)
        data = {"file": model, "new_name": new_name}
        if feat_id is not None:
            data["feat_id"] = feat_id
        else:
            data["name"] = name
        await ctx.call("feature", "rename", data)
        return f"Renamed feature {feat_id if feat_id is not None else name} in {model} → {new_name}."
