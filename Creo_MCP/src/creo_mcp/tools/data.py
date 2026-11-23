"""Werkzeuge: Parameter, Maße, Relationen, Masseneigenschaften, Material, Baugruppe/Stückliste."""

from __future__ import annotations

from collections import Counter
from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel, Field

from .common import FILE_HELP, READ, WRITE, ResponseFormat, ToolContext, md_table, to_json


class Point(BaseModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class Transform(BaseModel):
    """Lage einer Komponente: Ursprung + Drehwinkel (Grad) um X/Y/Z."""

    origin: Point = Field(default_factory=Point, description="Origin of the component in assembly coordinates.")
    x_rot: float = Field(0.0, description="Rotation about X in degrees.")
    y_rot: float = Field(0.0, description="Rotation about Y in degrees.")
    z_rot: float = Field(0.0, description="Rotation about Z in degrees.")


class Constraint(BaseModel):
    type: str = Field(description="Constraint type. CREOSON fully supports only 'csys' (coordinate system to coordinate system).")
    asmref: str | None = Field(None, description="Reference in the assembly, e.g. 'ASM_DEF_CSYS'.")
    compref: str | None = Field(None, description="Reference in the component, e.g. 'PRT_CSYS_DEF'.")
    offset: float | None = Field(None, description="Offset for offset constraints.")


def _infer_type(value: object) -> str:
    if isinstance(value, bool):
        return "BOOL"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "DOUBLE"
    return "STRING"


def _bom_rows(node: dict[str, Any], depth: int, rows: list[list[Any]], counts: Counter[str]) -> None:
    for child in node.get("children") or []:
        counts[child.get("file", "?")] += 1
        rows.append([child.get("seq_path"), "  " * depth + str(child.get("file")), (child.get("path") or [None])[-1]])
        _bom_rows(child, depth + 1, rows, counts)


def register(server: MCPServer, ctx: ToolContext) -> None:
    # -- Parameter ----------------------------------------------------------
    @server.tool(name="creo_list_parameters", title="List parameters", annotations=READ, structured_output=False)
    async def creo_list_parameters(
        file: Annotated[str | None, Field(description=FILE_HELP)] = None,
        name: Annotated[str | None, Field(description="Name filter with * wildcards, e.g. 'BENENN*'.")] = None,
        response_format: Annotated[ResponseFormat, Field(description="'markdown' or 'json'.")] = "markdown",
    ) -> str:
        """List model parameters (e.g. BENENNUNG, WERKSTOFF, DESCRIPTION) with type, value and designation."""
        model = await ctx.ensure_open(file)
        params = (await ctx.call("parameter", "list", {"file": model, "name": name})).get("paramlist") or []
        if response_format == "json":
            return to_json(params)
        rows = [[p.get("name"), p.get("type"), p.get("value"), "yes" if p.get("designate") else "", p.get("description")] for p in params]
        return f"**{model}** – {len(params)} parameter(s)\n\n" + md_table(["Name", "Type", "Value", "Designated", "Description"], rows)

    @server.tool(name="creo_set_parameter", title="Set parameter", annotations=WRITE, structured_output=False)
    async def creo_set_parameter(
        name: Annotated[str, Field(description="Parameter name, e.g. 'BENENNUNG'.", min_length=1)],
        value: Annotated[str | float | int | bool | None, Field(description="New value (None clears it).")],
        file: Annotated[str | None, Field(description=FILE_HELP)] = None,
        type: Annotated[Literal["STRING", "DOUBLE", "INTEGER", "BOOL", "NOTE"] | None, Field(description="Parameter type. Default: keep the existing type, or infer it from the value for new parameters.")] = None,  # noqa: A002
        designate: Annotated[bool | None, Field(description="Designate for PDM/BOM (true/false); omit to keep.")] = None,
        description: Annotated[str | None, Field(description="Parameter description; omit to keep.")] = None,
        no_create: Annotated[bool, Field(description="Fail instead of creating a new parameter.")] = False,
    ) -> str:
        """Create or change a model parameter (z. B. BENENNUNG, WERKSTOFF, POSITION)."""
        model = await ctx.ensure_open(file)
        if type is None:
            existing = (await ctx.call("parameter", "list", {"file": model, "name": name})).get("paramlist") or []
            match = next((p for p in existing if str(p.get("name", "")).upper() == name.upper()), None)
            type = match.get("type") if match else _infer_type(value)  # noqa: A001
        await ctx.call(
            "parameter",
            "set",
            {"file": model, "name": name, "type": type, "value": value, "designate": designate, "description": description, "no_create": no_create},
        )
        return f"Set {name} = {value!r} ({type}) in {model}."

    @server.tool(name="creo_delete_parameter", title="Delete parameter", annotations=WRITE, structured_output=False)
    async def creo_delete_parameter(
        name: Annotated[str, Field(description="Parameter name.", min_length=1)],
        file: Annotated[str | None, Field(description=FILE_HELP)] = None,
    ) -> str:
        """Delete a model parameter."""
        model = await ctx.ensure_open(file)
        await ctx.call("parameter", "delete", {"file": model, "name": name})
        return f"Deleted parameter {name} in {model}."

    # -- Maße -----------------------------------------------------------------
    @server.tool(name="creo_list_dimensions", title="List dimensions", annotations=READ, structured_output=False)
    async def creo_list_dimensions(
        file: Annotated[str | None, Field(description=FILE_HELP)] = None,
        name: Annotated[str | None, Field(description="Name filter with * wildcards, e.g. 'd*'.")] = None,
        detail: Annotated[bool, Field(description="Include type, text and tolerances (slower).")] = False,
        response_format: Annotated[ResponseFormat, Field(description="'markdown' or 'json'.")] = "markdown",
    ) -> str:
        """List the dimensions (Maße, e.g. d0, d1 or renamed ones) of a model with their values."""
        model = await ctx.ensure_open(file)
        fn = "list_detail" if detail else "list"
        dims = (await ctx.call("dimension", fn, {"file": model, "name": name})).get("dimlist") or []
        if response_format == "json":
            return to_json(dims)
        headers = ["Name", "Value", "Type", "Tolerance"] if detail else ["Name", "Value"]
        rows = []
        for d in dims:
            row = [d.get("name"), d.get("value")]
            if detail:
                tol = d.get("tolerance_type") or ""
                row += [d.get("dim_type"), tol]
            rows.append(row)
        return f"**{model}** – {len(dims)} dimension(s)\n\n" + md_table(headers, rows)

    @server.tool(name="creo_set_dimension", title="Set dimension", annotations=WRITE, structured_output=False)
    async def creo_set_dimension(
        name: Annotated[str, Field(description="Dimension name, e.g. 'd3'.", min_length=1)],
        value: Annotated[float, Field(description="New value in model units (e.g. mm).")],
        file: Annotated[str | None, Field(description=FILE_HELP)] = None,
        regenerate: Annotated[bool, Field(description="Regenerate the model afterwards.")] = True,
    ) -> str:
        """Change a dimension value and (by default) regenerate the model."""
        model = await ctx.ensure_open(file)
        await ctx.call("dimension", "set", {"file": model, "name": name, "value": value})
        if regenerate:
            await ctx.call("file", "regenerate", {"file": model})
        return f"Set {name} = {value} in {model}" + (" and regenerated." if regenerate else " (not regenerated).")

    # -- Relationen -------------------------------------------------------------
    @server.tool(name="creo_get_relations", title="Get relations", annotations=READ, structured_output=False)
    async def creo_get_relations(file: Annotated[str | None, Field(description=FILE_HELP)] = None) -> str:
        """Read the relations (Beziehungen) of a model."""
        model = await ctx.ensure_open(file)
        rels = (await ctx.call("file", "relations_get", {"file": model})).get("relations") or []
        return f"**{model}** – {len(rels)} relation line(s)\n\n```text\n" + "\n".join(rels) + "\n```"

    @server.tool(name="creo_set_relations", title="Set relations", annotations=WRITE, structured_output=False)
    async def creo_set_relations(
        relations: Annotated[list[str], Field(description="Complete new list of relation lines (replaces all), e.g. ['d3 = d1/2'].")],
        file: Annotated[str | None, Field(description=FILE_HELP)] = None,
        regenerate: Annotated[bool, Field(description="Regenerate afterwards.")] = True,
    ) -> str:
        """Replace ALL relations of a model with the given lines (read them first with creo_get_relations)."""
        model = await ctx.ensure_open(file)
        await ctx.call("file", "relations_set", {"file": model, "relations": relations})
        if regenerate:
            await ctx.call("file", "regenerate", {"file": model})
        return f"Set {len(relations)} relation line(s) in {model}."

    # -- Masseneigenschaften / Material -------------------------------------------
    @server.tool(name="creo_mass_properties", title="Mass properties (volume, mass)", annotations=READ, structured_output=False)
    async def creo_mass_properties(
        file: Annotated[str | None, Field(description=FILE_HELP)] = None,
        response_format: Annotated[ResponseFormat, Field(description="'markdown' or 'json'.")] = "markdown",
    ) -> str:
        """Volume, mass, density, surface area and centre of gravity – e.g. to compare with a target volume (Sollvolumen)."""
        model = await ctx.ensure_open(file)
        mp = await ctx.call("file", "massprops", {"file": model})
        if response_format == "json":
            return to_json(mp)
        lu = ((await ctx.try_call("file", "get_length_units", {"file": model})) or {}).get("units") or "?"
        mu = ((await ctx.try_call("file", "get_mass_units", {"file": model})) or {}).get("units") or "?"
        cg = mp.get("ctr_grav") or {}
        rows = [
            ["Volume", f"{mp.get('volume', 0):.3f} {lu}³"],
            ["Mass", f"{mp.get('mass', 0):.6g} {mu}"],
            ["Density", f"{mp.get('density', 0):.6g} {mu}/{lu}³"],
            ["Surface area", f"{mp.get('surface_area', 0):.3f} {lu}²"],
            ["Centre of gravity", f"x={cg.get('x')}, y={cg.get('y')}, z={cg.get('z')}"],
        ]
        return f"## Mass properties of {model}\n\n" + md_table(["Property", "Value"], rows)

    @server.tool(name="creo_set_material", title="Assign material", annotations=WRITE, structured_output=False)
    async def creo_set_material(
        material: Annotated[str, Field(description="Material name, e.g. 'STEEL' or a material file name without .mtl.", min_length=1)],
        file: Annotated[str | None, Field(description=FILE_HELP)] = None,
        load_from_dir: Annotated[str | None, Field(description="Folder of the .mtl file if it is not loaded yet (default: pro_material_dir).")] = None,
    ) -> str:
        """Assign a material to a part (loads the material file first if needed)."""
        model = await ctx.ensure_open(file)
        loaded = (await ctx.call("file", "list_materials", {"file": model})).get("materials") or []
        if material.lower() not in [m.lower() for m in loaded]:
            await ctx.call("file", "load_material_file", {"file": model, "material": material, "dirname": load_from_dir})
        await ctx.call("file", "set_cur_material", {"file": model, "material": material})
        return f"Material of {model} set to {material}."

    # -- Baugruppe ----------------------------------------------------------------
    @server.tool(name="creo_assemble_component", title="Assemble component", annotations=WRITE, structured_output=False)
    async def creo_assemble_component(
        file: Annotated[str, Field(description="Component to insert, e.g. 'scheibe.prt'.")],
        into_asm: Annotated[str | None, Field(description="Target assembly. Default: active model.")] = None,
        constraints: Annotated[list[Constraint] | None, Field(description="Constraints. Reliable: [{type:'csys', asmref:'ASM_DEF_CSYS', compref:'PRT_CSYS_DEF'}].")] = None,
        transform: Annotated[Transform | None, Field(description="Fixed placement (origin + rotations) instead of constraints.")] = None,
        dirname: Annotated[str | None, Field(description="Folder of the component file. Default: working directory.")] = None,
        package: Annotated[bool, Field(description="Insert as packaged (unconstrained) component.")] = False,
    ) -> str:
        """Insert a component into an assembly. CREOSON supports reliably only CSYS-to-CSYS constraints or a fixed
        transform; for mate/align use creo_run_mapkey or place the component in the Creo UI."""
        data: dict[str, Any] = {"file": file, "into_asm": into_asm, "dirname": dirname, "package_assembly": package or None}
        if constraints:
            data["constraints"] = [c.model_dump(exclude_none=True) for c in constraints]
        if transform:
            data["transform"] = transform.model_dump()
        result = await ctx.call("file", "assemble", data)
        return f"Assembled {file} (feature id {result.get('featureid')}) into {into_asm or 'the active assembly'}."

    @server.tool(name="creo_get_bom", title="Bill of materials (Stückliste)", annotations=READ, structured_output=False)
    async def creo_get_bom(
        file: Annotated[str | None, Field(description="Assembly. " + FILE_HELP)] = None,
        top_level_only: Annotated[bool, Field(description="Only direct components.")] = False,
        transforms: Annotated[bool, Field(description="Include the 3D placement of each component (JSON only).")] = False,
        response_format: Annotated[ResponseFormat, Field(description="'markdown' or 'json'.")] = "markdown",
    ) -> str:
        """Assembly structure with component paths and a quantity table (Stückliste) per model file."""
        model = await ctx.ensure_open(file)
        bom = await ctx.call("bom", "get_paths", {"file": model, "paths": True, "top_level": top_level_only, "get_transforms": transforms})
        if response_format == "json":
            return to_json(bom)
        rows: list[list[Any]] = []
        counts: Counter[str] = Counter()
        _bom_rows(bom.get("children") or {}, 0, rows, counts)
        qty = sorted(counts.items())
        return (
            f"## Structure of {model}\n\n" + md_table(["Seq", "Component", "Feature ID"], rows)
            + "\n\n## Quantities (all levels)\n\n" + md_table(["File", "Qty"], [list(q) for q in qty])
        )
