"""Katalog aller CREOSON-Funktionen.

Die JSON-Spezifikationen stammen unverändert aus CREOSON 3.0.2
(`creoson-server/web/assets/creoson_stuff/jsonSpecs`, MIT-Lizenz, siehe specs/LICENSE-CREOSON.txt).
Sie treiben die Parameterprüfung, die Hilfe-Werkzeuge und den generischen Aufruf.
"""

from __future__ import annotations

import difflib
import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Any

_MAX_EXAMPLE_CHARS = 1500


@dataclass(frozen=True)
class ParamSpec:
    name: str
    type: str
    description: str = ""
    default: str | None = None
    required: bool = False
    valid_values: tuple[str, ...] = ()

    def enum(self) -> tuple[str, ...]:
        """Erlaubte Werte – nur wenn die Liste aus einfachen Wörtern besteht (keine Beschreibungen) und Text-Typ."""
        if self.type != "string" or not self.valid_values:
            return ()
        if any(" " in v for v in self.valid_values):
            return ()
        return self.valid_values


@dataclass(frozen=True)
class FunctionSpec:
    command: str
    function: str
    description: str
    notes: tuple[str, ...]
    request: tuple[ParamSpec, ...]
    response: tuple[ParamSpec, ...]
    examples: tuple[dict[str, Any], ...]

    @property
    def qualified_name(self) -> str:
        return f"{self.command}.{self.function}"


@dataclass(frozen=True)
class ObjectSpec:
    name: str
    description: str
    notes: tuple[str, ...]
    fields: tuple[ParamSpec, ...]


def _params(raw: list[dict[str, Any]] | None) -> tuple[ParamSpec, ...]:
    return tuple(
        ParamSpec(
            name=p["name"],
            type=p.get("type", ""),
            description=p.get("description", ""),
            default=p.get("default"),
            required=bool(p.get("required")),
            valid_values=tuple(v.strip() for v in str(p.get("valid_values") or "").split(",") if v.strip()),
        )
        for p in raw or []
    )


def _type_ok(expected: str, value: Any) -> bool:
    """Prüft einen Wert gegen einen CREOSON-Typnamen (tolerant wie CREOSON selbst)."""
    if value is None:
        return True
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool) or (isinstance(value, str) and value.lower() in {"true", "false"})
    if expected == "integer":
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return True
        return isinstance(value, str) and value.strip().lstrip("-").isdigit()
    if expected == "double":
        if isinstance(value, bool):
            return False
        if isinstance(value, (int, float)):
            return True
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False
    if expected == "array:string":
        return isinstance(value, list) and all(isinstance(v, str) for v in value)
    if expected == "array:integer":
        return isinstance(value, list) and all(isinstance(v, int) and not isinstance(v, bool) for v in value)
    if expected.startswith("object_array"):
        return isinstance(value, list) and all(isinstance(v, dict) for v in value)
    if expected.startswith("object"):
        return isinstance(value, dict)
    return True  # "depends on data type" und Unbekanntes


