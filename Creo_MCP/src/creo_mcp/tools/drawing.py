"""Werkzeuge: Zeichnungen (anlegen, Ansichten, Blätter, Maßstab, Infos)."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from .common import READ, WRITE, ToolContext, ext_name, md_table

DRAWING_HELP = "Drawing name incl. .drw, e.g. 'abtriebsnabe.drw'. Default: the active drawing."


def register(server: MCPServer, ctx: ToolContext) -> None:
    @server.tool(name="creo_create_drawing", title="Create drawing", annotations=WRITE, structured_output=False)
    async def creo_create_drawing(
        template: Annotated[str, Field(description="Creo drawing template name, e.g. 'a3_drawing' or your school template (without .drw).", min_length=1)],
        model: Annotated[str | None, Field(description="Model to document, e.g. 'abtriebsnabe.prt'. Default: active model.")] = None,
        drawing: Annotated[str | None, Field(description="Name of the new drawing. Default: model name + .drw.")] = None,
        scale: Annotated[float, Field(description="Sheet scale, e.g. 1.0 for 1:1, 0.5 for 1:2.", gt=0)] = 1.0,
        sheet_format: Annotated[str | None, Field(description="Optional format file (.frm) for sheet 1, e.g. 'a3_iso'.")] = None,
        format_dir: Annotated[str | None, Field(description="Folder of the format file. Default: working directory.")] = None,
    ) -> str:
        """Create a new drawing (Zeichnung) for a model from a template and show it. Then add views with
        creo_add_drawing_view and export with creo_export(format='PDF')."""
        name = await ctx.ensure_open(model)
        data = await ctx.call(
            "drawing",
            "create",
            {"model": name, "drawing": ext_name(drawing, "drw") if drawing else None, "template": template, "scale": scale, "display": True, "activate": True},
        )
        drw = data.get("drawing")
        if sheet_format:
            await ctx.call("drawing", "set_sheet_format", {"drawing": drw, "sheet": 1, "file": sheet_format, "dirname": format_dir})
        return f"Created drawing {drw} for {name} (template {template}, scale {scale})."

    @server.tool(name="creo_add_drawing_view", title="Add drawing view", annotations=WRITE, structured_output=False)
    async def creo_add_drawing_view(
        view_name: Annotated[str, Field(description="Name of the new view, e.g. 'VORNE'.", min_length=1)],
        x: Annotated[float, Field(description="Sheet X position of the view centre (drawing units, mm for metric sheets).")],
        y: Annotated[float, Field(description="Sheet Y position of the view centre.")],
        kind: Annotated[Literal["general", "projection"], Field(description="'general' (from a named model view) or 'projection' (from a parent view).")] = "general",
        drawing: Annotated[str | None, Field(description=DRAWING_HELP)] = None,
        model_view: Annotated[str | None, Field(description="For 'general': saved model view, e.g. 'FRONT', 'TOP', 'RIGHT', 'DEFAULT'.")] = None,
        parent_view: Annotated[str | None, Field(description="For 'projection': name of the parent view.")] = None,
        model: Annotated[str | None, Field(description="Model shown in a general view. Default: the drawing's current model.")] = None,
        sheet: Annotated[int | None, Field(description="Sheet number. Default: current sheet.", ge=1)] = None,
        scale: Annotated[float | None, Field(description="View scale for general views. Default: sheet scale.", gt=0)] = None,
        style: Annotated[Literal["default", "follow_environment", "wireframe", "hidden_line", "no_hidden", "shaded"] | None, Field(description="Display style.")] = None,
    ) -> str:
        """Place a general or projection view on a drawing sheet."""
        point = {"x": x, "y": y}
        display: dict[str, Any] | None = {"style": style} if style else None
        if kind == "general":
            if not model_view:
                raise ToolError("model_view is required for general views (e.g. 'FRONT').")
            await ctx.call(
                "drawing",
                "create_gen_view",
                {"drawing": drawing, "view": view_name, "model_view": model_view, "model": model, "sheet": sheet, "point": point, "scale": scale, "display_data": display},
            )
        else:
            if not parent_view:
                raise ToolError("parent_view is required for projection views.")
            await ctx.call(
                "drawing",
                "create_proj_view",
                {"drawing": drawing, "view": view_name, "parent_view": parent_view, "sheet": sheet, "point": point, "display_data": display},
            )
        return f"Added {kind} view {view_name} at ({x}, {y})."

    @server.tool(name="creo_get_drawing_info", title="Drawing information", annotations=READ, structured_output=False)
    async def creo_get_drawing_info(drawing: Annotated[str | None, Field(description=DRAWING_HELP)] = None) -> str:
        """Sheets (size, scale, format), views (position, sheet, model) and models of a drawing."""
        base = {"drawing": drawing}
        sheets = (await ctx.call("drawing", "get_num_sheets", base)).get("num_sheets") or 1
        cur = (await ctx.try_call("drawing", "get_cur_sheet", base) or {}).get("sheet")
        sheet_rows = []
        for s in range(1, int(sheets) + 1):
            size = (await ctx.try_call("drawing", "get_sheet_size", {**base, "sheet": s}) or {}).get("size")
            scale = (await ctx.try_call("drawing", "get_sheet_scale", {**base, "sheet": s}) or {}).get("scale")
            fmt = (await ctx.try_call("drawing", "get_sheet_format", {**base, "sheet": s}) or {}).get("file")
            sheet_rows.append([s, size, scale, fmt, "←" if s == cur else ""])
        views = (await ctx.call("drawing", "list_view_details", base)).get("views") or []
        view_rows = [
            [v.get("name"), v.get("sheet"), (v.get("location") or {}).get("x"), (v.get("location") or {}).get("y"), v.get("view_model")]
            for v in views
        ]
        models = (await ctx.call("drawing", "list_models", base)).get("files") or []
        return (
            f"## Drawing {drawing or '(active)'}\n\nModels: {', '.join(models) or '(none)'}\n\n### Sheets\n\n"
            + md_table(["Sheet", "Size", "Scale", "Format", "Current"], sheet_rows)
            + "\n\n### Views\n\n"
            + md_table(["View", "Sheet", "X", "Y", "Model"], view_rows)
        )

    @server.tool(name="creo_edit_drawing", title="Edit drawing (sheets, scale, views)", annotations=WRITE, structured_output=False)
    async def creo_edit_drawing(
        action: Annotated[
            Literal["scale_sheet", "scale_view", "move_view", "delete_view", "add_sheet", "delete_sheet", "select_sheet", "set_format", "regenerate"],
            Field(description="What to do."),
        ],
        drawing: Annotated[str | None, Field(description=DRAWING_HELP)] = None,
        sheet: Annotated[int | None, Field(description="Sheet number (scale_sheet, delete_sheet, select_sheet, set_format).", ge=1)] = None,
        view: Annotated[str | None, Field(description="View name (scale_view, move_view, delete_view).")] = None,
        scale: Annotated[float | None, Field(description="Scale for scale_sheet/scale_view, e.g. 0.5 for 1:2.", gt=0)] = None,
        x: Annotated[float | None, Field(description="New X for move_view.")] = None,
        y: Annotated[float | None, Field(description="New Y for move_view.")] = None,
        format_file: Annotated[str | None, Field(description="Format file for set_format, e.g. 'a3_iso'.")] = None,
    ) -> str:
        """Change a drawing: sheet/view scale, move or delete views, add/delete/select sheets, set sheet format, regenerate."""
        base: dict[str, Any] = {"drawing": drawing}

        def need(**values: Any) -> None:
            missing = [k for k, v in values.items() if v is None]
            if missing:
                raise ToolError(f"Action '{action}' needs: {', '.join(missing)}.")

        if action == "scale_sheet":
            need(sheet=sheet, scale=scale)
            await ctx.call("drawing", "scale_sheet", {**base, "sheet": sheet, "scale": scale})
        elif action == "scale_view":
            need(view=view, scale=scale)
            await ctx.call("drawing", "scale_view", {**base, "view": view, "scale": scale})
        elif action == "move_view":
            need(view=view, x=x, y=y)
            await ctx.call("drawing", "set_view_loc", {**base, "view": view, "point": {"x": x, "y": y}})
        elif action == "delete_view":
            need(view=view)
            await ctx.call("drawing", "delete_view", {**base, "view": view})
        elif action == "add_sheet":
            await ctx.call("drawing", "add_sheet", base)
        elif action == "delete_sheet":
            need(sheet=sheet)
            await ctx.call("drawing", "delete_sheet", {**base, "sheet": sheet})
        elif action == "select_sheet":
            need(sheet=sheet)
            await ctx.call("drawing", "select_sheet", {**base, "sheet": sheet})
        elif action == "set_format":
            need(sheet=sheet, format_file=format_file)
            await ctx.call("drawing", "set_sheet_format", {**base, "sheet": sheet, "file": format_file})
        else:
            await ctx.call("drawing", "regenerate", base)
        return f"Drawing action '{action}' done."
