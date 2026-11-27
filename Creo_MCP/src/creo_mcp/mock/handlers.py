"""CREOSON-Protokoll-Nachbildung: verarbeitet eine JSON-Anfrage gegen den MockCreo-Zustand."""

from __future__ import annotations

import copy
import fnmatch
import uuid
from collections.abc import Callable
from typing import Any

from ..catalog import FunctionCatalog
from ..feattypes import head_kind, is_datum
from .state import MDrawing, MFeature, MModel, MockCreo, MView, norm_dir

TOOLKIT_ERROR = "A Pro/TOOLKIT error has occurred: {}.  Check your model/drawing for accuracy."
TEMPLATE_VIEWS = ("FRONT", "TOP", "RIGHT")  # braucht die Creo-Vorlage a3_drawing im Modell


class MockError(Exception):
    pass


Handler = Callable[[MockCreo, dict[str, Any]], dict[str, Any] | None]
_HANDLERS: dict[tuple[str, str], Handler] = {}
_NO_SESSION_NEEDED = {("connection", "connect"), ("connection", "is_creo_running"), ("connection", "kill_creo")}
_NO_CREO_NEEDED = {"connection", "server"}


def handler(command: str, function: str) -> Callable[[Handler], Handler]:
    def deco(fn: Handler) -> Handler:
        _HANDLERS[(command, function)] = fn
        return fn

    return deco


def handle_request(state: MockCreo, payload: dict[str, Any]) -> dict[str, Any]:
    command = payload.get("command")
    function = payload.get("function")
    data = payload.get("data") or {}
    if not command:
        return _error("Request is missing the 'command' property")
    if not function:
        return _error("Request is missing the 'function' property")
    state.calls.append((command, function, copy.deepcopy(data)))
    session_id = payload.get("sessionId")
    if (command, function) not in _NO_SESSION_NEEDED and session_id not in state.sessions:
        return _error("No session found")
    if not state.creo_running and command not in _NO_CREO_NEEDED and (command, function) != ("creo", "set_creo_version"):
        return _error("Unable to connect to Creo through J-Link")
    if (command, function) in state.fail_functions:
        return _error(state.fail_functions[(command, function)])
    problems = FunctionCatalog.load().validate(command, function, data)
    if problems:
        return _error("Spec violation: " + " ".join(problems))
    fn = _HANDLERS.get((command, function))
    if fn is None:
        return _error(f"Function {command}.{function} is not simulated in the CREOSON mock")
    try:
        if (command, function) == ("creo", "set_creo_version"):
            state.creo_versions[session_id] = int(data.get("version"))
        out = fn(state, data)
    except MockError as exc:
        return _error(str(exc))
    response: dict[str, Any] = {"status": {"error": False}}
    if out and "sessionId" in out:
        response["sessionId"] = out.pop("sessionId")
    if out is not None:
        response["data"] = out
    return response


def _error(message: str) -> dict[str, Any]:
    return {"status": {"error": True, "message": message}}


# -- Hilfen -------------------------------------------------------------------

def _match(pattern: str | None, value: str | None) -> bool:
    if pattern is None or pattern == "":
        return True
    return fnmatch.fnmatchcase((value or "").lower(), pattern.lower())


def _model(state: MockCreo, file: str | None) -> MModel:
    name = (file or state.active or "").lower()
    if not name:
        raise MockError("No active model in Creo")
    m = state.session.get(name)
    if m is None:
        raise MockError(f"Model '{name}' is not in session")
    if not isinstance(m, MModel):
        raise MockError(f"'{name}' is not a part or assembly")
    return m


def _drawing(state: MockCreo, name: str | None) -> MDrawing:
    key = (name or state.active or "").lower()
    d = state.session.get(key)
    if not isinstance(d, MDrawing):
        raise MockError(f"Drawing '{key}' is not in session")
    return d


def _numbered(model: MModel) -> list[tuple[int, MFeature]]:
    return [(i + 1, f) for i, f in enumerate(model.features)]


def _feat_out(f: MFeature, number: int | None) -> dict[str, Any]:
    out = {"name": f.name or "", "type": f.type, "status": f.status, "feat_id": f.feat_id}
    if number is not None:
        out["feat_number"] = number
    return out


def _select_features(model: MModel, data: dict[str, Any]) -> list[MFeature]:
    feat_id = data.get("feat_id")
    feat_ids = data.get("feat_ids")
    names = data.get("names") or ([data["name"]] if isinstance(data.get("name"), str) else data.get("name"))
    result = []
    for f in model.features:
        if feat_id is not None and f.feat_id != int(feat_id):
            continue
        if feat_ids and f.feat_id not in feat_ids:
            continue
        if names and not any(_match(n, f.name) for n in names):
            continue
        if not _match(data.get("type"), f.type) or not _match(data.get("status"), f.status):
            continue
        result.append(f)
    return result


