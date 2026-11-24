"""Modellbaum ("Stammbaum") aus CREOSON-Daten.

Quellen:
- `feature.list` (inc_unnamed, paths): alle sichtbaren KEs in Regenerationsreihenfolge mit ID/Nummer/Typ/Status.
  Bei Komponenten-KEs ist der Name der Dateiname der Komponente.
- `bom.get_paths` (paths): Baugruppenstruktur; `path[-1]` ist die Feature-ID des Komponenten-KEs
  in der übergeordneten Baugruppe → so werden Komponenten an der richtigen Stelle eingehängt.
- `feature.list_group_features` / `feature.list_pattern_features`: Mitglieder von Gruppen/Mustern.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from .errors import CreoMCPError
from .feattypes import DATUM_TYPES, head_kind, is_component, is_datum, same_type

CallFn = Callable[[str, str, dict[str, Any] | None], Awaitable[dict[str, Any]]]
Kind = Literal["model", "feature", "component", "group", "pattern"]

__all__ = ["DATUM_TYPES", "TreeNode", "TreeResult", "build_model_tree", "render_tree_markdown", "tree_to_dict"]
_SUPPRESSED = {"SUPPRESSED", "FAMILY_TABLE_SUPPRESSED", "SIMP_REP_SUPPRESSED", "PROGRAM_SUPPRESSED"}


@dataclass
class TreeNode:
    kind: Kind
    name: str
    type: str = ""
    status: str = "ACTIVE"
    feat_id: int | None = None
    feat_number: int | None = None
    file: str | None = None
    children: list[TreeNode] = field(default_factory=list)


@dataclass
class TreeResult:
    root: TreeNode
    node_count: int
    truncated: bool
    warnings: list[str]


def _pattern_members_by_id(feats: list[dict[str, Any]], index: int) -> list[dict[str, Any]] | None:
    """Mitglieder eines Musters ohne Namen aus der KE-Liste ableiten.

    So liefert echtes Creo 12 ein Muster: Musterkopf, direkt danach das Leit-KE (ältere ID), danach die Kopien mit
    den IDs Kopf-ID + 1, + 2, … und gleichem Typ wie das Leit-KE. Bei Lücken, Gruppen als Leit-KE oder weniger als
    zwei Mitgliedern wird nichts geraten.
    """
    head_id = feats[index].get("feat_id")
    if head_id is None or index + 1 >= len(feats):
        return None
    leader = feats[index + 1]
    if head_kind(leader.get("type")) is not None or is_component(leader.get("type")):
        return None
    members = [leader]
    expected = int(head_id) + 1
    for feat in feats[index + 2 :]:
        if feat.get("feat_id") != expected or not same_type(feat.get("type"), leader.get("type")):
            break
        members.append(feat)
        expected += 1
    return members if len(members) >= 2 else None


def _model_type(file: str) -> str:
    ext = file.rsplit(".", 1)[-1].lower() if "." in file else ""
    return {"prt": "PART", "asm": "ASSEMBLY", "drw": "DRAWING"}.get(ext, ext.upper())


class _Builder:
    def __init__(self, call: CallFn, *, include_features: bool, include_datums: bool, expand_components: bool,
                 max_depth: int | None, max_nodes: int):
        self.call = call
        self.include_features = include_features
        self.include_datums = include_datums
        self.expand_components = expand_components
        self.max_depth = max_depth
        self.max_nodes = max(1, max_nodes)
        self.count = 1  # Wurzel
        self.truncated = False
        self.warnings: list[str] = []
        self._features: dict[str, list[dict[str, Any]]] = {}
        self._members: dict[tuple[str, int], list[dict[str, Any]] | None] = {}

    def _take(self) -> bool:
        if self.count >= self.max_nodes:
            self.truncated = True
            return False
        self.count += 1
        return True

    async def features(self, file: str) -> list[dict[str, Any]]:
        if file not in self._features:
            data = await self.call("feature", "list", {"file": file, "inc_unnamed": True, "paths": True})
            self._features[file] = list(data.get("featlist") or [])
        return self._features[file]

    async def members(self, file: str, feats: list[dict[str, Any]], index: int, kind: Kind) -> list[dict[str, Any]] | None:
        head = feats[index]
        following = feats[index + 1] if index + 1 < len(feats) else None
        key = (file, int(head.get("feat_id") or 0))
        if key in self._members:
            return self._members[key]
        function, param = ("list_group_features", "group_name") if kind == "group" else ("list_pattern_features", "pattern_name")
        candidates = [head.get("name")]
        if kind == "pattern" and following is not None:
            candidates.append(following.get("name"))  # Fallback: Leit-KE des Musters
        result = None
        last_error = ""
        for name in [c for c in candidates if c]:
            try:
                data = await self.call("feature", function, {"file": file, param: name})
                result = list(data.get("featlist") or [])
                break
            except CreoMCPError as exc:
                last_error = str(exc)
        label = head.get("name") or f"id {head.get('feat_id')}"
        if result is None and kind == "pattern" and not head.get("name"):
            result = _pattern_members_by_id(feats, index)
            if result is not None:
                self.warnings.append(
                    f"{file}: Muster {label} hat keinen Namen – Mitglieder über die Feature-IDs zugeordnet "
                    f"(Leit-KE id {result[0].get('feat_id')} + {len(result) - 1} Kopien)."
                )
        if result is None:
            self.warnings.append(f"{file}: Mitglieder von {kind} '{label}' nicht lesbar ({last_error or 'ohne Namen'}); flach angezeigt.")
        self._members[key] = result
        return result

    def _visible(self, feat: dict[str, Any]) -> bool:
        if is_component(feat.get("type")):
            return True
        if not self.include_features:
            return False
        return self.include_datums or not is_datum(feat.get("type"))

    def _node(self, feat: dict[str, Any], kind: Kind) -> TreeNode:
        return TreeNode(
            kind=kind,
            name=str(feat.get("name") or ""),
            type=str(feat.get("type") or ""),
            status=str(feat.get("status") or "ACTIVE"),
            feat_id=feat.get("feat_id"),
            feat_number=feat.get("feat_number"),
            file=str(feat.get("name")) if kind == "component" else None,
        )

    async def expand(self, file: str, bom_node: dict[str, Any] | None, depth: int) -> list[TreeNode]:
        feats = await self.features(file)
        # Gruppen/Muster: Mitglieder ermitteln
        member_ids: set[int] = set()
        head_members: dict[int, list[dict[str, Any]]] = {}
        for index, feat in enumerate(feats):
            kind = head_kind(feat.get("type"))
            if kind is None or not self.include_features:
                continue
            members = await self.members(file, feats, index, kind)
            if members:
                ids = {int(m["feat_id"]) for m in members if m.get("feat_id") is not None}
                ids.discard(int(feat.get("feat_id") or -1))
                by_id = {int(f["feat_id"]): f for f in feats if f.get("feat_id") is not None}
                ordered = [by_id.get(i) or m for i, m in ((int(m["feat_id"]), m) for m in members if m.get("feat_id") is not None) if i in ids]
                head_members[int(feat["feat_id"])] = ordered
                member_ids |= ids

        bom_children = {}
        if bom_node:
            for child in bom_node.get("children") or []:
                path = child.get("path") or []
                if path:
                    bom_children[int(path[-1])] = child

        nodes: list[TreeNode] = []
        for feat in feats:
            fid = feat.get("feat_id")
            if fid is not None and int(fid) in member_ids:
                continue
            if not self._visible(feat):
                continue
            if not self._take():
                break
            ftype = feat.get("type")
            if is_component(ftype):
                nodes.append(await self._component(feat, bom_children, depth))
                continue
            kind = head_kind(ftype) if fid is not None and int(fid) in head_members else None
            node = self._node(feat, kind or "feature")
            if kind:
                for member in head_members[int(fid)]:
                    if not self._visible(member):
                        continue
                    if not self._take():
                        break
                    if is_component(member.get("type")):
                        node.children.append(await self._component(member, bom_children, depth))
                    else:
                        node.children.append(self._node(member, "feature"))
            nodes.append(node)
        return nodes

    async def _component(self, feat: dict[str, Any], bom_children: dict[int, dict[str, Any]], depth: int) -> TreeNode:
        """Komponenten-KE als Knoten; Inhalt (KEs/Unterkomponenten) wird rekursiv eingehängt."""
        node = self._node(feat, "component")
        fid = feat.get("feat_id")
        child_bom = bom_children.get(int(fid)) if fid is not None else None
        if child_bom is not None:
            node.file = child_bom.get("file") or node.file
        can_expand = self.expand_components and (self.max_depth is None or depth + 1 < self.max_depth)
        if can_expand and node.file:
            node.children = await self.expand(node.file, child_bom, depth + 1)
        return node


async def build_model_tree(
    call: CallFn,
    file: str | None = None,
    *,
    include_features: bool = True,
    include_datums: bool = True,
    expand_components: bool = True,
    max_depth: int | None = None,
    max_nodes: int = 400,
) -> TreeResult:
    """Baut den Modellbaum für `file` (oder das aktive Modell)."""
    if not file:
        file = str((await call("file", "get_active", None)).get("file") or "")
        if not file:
            raise CreoMCPError("No active model in Creo. Open a model first or pass 'file'.")
    builder = _Builder(
        call,
        include_features=include_features,
        include_datums=include_datums,
        expand_components=expand_components,
        max_depth=max_depth,
        max_nodes=max_nodes,
    )
    root = TreeNode(kind="model", name=file, type=_model_type(file), file=file)
    bom_root = None
    if file.lower().endswith(".asm"):
        bom = await call("bom", "get_paths", {"file": file, "paths": True, "skeletons": True})
        bom_root = bom.get("children") if isinstance(bom.get("children"), dict) else None
    if not file.lower().endswith(".drw"):
        root.children = await builder.expand(file, bom_root, 0)
    return TreeResult(root=root, node_count=builder.count, truncated=builder.truncated, warnings=builder.warnings)


def _marker(status: str) -> str:
    if status in _SUPPRESSED:
        return "⊘ "
    if status in ("INACTIVE", "UNREGENERATED"):
        return "⚠ "
    return ""


def _label(node: TreeNode) -> str:
    if node.kind == "model":
        return f"{node.name}  [{node.type}]"
    name = node.name or "(ohne Namen)"
    details = [node.type] if node.type else []
    if node.status and node.status != "ACTIVE":
        details.append(node.status)
    ident = []
    if node.feat_number is not None:
        ident.append(f"#{node.feat_number}")
    if node.feat_id is not None:
        ident.append(f"id {node.feat_id}")
    icon = {"component": "▣ ", "group": "▤ ", "pattern": "▦ "}.get(node.kind, "")
    suffix = f"  ({', '.join(ident)})" if ident else ""
    return f"{_marker(node.status)}{icon}{name}  [{', '.join(details)}]{suffix}"


def render_tree_markdown(result: TreeResult) -> str:
    lines = [_label(result.root)]

    def walk(node: TreeNode, prefix: str) -> None:
        for i, child in enumerate(node.children):
            last = i == len(node.children) - 1
            lines.append(f"{prefix}{'└── ' if last else '├── '}{_label(child)}")
            walk(child, prefix + ("    " if last else "│   "))

    walk(result.root, "")
    out = [f"**Modellbaum von {result.root.name}** – {result.node_count} Knoten", "", "```text", *lines, "```"]
    if result.truncated:
        out.append(
            f"\n_Baum bei {result.node_count} Knoten abgeschnitten. Für Details `file` auf eine Komponente setzen, "
            "`max_depth` verkleinern, `include_datums=false` oder `max_nodes` erhöhen._"
        )
    if result.warnings:
        out.append("\n**Warnungen:**")
        out.extend(f"- {w}" for w in result.warnings)
    out.append("\nLegende: ▣ Komponente · ▤ Gruppe · ▦ Muster · ⊘ unterdrückt · ⚠ inaktiv/nicht regeneriert")
    return "\n".join(out)


def tree_to_dict(result: TreeResult) -> dict[str, Any]:
    return {
        "root": asdict(result.root),
        "node_count": result.node_count,
        "truncated": result.truncated,
        "warnings": list(result.warnings),
    }