class FunctionCatalog:
    """Nachschlagewerk für alle CREOSON-Funktionen und Datenobjekte."""

    def __init__(self, functions: dict[tuple[str, str], FunctionSpec], objects: dict[str, ObjectSpec]):
        self._functions = functions
        self._objects = objects

    @classmethod
    def load(cls) -> FunctionCatalog:
        return _load_catalog()

    def commands(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for command, function in sorted(self._functions):
            out.setdefault(command, []).append(function)
        return out

    def all(self) -> list[FunctionSpec]:
        return [self._functions[k] for k in sorted(self._functions)]

    def get(self, command: str, function: str) -> FunctionSpec | None:
        return self._functions.get((command, function))

    def get_object(self, name: str) -> ObjectSpec | None:
        return self._objects.get(name)

    def search(self, text: str) -> list[FunctionSpec]:
        needle = text.lower()
        return [
            s
            for s in self.all()
            if needle in s.qualified_name.lower() or needle in s.description.lower()
        ]

    def unknown_function_hint(self, command: str, function: str) -> str:
        cmds = self.commands()
        if command not in cmds:
            close = difflib.get_close_matches(command, list(cmds), n=3)
            hint = f" Did you mean: {', '.join(close)}?" if close else ""
            return f"Unknown CREOSON command '{command}'.{hint} Commands: {', '.join(sorted(cmds))}."
        close = difflib.get_close_matches(function, cmds[command], n=3, cutoff=0.4)
        hint = f" Did you mean: {', '.join(close)}?" if close else ""
        return f"Unknown function '{command}.{function}'.{hint} Available: {', '.join(cmds[command])}."

    def validate(self, command: str, function: str, data: dict[str, Any] | None) -> list[str]:
        spec = self.get(command, function)
        if spec is None:
            return [self.unknown_function_hint(command, function)]
        data = data or {}
        problems = [
            f"Parameter '{p.name}' is required for {spec.qualified_name}."
            for p in spec.request
            if p.required and data.get(p.name) is None
        ]
        problems += self._check_fields(spec.qualified_name, spec.request, data)
        return problems

    def _check_fields(self, where: str, fields: tuple[ParamSpec, ...], data: dict[str, Any]) -> list[str]:
        problems: list[str] = []
        known = {p.name: p for p in fields}
        for key, value in data.items():
            param = known.get(key)
            if param is None:
                allowed = ", ".join(known) or "(none)"
                problems.append(f"Unknown parameter '{key}' for {where}. Allowed: {allowed}.")
                continue
            if not _type_ok(param.type, value):
                problems.append(f"Parameter '{key}' of {where} must be of type {param.type}, got {value!r}.")
                continue
            enum = param.enum()
            if enum and isinstance(value, str) and value.lower() not in {e.lower() for e in enum}:
                problems.append(f"Parameter '{key}' of {where} must be one of {', '.join(enum)}; got {value!r}.")
            if ":" in param.type and value is not None:
                obj = self.get_object(param.type.split(":", 1)[1])
                if obj is not None:
                    items = value if isinstance(value, list) else [value]
                    for item in items:
                        if isinstance(item, dict):
                            problems += self._check_fields(f"{where}.{key}", obj.fields, item)
        return problems

    def describe(self, command: str, function: str) -> str:
        spec = self.get(command, function)
        if spec is None:
            return self.unknown_function_hint(command, function)
        lines = [f"### {spec.qualified_name}", "", spec.description, ""]
        if spec.notes:
            lines.append("**Notes:**")
            lines.extend(f"- {n}" for n in spec.notes)
            lines.append("")
        lines.append("**Request parameters (data):**")
        if spec.request:
            lines.append("| Name | Type | Default | Description |")
            lines.append("|---|---|---|---|")
            for p in spec.request:
                lines.append(f"| {p.name} | {p.type} | {p.default or ''} | {p.description} |")
        else:
            lines.append("(none)")
        lines.append("")
        lines.append("**Response fields (data):**")
        if spec.response:
            for p in spec.response:
                lines.append(f"- `{p.name}` ({p.type}): {p.description}")
        else:
            lines.append("(none)")
        object_types = {
            p.type.split(":", 1)[1] for p in (*spec.request, *spec.response) if ":" in p.type and "object" in p.type
        }
        for name in sorted(object_types):
            obj = self.get_object(name)
            if obj:
                fields = ", ".join(f"{f.name} ({f.type})" for f in obj.fields)
                lines.append(f"- Object `{name}`: {fields}")
        if spec.examples:
            ex = spec.examples[0]
            req = json.dumps((ex.get("request") or {}).get("data") or {}, ensure_ascii=False)
            res = json.dumps((ex.get("response") or {}).get("data") or {}, ensure_ascii=False)
            lines += ["", "**Example request data:**", f"```json\n{req[:_MAX_EXAMPLE_CHARS]}\n```"]
            lines += ["**Example response data:**", f"```json\n{res[:_MAX_EXAMPLE_CHARS]}\n```"]
        return "\n".join(lines)


@lru_cache(maxsize=1)
def _load_catalog() -> FunctionCatalog:
    functions: dict[tuple[str, str], FunctionSpec] = {}
    objects: dict[str, ObjectSpec] = {}
    spec_dir = resources.files("creo_mcp") / "specs"
    for entry in spec_dir.iterdir():
        if not entry.name.endswith(".json"):
            continue
        raw = json.loads(entry.read_text(encoding="utf-8"))
        if "spec" in raw:
            s = raw["spec"]
            fs = FunctionSpec(
                command=s["command"],
                function=s["function"],
                description=s.get("function_description", ""),
                notes=tuple(s.get("notes") or ()),
                request=_params(s.get("request")),
                response=_params(s.get("response")),
                examples=tuple(raw.get("examples") or ()),
            )
            functions[(fs.command, fs.function)] = fs
        elif "object_name" in raw:
            objects[raw["object_name"]] = ObjectSpec(
                name=raw["object_name"],
                description=raw.get("description", ""),
                notes=tuple(raw.get("notes") or ()),
                fields=_params(raw.get("data")),
            )
    return FunctionCatalog(functions, objects)