def _head_key(f: MFeature) -> str:
    """Gruppen-/Musterkopf: per Name oder – bei KEs ohne Namen – per '#<id>'."""
    return f.name or f"#{f.feat_id}"


def _dirname(state: MockCreo, dirname: str) -> str:
    return "C:" + dirname if state.double_drive_quirk and dirname[1:2] == ":" else dirname


def _with_members(model: MModel, feats: list[MFeature]) -> list[MFeature]:
    heads = {_head_key(f) for f in feats if head_kind(f.type)}
    extra = [f for f in model.features if (f.group in heads or f.pattern in heads) and f not in feats]
    return feats + extra


def _open_one(state: MockCreo, file: str, dirname: str | None) -> MModel | MDrawing:
    key = file.lower()
    if key in state.session:
        return state.session[key]
    m = state.from_disk(key, dirname)
    if m is None:
        raise MockError(f"Could not open {file}: file not found in {dirname or state.working_dir}")
    state.session[key] = m
    if isinstance(m, MModel):
        for f in m.features:
            if f.component and f.component not in state.session:
                _open_one(state, f.component, dirname or m.dirname)
    return m


def _set_status(state: MockCreo, data: dict[str, Any], status: str) -> None:
    model = _model(state, data.get("file"))
    feats = _select_features(model, data)
    if not feats:
        raise MockError("No features found matching the criteria")
    for f in _with_members(model, feats):
        f.status = status
    model.modified = True


# -- connection ---------------------------------------------------------------

