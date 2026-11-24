"""Werkzeuge: Dateien und Modelle (öffnen, neu, speichern, regenerieren, Infos)."""

from __future__ import annotations

import glob
import os
from typing import Annotated, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from .common import DESTRUCTIVE, FILE_HELP, READ, SESSION, WRITE, ToolContext, clean_dirname, ext_name, md_table

DEFAULT_TEMPLATES = {"part": "mmns_part_solid_abs.prt", "assembly": "mmns_asm_design_abs.asm"}


def find_template_dir() -> str | None:
    """Sucht den Creo-Vorlagenordner (höchste installierte Version)."""
    patterns = [
        r"C:\Program Files\PTC\Creo *\Common Files\templates",
        r"C:\PTC\Creo *\Common Files\templates",
    ]
    hits: list[str] = []
    for pattern in patterns:
        hits.extend(glob.glob(pattern))
    hits = [h for h in hits if os.path.isdir(h)]
    return sorted(hits)[-1] if hits else None


def register(server: MCPServer, ctx: ToolContext) -> None:
    @server.tool(name="creo_list_models", title="List models in session", annotations=READ, structured_output=False)
    async def creo_list_models(
        pattern: Annotated[str | None, Field(description="Name filter with * wildcards, e.g. '*.prt'.")] = None,
    ) -> str:
        """List the models currently loaded in Creo's memory (session) and the active model."""
        files = (await ctx.call("file", "list", {"file": pattern})).get("files") or []
        active = (await ctx.try_call("file", "get_active") or {}).get("file")
        lines = [f"- {f}{'  ← active' if f == active else ''}" for f in files]
        return f"{len(files)} model(s) in session:\n" + ("\n".join(lines) or "(none)")

    @server.tool(name="creo_list_files", title="List files in working directory", annotations=READ, structured_output=False)
    async def creo_list_files(
        pattern: Annotated[str | None, Field(description="File name filter with * wildcards, e.g. '*.prt' or 'nabe*'.")] = None,
    ) -> str:
        """List files on disk in Creo's working directory (change it with creo_working_dir)."""
        files = (await ctx.call("creo", "list_files", {"filename": pattern})).get("filelist") or []
        pwd = (await ctx.call("creo", "pwd")).get("dirname")
        return f"{len(files)} file(s) in {pwd}:\n" + ("\n".join(f"- {f}" for f in files) or "(none)")

    @server.tool(name="creo_open_model", title="Open model", annotations=SESSION, structured_output=False)
    async def creo_open_model(
        file: Annotated[str, Field(description="File to open incl. extension, e.g. 'abtriebsnabe.prt'. Wildcards not allowed.")],
        dirname: Annotated[str | None, Field(description="Folder of the file. Default: Creo working directory.")] = None,
        generic: Annotated[str | None, Field(description="Generic name if 'file' is a family-table instance.")] = None,
        display: Annotated[bool, Field(description="Show the model in a Creo window.")] = True,
        activate: Annotated[bool, Field(description="Make it the active model.")] = True,
        new_window: Annotated[bool, Field(description="Open in a new window.")] = False,
    ) -> str:
        """Open a part/assembly/drawing in Creo (loads it into the session, shows and activates it)."""
        data = await ctx.call(
            "file",
            "open",
            {"file": file, "dirname": dirname, "generic": generic, "display": display, "activate": activate, "new_window": new_window},
        )
        return f"Opened {', '.join(data.get('files') or [file])} from {clean_dirname(data.get('dirname')) or '?'} (revision {data.get('revision', '?')})."

    @server.tool(name="creo_new_model", title="Create new part/assembly", annotations=WRITE, structured_output=False)
    async def creo_new_model(
        name: Annotated[str, Field(description="Name of the new model, e.g. 'abtriebsnabe' (extension is added).", min_length=1, max_length=31)],
        model_type: Annotated[Literal["part", "assembly"], Field(description="part (.prt) or assembly (.asm).")] = "part",
        template: Annotated[str | None, Field(description="Template model, default mmns_part_solid_abs.prt / mmns_asm_design_abs.asm (mm, N, s).")] = None,
        template_dir: Annotated[str | None, Field(description="Folder with the template. Default: CREO_TEMPLATE_DIR or the Creo installation's 'Common Files/templates'.")] = None,
        overwrite: Annotated[bool, Field(description="Replace an existing file with the same name in the working directory.")] = False,
    ) -> str:
        """Create a new part or assembly from a Creo start template (with default datum planes and CSYS),
        save it in the working directory and open it as active model. Model names may have max. 31 characters."""
        ext = "prt" if model_type == "part" else "asm"
        target = ext_name(name, ext).lower()
        tpl = ext_name(template or DEFAULT_TEMPLATES[model_type], ext).lower()
        tdir = template_dir or ctx.settings.template_dir or find_template_dir()
        if not tdir:
            raise ToolError(
                "Creo template folder not found. Set CREO_TEMPLATE_DIR (e.g. 'C:/Program Files/PTC/Creo 12.4.4.0/Common Files/templates') or pass template_dir."
            )
        existing = (await ctx.call("creo", "list_files", {"filename": target})).get("filelist") or []
        if existing and not overwrite:
            raise ToolError(f"{target} already exists in the working directory. Choose another name or set overwrite=true.")
        pwd = (await ctx.call("creo", "pwd")).get("dirname")
        await ctx.call("file", "open", {"file": tpl, "dirname": tdir, "display": False})
        await ctx.call("file", "rename", {"file": tpl, "new_name": target, "onlysession": True})
        await ctx.call("file", "backup", {"file": target, "target_dir": pwd})
        await ctx.call("file", "erase", {"file": target})
        await ctx.call("file", "open", {"file": target, "dirname": pwd, "display": True, "activate": True})
        return f"Created {target} from template {tpl} in {clean_dirname(pwd)} and opened it as active model."

    @server.tool(name="creo_save_model", title="Save model", annotations=WRITE, structured_output=False)
    async def creo_save_model(file: Annotated[str | None, Field(description=FILE_HELP)] = None) -> str:
        """Save a model to disk (creates a new version file, e.g. teil.prt.2)."""
        name = await ctx.ensure_open(file)
        await ctx.call("file", "save", {"file": name})
        return f"Saved {name}."

    @server.tool(name="creo_regenerate", title="Regenerate model", annotations=WRITE, structured_output=False)
    async def creo_regenerate(file: Annotated[str | None, Field(description=FILE_HELP)] = None) -> str:
        """Regenerate a model after changes (dimensions, parameters, relations, suppress/resume)."""
        name = await ctx.ensure_open(file)
        await ctx.call("file", "regenerate", {"file": name, "display": True})
        return f"Regenerated {name}."

    @server.tool(name="creo_close_model", title="Close model window", annotations=DESTRUCTIVE, structured_output=False)
    async def creo_close_model(
        file: Annotated[str | None, Field(description=FILE_HELP)] = None,
        erase_from_memory: Annotated[bool, Field(description="Also erase it from the session. UNSAVED CHANGES ARE LOST.")] = False,
    ) -> str:
        """Close the window of a model and optionally erase it from memory (unsaved changes are lost)."""
        name = await ctx.ensure_open(file)
        await ctx.call("file", "close_window", {"file": name})
        if erase_from_memory:
            await ctx.call("file", "erase", {"file": name})
            return f"Closed and erased {name} from the session."
        return f"Closed the window of {name} (still in session)."

    @server.tool(name="creo_rename_model", title="Rename model", annotations=WRITE, structured_output=False)
    async def creo_rename_model(
        new_name: Annotated[str, Field(description="New name incl. extension, e.g. 'antriebsnabe.prt'.")],
        file: Annotated[str | None, Field(description=FILE_HELP)] = None,
        only_in_session: Annotated[bool, Field(description="Rename only in memory, not the file on disk.")] = False,
    ) -> str:
        """Rename a model (like File > Manage File > Rename). With assemblies open, references are updated in session."""
        name = await ctx.ensure_open(file)
        data = await ctx.call("file", "rename", {"file": name, "new_name": new_name, "onlysession": only_in_session})
        return f"Renamed {name} → {data.get('file', new_name)}" + (" (only in session)." if only_in_session else ".")

    @server.tool(name="creo_get_model_info", title="Model information", annotations=READ, structured_output=False)
    async def creo_get_model_info(file: Annotated[str | None, Field(description=FILE_HELP)] = None) -> str:
        """Show file info (folder, revision), units, material and bounding box of a model."""
        name = await ctx.ensure_open(file)
        info = await ctx.call("file", "get_fileinfo", {"file": name})
        rows = [["File", info.get("file")], ["Folder", clean_dirname(info.get("dirname"))], ["Revision", info.get("revision")]]
        lu = await ctx.try_call("file", "get_length_units", {"file": name})
        mu = await ctx.try_call("file", "get_mass_units", {"file": name})
        rows.append(["Units", f"{(lu or {}).get('units', '?')} / {(mu or {}).get('units', '?')}"])
        if name.lower().endswith(".prt"):
            mat = await ctx.try_call("file", "get_cur_material", {"file": name})
            rows.append(["Material", (mat or {}).get("material") or "(none)"])
        bb = await ctx.try_call("geometry", "bound_box", {"file": name})
        if bb:
            rows.append(
                ["Bounding box", f"x {bb.get('xmin')}…{bb.get('xmax')}, y {bb.get('ymin')}…{bb.get('ymax')}, z {bb.get('zmin')}…{bb.get('zmax')}"]
            )
        return f"## {name}\n\n" + md_table(["Property", "Value"], rows)
