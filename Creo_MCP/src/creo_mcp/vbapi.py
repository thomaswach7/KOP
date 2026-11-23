"""Optionales Backend über die Creo VB API (COM, nur Windows).

Wofür: Informationen, die CREOSON nicht liefert – vor allem die Eltern/Kind-Beziehungen der KEs
("Stammbaum" im Sinne von Abhängigkeiten) – und Makros direkt über `Session.RunMacro`.

Voraussetzungen auf dem PC:
- Creo mit gesetztem PRO_COMM_MSG_EXE gestartet (macht nitro_proe_remote.bat von CREOSON),
- VB API registriert: `<Creo>\\Parametric\\bin\\vb_api_register.bat` als Administrator ausführen,
- `pip install pywin32`.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterator
from typing import Any

from .errors import CreoMCPError

# Reihenfolge von EpfcFeatureStatus (wie J-Link FeatureStatus)
_STATUS = {
    0: "ACTIVE",
    1: "INACTIVE",
    2: "FAMILY_TABLE_SUPPRESSED",
    3: "SIMP_REP_SUPPRESSED",
    4: "PROGRAM_SUPPRESSED",
    5: "SUPPRESSED",
    6: "UNREGENERATED",
}
PROG_ID = "pfcls.pfcAsyncConnection"


class VbApiUnavailable(CreoMCPError):
    """VB API kann auf diesem System nicht genutzt werden."""


def _iter(collection: Any) -> Iterator[Any]:
    if collection is None:
        return
    for i in range(int(collection.Count)):
        yield collection.Item(i)


def _safe(fn: Callable[[], Any]) -> Any:
    try:
        return fn()
    except Exception:  # COM-Fehler einzelner Eigenschaften nicht eskalieren
        return None


def feature_info(feat: Any) -> dict[str, Any]:
    status = _safe(lambda: int(feat.Status))
    return {
        "feat_id": _safe(lambda: int(feat.Id)),
        "name": _safe(feat.GetName) or "",
        "type": _safe(lambda: feat.FeatTypeName) or "",
        "number": _safe(lambda: feat.Number),
        "status": _STATUS.get(status, str(status)) if status is not None else None,
    }


class VbApiSession:
    def __init__(self, session: Any, connection: Any = None):
        self.session = session
        self.connection = connection

    @classmethod
    def connect(cls, dispatch: Callable[[str], Any] | None = None, timeout_s: int = 10, platform: str = sys.platform) -> VbApiSession:
        if dispatch is None:
            if platform != "win32":
                raise VbApiUnavailable("The Creo VB API needs Windows with Creo installed (COM). Use the CREOSON tools instead.")
            try:
                import win32com.client  # type: ignore[import-not-found]
            except ImportError as exc:
                raise VbApiUnavailable("pywin32 is missing: run 'pip install pywin32' in the MCP server's Python.") from exc
            dispatch = win32com.client.Dispatch
        try:
            factory = dispatch(PROG_ID)
        except Exception as exc:
            raise VbApiUnavailable(
                "VB API is not registered. Run '<Creo>\\Parametric\\bin\\vb_api_register.bat' as administrator once."
            ) from exc
        try:
            connection = factory.Connect("", "", ".", timeout_s)
        except Exception as exc:
            raise VbApiUnavailable(
                "Could not connect to Creo via VB API. Creo must run and be started with PRO_COMM_MSG_EXE set "
                f"(e.g. via CREOSON's nitro_proe_remote.bat). Details: {exc}"
            ) from exc
        return cls(connection.Session, connection)

    def model(self, file: str | None) -> Any:
        model = self.session.GetModelFromFileName(file) if file else self.session.CurrentModel
        if model is None:
            raise CreoMCPError(f"Model '{file or 'active model'}' is not in the Creo session. Open it first (creo_open_model).")
        return model

    def feature_relations(self, file: str | None, feature_id: int) -> dict[str, Any]:
        feat = self.model(file).GetFeatureById(int(feature_id))
        if feat is None:
            raise CreoMCPError(f"Feature id {feature_id} not found in {file or 'the active model'}.")
        return {
            "feature": feature_info(feat),
            "parents": [feature_info(p) for p in _iter(_safe(feat.ListParents))],
            "children": [feature_info(c) for c in _iter(_safe(feat.ListChildren))],
        }

    def dependency_graph(self, file: str | None, limit: int = 500) -> list[dict[str, Any]]:
        model = self.model(file)
        rows = []
        try:
            feats = model.ListFeaturesByType(True)  # Typ ist optional
        except Exception:
            feats = model.ListFeaturesByType(True, None)
        for feat in _iter(feats):
            info = feature_info(feat)
            info["parents"] = [feature_info(p)["feat_id"] for p in _iter(_safe(feat.ListParents))]
            rows.append(info)
            if len(rows) >= limit:
                break
        return rows

    def run_macro(self, script: str) -> None:
        self.session.RunMacro(script)

    def disconnect(self) -> None:
        if self.connection is not None:
            _safe(lambda: self.connection.Disconnect(2))