@handler("connection", "connect")
def _connect(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    sid = uuid.uuid4().hex[:12]
    state.sessions.add(sid)
    return {"sessionId": sid}


@handler("connection", "disconnect")
def _disconnect(state: MockCreo, data: dict[str, Any]) -> None:
    return None


@handler("connection", "is_creo_running")
def _running(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"running": state.creo_running}


for _fn in ("start_creo", "stop_creo", "kill_creo"):
    handler("connection", _fn)(lambda state, data: None)


# -- creo ---------------------------------------------------------------------

@handler("creo", "set_creo_version")
def _set_version(state: MockCreo, data: dict[str, Any]) -> None:
    if data.get("version") is None:
        raise MockError("Missing version")
    return None


@handler("creo", "pwd")
def _pwd(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"dirname": state.working_dir}


@handler("creo", "cd")
def _cd(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    dirname = data.get("dirname")
    if not dirname:
        raise MockError("Missing dirname")
    state.working_dir = dirname.replace("\\", "/")
    state.disk.setdefault(norm_dir(state.working_dir), {})
    return {"dirname": state.working_dir}


@handler("creo", "list_files")
def _list_files(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"filelist": [f for f in state.files_in_dir() if _match(data.get("filename"), f)]}


@handler("creo", "list_dirs")
def _list_dirs(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    base = norm_dir(state.working_dir) + "/"
    subs = sorted({d[len(base):].split("/")[0] for d in state.disk if d.startswith(base)})
    return {"dirlist": [s for s in subs if _match(data.get("dirname"), s)]}


@handler("creo", "get_config")
def _get_config(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"values": [state.config.get(data.get("name", ""), "")]}


@handler("creo", "set_config")
def _set_config(state: MockCreo, data: dict[str, Any]) -> None:
    state.config[data.get("name", "")] = str(data.get("value", ""))
    return None


# -- file ---------------------------------------------------------------------

@handler("file", "open")
def _file_open(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    files = data.get("files") or ([data["file"]] if data.get("file") else [])
    if not files:
        raise MockError("No file name given")
    opened = []
    for f in files:
        m = _open_one(state, f, data.get("dirname"))
        opened.append(m.file)
    if data.get("display") or data.get("activate"):
        state.displayed.add(opened[0].lower())
    if data.get("activate"):
        state.active = opened[0].lower()
    if state.active is None:
        state.active = opened[0].lower()
    return {"dirname": _dirname(state, data.get("dirname") or state.working_dir), "files": opened, "revision": 1}


@handler("file", "get_active")
def _get_active(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    if not state.active:
        raise MockError("No active model in Creo")
    m = state.session[state.active]
    return {"dirname": _dirname(state, m.dirname), "file": m.file}


@handler("file", "list")
def _file_list(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    pats = data.get("files") or ([data["file"]] if data.get("file") else [None])
    return {"files": sorted(m.file for m in state.session.values() if any(_match(p, m.file) for p in pats))}


@handler("file", "exists")
def _exists(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"exists": (data.get("file") or "").lower() in state.session}


@handler("file", "save")
def _save(state: MockCreo, data: dict[str, Any]) -> None:
    files = data.get("files") or [data.get("file") or state.active]
    for f in files:
        m = state.session.get((f or "").lower())
        if m is None:
            raise MockError(f"Model '{f}' is not in session")
        if isinstance(m, MModel):
            m.revision += 1
            m.modified = False
        state.put_on_disk(m)
    return None


@handler("file", "regenerate")
def _regenerate(state: MockCreo, data: dict[str, Any]) -> None:
    files = data.get("files") or [data.get("file") or state.active]
    for f in files:
        _model(state, f).modified = True
    return None


@handler("file", "erase")
def _erase(state: MockCreo, data: dict[str, Any]) -> None:
    files = data.get("files") or ([data["file"]] if data.get("file") else list(state.session))
    for f in files:
        m = state.session.pop(f.lower(), None)
        if m is None:
            continue
        state.displayed.discard(f.lower())
        if state.active == f.lower():
            state.active = None
        if data.get("erase_children") and isinstance(m, MModel):
            for feat in m.features:
                if feat.component:
                    state.session.pop(feat.component, None)
    return None


@handler("file", "erase_not_displayed")
def _erase_nd(state: MockCreo, data: dict[str, Any]) -> None:
    for key in [k for k in state.session if k not in state.displayed and k != state.active]:
        state.session.pop(key)
    return None


@handler("file", "display")
def _display(state: MockCreo, data: dict[str, Any]) -> None:
    key = (data.get("file") or "").lower()
    if key not in state.session:
        _open_one(state, key, None)
    state.displayed.add(key)
    if data.get("activate"):
        state.active = key
    return None


@handler("file", "close_window")
def _close_window(state: MockCreo, data: dict[str, Any]) -> None:
    key = (data.get("file") or state.active or "").lower()
    state.displayed.discard(key)
    if state.active == key:
        state.active = next(iter(state.displayed), None)
    return None


@handler("file", "rename")
def _rename(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    old = (data.get("file") or state.active or "").lower()
    new = (data.get("new_name") or "").lower()
    if not new:
        raise MockError("Missing new_name")
    m = state.session.pop(old, None)
    if m is None:
        raise MockError(f"Model '{old}' is not in session")
    m.file = new
    state.session[new] = m
    if state.active == old:
        state.active = new
    if not data.get("onlysession"):
        d = norm_dir(m.dirname)
        state.disk.get(d, {}).pop(old, None)
        state.put_on_disk(m)
    return {"file": new}


@handler("file", "backup")
def _backup(state: MockCreo, data: dict[str, Any]) -> None:
    key = (data.get("file") or state.active or "").lower()
    m = state.session.get(key)
    if m is None:
        raise MockError(f"Model '{key}' is not in session")
    target = data.get("target_dir")
    if not target:
        raise MockError("Missing target_dir")
    clone = copy.deepcopy(m)
    clone.dirname = target
    state.put_on_disk(clone, target)
    return None


@handler("file", "get_fileinfo")
def _fileinfo(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    m = state.session.get((data.get("file") or state.active or "").lower())
    if m is None:
        raise MockError("Model is not in session")
    return {"dirname": m.dirname, "file": m.file, "revision": getattr(m, "revision", 1)}


def _volume(state: MockCreo, model: MModel) -> float:
    if not model.is_assembly:
        return model.volume
    total = 0.0
    for f in model.features:
        if f.component and f.status == "ACTIVE":
            comp = state.session.get(f.component) or state.from_disk(f.component, model.dirname)
            if isinstance(comp, MModel):
                total += _volume(state, comp)
    return total


@handler("file", "massprops")
def _massprops(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    model = _model(state, data.get("file"))
    vol = _volume(state, model)
    zero = {"x_axis": {"x": 0.0, "y": 0.0, "z": 0.0}, "y_axis": {"x": 0.0, "y": 0.0, "z": 0.0}, "z_axis": {"x": 0.0, "y": 0.0, "z": 0.0}}
    return {
        "volume": vol,
        "mass": vol * model.density,
        "density": model.density,
        "surface_area": model.surface_area,
        "ctr_grav_inertia_tensor": zero,
        "coord_sys_inertia": zero,
        "coord_sys_inertia_tensor": zero,
        "ctr_grav": {"x": 36.0, "y": 0.0, "z": 0.0},
    }


@handler("file", "relations_get")
def _rel_get(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"relations": list(_model(state, data.get("file")).relations)}


@handler("file", "relations_set")
def _rel_set(state: MockCreo, data: dict[str, Any]) -> None:
    _model(state, data.get("file")).relations = list(data.get("relations") or [])
    return None


@handler("file", "list_materials")
def _list_materials(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"materials": [m for m in _model(state, data.get("file")).materials if _match(data.get("material"), m)]}


@handler("file", "load_material_file")
def _load_material(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    m = _model(state, data.get("file"))
    mat = str(data.get("material") or "").rsplit(".mtl", 1)[0]
    if mat not in m.materials:
        m.materials.append(mat)
    return {"files": [m.file]}


@handler("file", "get_cur_material")
def _get_material(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"material": _model(state, data.get("file")).material}


@handler("file", "set_cur_material")
def _set_material(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    m = _model(state, data.get("file"))
    mat = data.get("material")
    if mat not in m.materials:
        m.materials.append(mat)
    m.material = mat
    return {"files": [m.file]}


@handler("file", "get_length_units")
def _get_lu(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"units": _model(state, data.get("file")).length_units}


@handler("file", "set_length_units")
def _set_lu(state: MockCreo, data: dict[str, Any]) -> None:
    _model(state, data.get("file")).length_units = data.get("units", "mm")
    return None


@handler("file", "get_mass_units")
def _get_mu(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"units": _model(state, data.get("file")).mass_units}


@handler("file", "set_mass_units")
def _set_mu(state: MockCreo, data: dict[str, Any]) -> None:
    _model(state, data.get("file")).mass_units = data.get("units", "kg")
    return None


@handler("file", "assemble")
def _assemble(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    asm = _model(state, data.get("into_asm"))
    if not asm.is_assembly:
        raise MockError(f"'{asm.file}' is not an assembly")
    comp_file = (data.get("file") or "").lower()
    _open_one(state, comp_file, data.get("dirname"))
    fid = state.new_id()
    asm.features.append(MFeature(fid, comp_file, "COMPONENT", component=comp_file))
    asm.modified = True
    return {"dirname": data.get("dirname") or state.working_dir, "files": [comp_file], "revision": 1, "featureid": fid}


# -- feature ------------------------------------------------------------------

@handler("feature", "list")
def _feature_list(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    model = _model(state, data.get("file"))
    out = []
    for number, f in _numbered(model):
        if f.name is None and not data.get("inc_unnamed"):
            continue
        if not _match(data.get("name"), f.name) or not _match(data.get("type"), f.type):
            continue
        if not _match(data.get("status"), f.status):
            continue
        if data.get("no_datum") and is_datum(f.type):
            continue
        if data.get("no_comp") and f.type == "COMPONENT":
            continue
        out.append(_feat_out(f, number if data.get("paths") else None))
    return {"featlist": out}


@handler("feature", "list_group_features")
def _list_group(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    model = _model(state, data.get("file"))
    group = data.get("group_name")
    if not group or not any(f.name == group and head_kind(f.type) == "group" for f in model.features):
        raise MockError(f"Group '{group}' not found")
    numbers = {f.feat_id: n for n, f in _numbered(model)}
    return {"featlist": [_feat_out(f, numbers[f.feat_id]) for f in model.features if f.group == group and _match(data.get("type"), f.type)]}


@handler("feature", "list_pattern_features")
def _list_pattern(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    model = _model(state, data.get("file"))
    name = data.get("pattern_name")
    feat = next((f for f in model.features if name and f.name == name), None)
    if feat is None:
        raise MockError(f"Feature '{name}' not found")
    head = _head_key(feat) if head_kind(feat.type) == "pattern" else feat.pattern
    if head is None:
        raise MockError(f"Feature '{name}' is not a pattern or pattern member")
    numbers = {f.feat_id: n for n, f in _numbered(model)}
    return {"featlist": [_feat_out(f, numbers[f.feat_id]) for f in model.features if f.pattern == head and _match(data.get("type"), f.type)]}


@handler("feature", "suppress")
def _suppress(state: MockCreo, data: dict[str, Any]) -> None:
    _set_status(state, data, "SUPPRESSED")
    return None


@handler("feature", "resume")
def _resume(state: MockCreo, data: dict[str, Any]) -> None:
    _set_status(state, data, "ACTIVE")
    return None


@handler("feature", "delete")
def _delete(state: MockCreo, data: dict[str, Any]) -> None:
    model = _model(state, data.get("file"))
    feats = _select_features(model, data)
    if not feats:
        raise MockError("No features found matching the criteria")
    doomed = {f.feat_id for f in _with_members(model, feats)}
    model.features = [f for f in model.features if f.feat_id not in doomed]
    model.modified = True
    return None


@handler("feature", "rename")
def _feat_rename(state: MockCreo, data: dict[str, Any]) -> None:
    model = _model(state, data.get("file"))
    feats = _select_features(model, {"feat_id": data.get("feat_id"), "name": data.get("name")})
    if len(feats) != 1:
        raise MockError("Feature to rename not found (give feat_id or an exact name)")
    old = feats[0].name
    feats[0].name = data.get("new_name")
    for f in model.features:
        if f.group == old:
            f.group = feats[0].name
        if f.pattern == old:
            f.pattern = feats[0].name
    return None


@handler("feature", "list_params")
def _feat_params(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    model = _model(state, data.get("file"))
    out = []
    for f in _select_features(model, {k: data.get(k) for k in ("feat_id", "name", "type")}):
        for pname, p in f.params.items():
            if _match(data.get("param"), pname):
                out.append({"name": pname, **p, "owner_name": f.name or "", "owner_type": f.type, "owner_id": f.feat_id})
    return {"paramlist": out}


@handler("feature", "set_param")
def _feat_set_param(state: MockCreo, data: dict[str, Any]) -> None:
    model = _model(state, data.get("file"))
    for f in _select_features(model, {"name": data.get("name")}):
        f.params[data["param"]] = {"type": data.get("type", "STRING"), "value": data.get("value"), "designate": bool(data.get("designate")), "description": data.get("description", "")}
    return None


@handler("feature", "list_selected")
def _feat_selected(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    out = []
    for file, fid in state.selected:
        f = state.session[file].feature_by_id(fid)
        if f:
            out.append({**_feat_out(f, None), "file": file})
    return {"featlist": out}


# -- parameter ----------------------------------------------------------------

@handler("parameter", "list")
def _param_list(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    model = _model(state, data.get("file"))
    names = data.get("names") or [data.get("name")]
    out = [
        {"name": n, "value": p["value"], "type": p["type"], "designate": p.get("designate", False), "description": p.get("description", ""), "encoded": False, "owner_name": model.file}
        for n, p in model.params.items()
        if any(_match(pat, n) for pat in names)
    ]
    return {"paramlist": out}


@handler("parameter", "set")
def _param_set(state: MockCreo, data: dict[str, Any]) -> None:
    model = _model(state, data.get("file"))
    name = data.get("name")
    if not name:
        raise MockError("Missing parameter name")
    existing = model.params.get(name)
    if existing is None and data.get("no_create"):
        raise MockError(f"Parameter '{name}' does not exist")
    p = existing or {"type": "STRING", "value": None, "designate": False, "description": ""}
    p["type"] = (data.get("type") or p["type"]).upper()
    p["value"] = data.get("value")
    if "designate" in data:
        p["designate"] = bool(data["designate"])
    if "description" in data:
        p["description"] = data["description"]
    model.params[name] = p
    return None


@handler("parameter", "delete")
def _param_delete(state: MockCreo, data: dict[str, Any]) -> None:
    model = _model(state, data.get("file"))
    if model.params.pop(data.get("name"), None) is None:
        raise MockError(f"Parameter '{data.get('name')}' does not exist")
    return None


@handler("parameter", "exists")
def _param_exists(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"exists": data.get("name") in _model(state, data.get("file")).params}


# -- dimension ----------------------------------------------------------------

def _dims(state: MockCreo, data: dict[str, Any], detail: bool) -> dict[str, Any]:
    model = _model(state, data.get("file"))
    names = data.get("names") or [data.get("name")]
    out = []
    for n, d in model.dims.items():
        if not any(_match(p, n) for p in names):
            continue
        row = {"name": n, "value": d["value"], "encoded": False, "dwg_dim": False}
        if detail:
            row.update({"dim_type": d.get("dim_type", "linear"), "text": ["{0:@D}\n"]})
        out.append(row)
    return {"dimlist": out}


handler("dimension", "list")(lambda state, data: _dims(state, data, False))
handler("dimension", "list_detail")(lambda state, data: _dims(state, data, True))


@handler("dimension", "set")
def _dim_set(state: MockCreo, data: dict[str, Any]) -> None:
    model = _model(state, data.get("file"))
    name = data.get("name")
    if name not in model.dims:
        raise MockError(f"Dimension '{name}' not found")
    model.dims[name]["value"] = float(data.get("value"))
    model.modified = True
    return None


@handler("dimension", "show")
def _dim_show(state: MockCreo, data: dict[str, Any]) -> None:
    _model(state, data.get("file"))
    return None


# -- bom / geometry ---------------------------------------------------------

def _bom_node(state: MockCreo, model: MModel, seq: str, path: list[int], data: dict[str, Any]) -> dict[str, Any]:
    node: dict[str, Any] = {"file": model.file, "seq_path": seq}
    if data.get("paths") and path:
        node["path"] = path
    if data.get("get_transforms") and path:
        node["transform"] = {
            "origin": {"x": 0.0, "y": 0.0, "z": 0.0},
            "x_axis": {"x": 1.0, "y": 0.0, "z": 0.0},
            "y_axis": {"x": 0.0, "y": 1.0, "z": 0.0},
            "z_axis": {"x": 0.0, "y": 0.0, "z": 1.0},
            "x_rot": 0.0,
            "y_rot": 0.0,
            "z_rot": 0.0,
        }
    children = []
    index = 0
    for f in model.features:
        if not f.component:
            continue
        if f.status in ("INACTIVE", "UNREGENERATED") or (data.get("exclude_inactive") and f.status != "ACTIVE"):
            continue
        index += 1
        comp = state.session.get(f.component) or state.from_disk(f.component, model.dirname)
        if not isinstance(comp, MModel):
            continue
        child_path = path + [f.feat_id]
        if data.get("top_level"):
            c: dict[str, Any] = {"file": comp.file, "seq_path": f"{seq}.{index}"}
            if data.get("paths"):
                c["path"] = child_path
            children.append(c)
        else:
            children.append(_bom_node(state, comp, f"{seq}.{index}", child_path, data))
    if children:
        node["children"] = children
    return node


@handler("bom", "get_paths")
def _bom(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    model = _model(state, data.get("file"))
    if not model.is_assembly:
        raise MockError(f"'{model.file}' is not an assembly")
    return {"file": model.file, "generic": "", "children": _bom_node(state, model, "root", [], data)}


@handler("geometry", "bound_box")
def _bbox(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    b = _model(state, data.get("file")).bbox
    return dict(zip(("xmin", "xmax", "ymin", "ymax", "zmin", "zmax"), b))


# -- interface ----------------------------------------------------------------

def _export(state: MockCreo, data: dict[str, Any], kind: str, ext: str) -> dict[str, Any]:
    m = state.session.get((data.get("file") or state.active or "").lower())
    if m is None:
        raise MockError("Model is not in session")
    filename = data.get("filename") or f"{m.file.rsplit('.', 1)[0]}.{ext}"
    dirname = data.get("dirname") or state.working_dir
    state.exports.append({"kind": kind, "file": m.file, "filename": filename, "dirname": dirname, **data})
    state.other_files.setdefault(norm_dir(dirname), set()).add(filename.lower())
    return {"dirname": dirname, "filename": filename}


_EXT = {"STEP": "stp", "IGES": "igs", "DXF": "dxf", "VRML": "wrl", "NEUTRAL": "neu", "PV": "pvz"}


@handler("interface", "export_file")
def _export_file(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    kind = (data.get("type") or "").upper()
    if not kind:
        raise MockError("Missing export type")
    return _export(state, data, kind, _EXT.get(kind, kind.lower()))


handler("interface", "export_pdf")(lambda state, data: _export(state, data, "PDF", "pdf"))
handler("interface", "export_3dpdf")(lambda state, data: _export(state, data, "3DPDF", "pdf"))
handler("interface", "export_image")(lambda state, data: _export(state, data, (data.get("type") or "JPEG").upper(), (data.get("type") or "jpg").lower()))


@handler("interface", "import_file")
def _import(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    filename = data.get("filename")
    if not filename:
        raise MockError("Missing filename")
    mtype = (data.get("new_model_type") or "asm").lower()
    base = (data.get("new_name") or filename.rsplit(".", 1)[0]).lower()
    name = base if base.endswith(f".{mtype}") else f"{base}.{mtype}"
    model = MModel(file=name, features=[MFeature(state.new_id(), "IMPORT_FEATURE", "IMPORT FEATURE")], dirname=state.working_dir)
    state.session[name] = model
    return {"file": name}


@handler("interface", "mapkey")
def _mapkey(state: MockCreo, data: dict[str, Any]) -> None:
    if not data.get("script"):
        raise MockError("Missing script")
    state.mapkeys.append(data["script"])
    return None


# -- drawing ------------------------------------------------------------------

@handler("drawing", "create")
def _drw_create(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    model = _model(state, data.get("model"))
    if not data.get("template"):
        raise MockError("Missing template")
    name = (data.get("drawing") or model.file.rsplit(".", 1)[0] + ".drw").lower()
    if not name.endswith(".drw"):
        name += ".drw"
    drw = MDrawing(file=name, models=[model.file], sheet_scale={1: float(data.get("scale", 1.0))})
    state.session[name] = drw
    if data.get("display") or data.get("activate"):
        state.displayed.add(name)
    if data.get("activate"):
        state.active = name
    if not all(v in model.views for v in TEMPLATE_VIEWS):
        # Wie Creo 12: Die Zeichnung bleibt halb angelegt in der Sitzung, Ansichten lassen sich dort nicht mehr anlegen.
        drw.broken = True
        drw.sheet_scale = {1: 1 / 3}
        raise MockError(TOOLKIT_ERROR.format("Dwg Create Errors"))
    for i, (view, x, y) in enumerate([("FRONT", 108.75, 112.53), ("TOP", 108.75, 232.431), ("RIGHT", 267.952, 112.53)], start=1):
        drw.views[f"VIEW_TEMPLATE_{i}"] = MView(f"VIEW_TEMPLATE_{i}", 1, model.file.lower(), x, y, drw.sheet_scale[1])
    return {"drawing": name}


@handler("drawing", "create_gen_view")
def _drw_gen(state: MockCreo, data: dict[str, Any]) -> None:
    d = _drawing(state, data.get("drawing"))
    name = data.get("view") or data.get("model_view")
    if not data.get("model_view"):
        raise MockError("Missing model_view")
    if d.broken:
        raise MockError(TOOLKIT_ERROR.format("Bad Inputs"))
    target = _model(state, data.get("model") or d.models[0])
    if data["model_view"] not in target.views:
        raise MockError(f"View does not exist on model: {data['model_view']}")
    pt = data.get("point") or {}
    if name in d.views:
        raise MockError(f"View '{name}' already exists")
    d.views[name] = MView(name, int(data.get("sheet", d.cur_sheet)), (data.get("model") or d.models[0]).lower(), float(pt.get("x", 0)), float(pt.get("y", 0)), float(data.get("scale", d.sheet_scale.get(d.cur_sheet, 1.0))))
    return None


@handler("drawing", "create_proj_view")
def _drw_proj(state: MockCreo, data: dict[str, Any]) -> None:
    d = _drawing(state, data.get("drawing"))
    parent = d.views.get(data.get("parent_view"))
    if parent is None:
        raise MockError(f"Parent view '{data.get('parent_view')}' not found")
    name = data.get("view") or f"new_view_{len(d.views) + 1}"
    pt = data.get("point") or {}
    d.views[name] = MView(name, parent.sheet, parent.model, float(pt.get("x", parent.x)), float(pt.get("y", parent.y)), parent.scale, parent=parent.name)
    return None


@handler("drawing", "list_views")
def _drw_views(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    d = _drawing(state, data.get("drawing"))
    return {"views": [v for v in d.views if _match(data.get("view"), v)]}


@handler("drawing", "list_view_details")
def _drw_view_details(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    d = _drawing(state, data.get("drawing"))
    return {
        "views": [
            {"name": v.name, "sheet": v.sheet, "location": {"x": v.x, "y": v.y, "z": 0.0}, "text_height": 3.5, "view_model": v.model, "simp_rep": "Master Rep"}
            for v in d.views.values()
            if _match(data.get("view"), v.name)
        ]
    }


@handler("drawing", "get_num_sheets")
def _drw_num(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"num_sheets": _drawing(state, data.get("drawing")).sheets}


@handler("drawing", "get_cur_sheet")
def _drw_cur(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"sheet": _drawing(state, data.get("drawing")).cur_sheet}


@handler("drawing", "add_sheet")
def _drw_add_sheet(state: MockCreo, data: dict[str, Any]) -> None:
    d = _drawing(state, data.get("drawing"))
    d.sheets += 1
    d.sheet_scale[d.sheets] = 1.0
    return None


@handler("drawing", "delete_sheet")
def _drw_del_sheet(state: MockCreo, data: dict[str, Any]) -> None:
    d = _drawing(state, data.get("drawing"))
    if d.sheets <= 1:
        raise MockError("Cannot delete the only sheet")
    d.sheets -= 1
    return None


@handler("drawing", "select_sheet")
def _drw_select(state: MockCreo, data: dict[str, Any]) -> None:
    d = _drawing(state, data.get("drawing"))
    sheet = int(data.get("sheet", 1))
    if not 1 <= sheet <= d.sheets:
        raise MockError(f"Sheet {sheet} does not exist")
    d.cur_sheet = sheet
    return None


@handler("drawing", "scale_sheet")
def _drw_scale_sheet(state: MockCreo, data: dict[str, Any]) -> None:
    d = _drawing(state, data.get("drawing"))
    d.sheet_scale[int(data.get("sheet", 1))] = float(data.get("scale"))
    return None


@handler("drawing", "get_sheet_scale")
def _drw_get_scale(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"scale": _drawing(state, data.get("drawing")).sheet_scale.get(int(data.get("sheet", 1)), 1.0)}


@handler("drawing", "get_sheet_size")
def _drw_size(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    _drawing(state, data.get("drawing"))
    return {"size": "A3"}


@handler("drawing", "scale_view")
def _drw_scale_view(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    d = _drawing(state, data.get("drawing"))
    ok = []
    for name, v in d.views.items():
        if data.get("view") in (None, name):
            v.scale = float(data.get("scale"))
            ok.append(name)
    return {"success_views": ok, "failed_views": []}


@handler("drawing", "get_view_scale")
def _drw_view_scale(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    v = _drawing(state, data.get("drawing")).views.get(data.get("view"))
    if v is None:
        raise MockError(f"View '{data.get('view')}' not found")
    return {"scale": v.scale}


@handler("drawing", "set_view_loc")
def _drw_set_loc(state: MockCreo, data: dict[str, Any]) -> None:
    v = _drawing(state, data.get("drawing")).views.get(data.get("view"))
    if v is None:
        raise MockError(f"View '{data.get('view')}' not found")
    pt = data.get("point") or {}
    v.x, v.y = float(pt.get("x", v.x)), float(pt.get("y", v.y))
    return None


@handler("drawing", "get_view_loc")
def _drw_get_loc(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    v = _drawing(state, data.get("drawing")).views.get(data.get("view"))
    if v is None:
        raise MockError(f"View '{data.get('view')}' not found")
    return {"x": v.x, "y": v.y, "z": 0.0}


@handler("drawing", "delete_view")
def _drw_del_view(state: MockCreo, data: dict[str, Any]) -> None:
    d = _drawing(state, data.get("drawing"))
    if d.views.pop(data.get("view"), None) is None:
        raise MockError(f"View '{data.get('view')}' not found")
    return None


@handler("drawing", "list_models")
def _drw_models(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"files": [m for m in _drawing(state, data.get("drawing")).models if _match(data.get("model"), m)]}


@handler("drawing", "add_model")
def _drw_add_model(state: MockCreo, data: dict[str, Any]) -> None:
    d = _drawing(state, data.get("drawing"))
    m = _model(state, data.get("model"))
    if m.file not in d.models:
        d.models.append(m.file)
    return None


@handler("drawing", "get_cur_model")
def _drw_cur_model(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"file": _drawing(state, data.get("drawing")).models[0]}


@handler("drawing", "regenerate")
def _drw_regen(state: MockCreo, data: dict[str, Any]) -> None:
    _drawing(state, data.get("drawing"))
    return None


@handler("drawing", "set_sheet_format")
def _drw_set_format(state: MockCreo, data: dict[str, Any]) -> None:
    d = _drawing(state, data.get("drawing"))
    name = str(data.get("file") or "")
    frm = name if name.lower().endswith(".frm") else name + ".frm"
    dirname = data.get("dirname") or state.working_dir
    # wie echtes CREOSON 3.0.2: ohne dirname nur im Arbeitsverzeichnis gesucht – außer das Format ist schon in der
    # Sitzung geladen (am echten Creo 12 ging der 2. Aufruf ohne Ordner durch)
    in_session = frm.lower() in state.formats_in_session
    if not in_session and frm.lower() not in state.other_files.get(norm_dir(dirname), set()):
        raise MockError(f"Could not open file '{frm}' in directory {dirname}")
    state.formats_in_session.add(frm.lower())
    d.sheet_format[int(data.get("sheet", 1))] = name
    return None


@handler("drawing", "get_sheet_format")
def _drw_get_format(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    d = _drawing(state, data.get("drawing"))
    f = d.sheet_format.get(int(data.get("sheet", 1)), "")
    return {"file": f, "full_name": f.upper(), "common_name": f}


# -- view / layer / note / familytable / server ---------------------------------

@handler("view", "list")
def _view_list(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    model = _model(state, data.get("file"))
    return {"viewlist": sorted(n for n in model.views if _match(data.get("name"), n))}


def _active_window_model(state: MockCreo, data: dict[str, Any]) -> MModel:
    """view.activate/view.save wirken in Creo nur auf das Modell im aktiven Fenster (sonst 'General Error')."""
    model = _model(state, data.get("file"))
    if state.active != model.file.lower():
        raise MockError(TOOLKIT_ERROR.format("General Error"))
    return model


@handler("view", "activate")
def _view_activate(state: MockCreo, data: dict[str, Any]) -> None:
    model = _active_window_model(state, data)
    if data.get("name") not in model.views:
        raise MockError(TOOLKIT_ERROR.format("General Error"))
    return None


@handler("view", "save")
def _view_save(state: MockCreo, data: dict[str, Any]) -> None:
    model = _active_window_model(state, data)
    if data["name"] not in model.views:
        model.views.append(data["name"])
    model.modified = True
    return None


@handler("layer", "list")
def _layer_list(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    _model(state, data.get("file"))
    return {"layers": [{"name": "01___PRT_ALL_DTM_PLN", "status": "NORMAL", "id": 17}]}


@handler("note", "list")
def _note_list(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"itemlist": []}


@handler("note", "set")
def _note_set(state: MockCreo, data: dict[str, Any]) -> None:
    return None


@handler("familytable", "list")
def _ft_list(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    _model(state, data.get("file"))
    return {"instances": []}


@handler("server", "pwd")
def _server_pwd(state: MockCreo, data: dict[str, Any]) -> dict[str, Any]:
    return {"dirname": "C:/CreosonServer"}


def known_functions() -> set[tuple[str, str]]:
    return set(_HANDLERS)

