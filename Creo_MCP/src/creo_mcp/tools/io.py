"""Werkzeuge: Export, Import, Mapkeys."""

from __future__ import annotations

from typing import Annotated, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from ..errors import SafetyError
from ..mapkeys import normalize_mapkey
from ..safety import check_mapkey
from .common import DESTRUCTIVE, FILE_HELP, SESSION, WRITE, ToolContext

ExportFormat = Literal["PDF", "3DPDF", "STEP", "IGES", "DXF", "STL", "VRML", "NEUTRAL", "JPEG", "TIFF", "BMP", "EPS"]
_IMAGE = {"JPEG", "TIFF", "BMP", "EPS"}


def register(server: MCPServer, ctx: ToolContext) -> None:
    @server.tool(name="creo_export", title="Export (PDF, STEP, DXF, STL, image)", annotations=SESSION, structured_output=False)
    async def creo_export(
        format: Annotated[ExportFormat, Field(description="Target format. Drawings: PDF/DXF. Parts/assemblies: STEP/IGES/STL/VRML/NEUTRAL/3DPDF/images.")],  # noqa: A002
        file: Annotated[str | None, Field(description=FILE_HELP + " Drawings: e.g. 'abtriebsnabe.drw'.")] = None,
        filename: Annotated[str | None, Field(description="Output file name. Default: model name + extension.")] = None,
        dirname: Annotated[str | None, Field(description="Output folder. Default: working directory.")] = None,
        use_drawing_settings: Annotated[bool, Field(description="PDF of a drawing: stroke all fonts, grayscale.")] = False,
        geom_flags: Annotated[Literal["solids", "surfaces", "wireframe", "wireframe_surfaces", "quilts", "default"] | None, Field(description="STEP/IGES geometry type.")] = None,
    ) -> str:
        """Export a model or drawing to a file in the working directory (or dirname)."""
        name = await ctx.ensure_open(file)
        base = {"file": name, "filename": filename, "dirname": dirname}
        if format == "PDF":
            data = await ctx.call("interface", "export_pdf", {**base, "use_drawing_settings": use_drawing_settings})
        elif format == "3DPDF":
            data = await ctx.call("interface", "export_3dpdf", base)
        elif format in _IMAGE:
            if name.lower().endswith(".drw"):
                raise ToolError("Images of drawings are not supported by CREOSON; export the drawing as PDF instead.")
            data = await ctx.call("interface", "export_image", {**base, "type": format})
        else:
            data = await ctx.call("interface", "export_file", {**base, "type": format, "geom_flags": geom_flags})
        return f"Exported {name} as {format}: {data.get('dirname')}/{data.get('filename')}"

    @server.tool(name="creo_import_geometry", title="Import STEP/IGES as new model", annotations=WRITE, structured_output=False)
    async def creo_import_geometry(
        filename: Annotated[str, Field(description="Source file, e.g. 'nabe.step'.", min_length=1)],
        file_type: Annotated[Literal["STEP", "IGES", "NEUTRAL", "PV"], Field(description="Source format.")] = "STEP",
        dirname: Annotated[str | None, Field(description="Folder of the source file. Default: working directory.")] = None,
        new_name: Annotated[str | None, Field(description="Name of the new Creo model (without extension).")] = None,
        model_type: Annotated[Literal["prt", "asm"], Field(description="Create a part (single body) or an assembly.")] = "prt",
        open_model: Annotated[bool, Field(description="Show and activate the imported model.")] = True,
    ) -> str:
        """Import neutral geometry (STEP/IGES) as a new Creo part or assembly. The result has an import feature,
        not a parametric feature history."""
        data = await ctx.call(
            "interface",
            "import_file",
            {"type": file_type, "filename": filename, "dirname": dirname, "new_name": new_name, "new_model_type": model_type},
        )
        name = data.get("file")
        if open_model and name:
            await ctx.call("file", "open", {"file": name, "display": True, "activate": True})
        return f"Imported {filename} as {name}."

    @server.tool(name="creo_run_mapkey", title="Run mapkey / UI macro", annotations=DESTRUCTIVE, structured_output=False)
    async def creo_run_mapkey(
        script: Annotated[str, Field(description="Mapkey macro, e.g. '~ Command `ProCmdModelSave` ;'. A full config.pro definition (mapkey $F2 ... with mapkey(continued) lines) is accepted and normalized.", min_length=1)],
        delay_ms: Annotated[int, Field(description="Wait time after starting the mapkey in milliseconds.", ge=0, le=600000)] = 0,
    ) -> str:
        """Run a Creo mapkey macro: any menu command or dialog sequence that can be recorded in Creo
        (Datei > Optionen > Mapkeys > Aufzeichnen). This is the way to reach functions without API support,
        e.g. creating sketch-based features. @SYSTEM (OS commands) is blocked unless explicitly allowed.
        Verify the result afterwards (creo_get_model_tree), because mapkeys report no errors."""
        macro = normalize_mapkey(script)
        try:
            check_mapkey(macro, ctx.settings.allow_system_mapkeys)
        except SafetyError as exc:
            raise ToolError(str(exc)) from exc
        await ctx.call("interface", "mapkey", {"script": macro, "delay": delay_ms or None})
        return f"Mapkey sent to Creo ({len(macro)} characters). Check the result, e.g. with creo_get_model_tree."
