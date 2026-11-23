import pytest

from creo_mcp.errors import CreoMCPError
from creo_mcp.vbapi import VbApiSession, VbApiUnavailable


class FakeColl:
    def __init__(self, items):
        self._items = list(items)

    @property
    def Count(self):  # noqa: N802 (COM-Name)
        return len(self._items)

    def Item(self, i):  # noqa: N802
        return self._items[i]


class FakeFeature:
    def __init__(self, fid, name, ftype, number, status=0):
        self.Id, self._name, self.FeatTypeName, self.Number, self.Status = fid, name, ftype, number, status
        self.parents, self.children = [], []

    def GetName(self):  # noqa: N802
        return self._name

    def ListParents(self):  # noqa: N802
        return FakeColl(self.parents)

    def ListChildren(self):  # noqa: N802
        return FakeColl(self.children)


class FakeModel:
    def __init__(self, name, feats):
        self.FileName = name
        self._feats = {f.Id: f for f in feats}

    def GetFeatureById(self, fid):  # noqa: N802
        return self._feats.get(fid)

    def ListFeaturesByType(self, visible, ftype):  # noqa: N802
        return FakeColl(self._feats.values())


class FakeSession:
    def __init__(self, model):
        self.CurrentModel = model
        self.macros = []
        self._models = {model.FileName: model}

    def GetModelFromFileName(self, name):  # noqa: N802
        return self._models.get(name)

    def RunMacro(self, macro):  # noqa: N802
        self.macros.append(macro)


def _fake_dispatch(session):
    class Conn:
        Session = session

        def Disconnect(self, timeout=None):  # noqa: N802
            pass

    class Factory:
        def Connect(self, display, user, textpath, timeout):  # noqa: N802
            return Conn()

    def dispatch(progid):
        assert progid == "pfcls.pfcAsyncConnection"
        return Factory()

    return dispatch


@pytest.fixture()
def vb():
    right = FakeFeature(1, "RIGHT", "DATUM PLANE", 1)
    body = FakeFeature(40, "Grundkörper", "PROTRUSION", 5)
    nut = FakeFeature(60, "Passfedernut", "CUT", 6, status=5)
    body.parents, body.children = [right], [nut]
    nut.parents = [body, right]
    right.children = [body, nut]
    session = FakeSession(FakeModel("abtriebsnabe.prt", [right, body, nut]))
    return VbApiSession.connect(dispatch=_fake_dispatch(session)), session


def test_feature_relations_lists_parents_and_children(vb):
    api, _ = vb
    rel = api.feature_relations("abtriebsnabe.prt", 40)
    assert rel["feature"]["name"] == "Grundkörper"
    assert [p["feat_id"] for p in rel["parents"]] == [1]
    assert [c["name"] for c in rel["children"]] == ["Passfedernut"]
    assert rel["children"][0]["status"] == "SUPPRESSED"


def test_dependency_graph_of_whole_model(vb):
    api, _ = vb
    graph = api.dependency_graph(None)
    by_id = {row["feat_id"]: row for row in graph}
    assert by_id[60]["parents"] == [40, 1]


def test_unknown_feature_raises(vb):
    api, _ = vb
    with pytest.raises(CreoMCPError):
        api.feature_relations("abtriebsnabe.prt", 999)


def test_run_macro(vb):
    api, session = vb
    api.run_macro("~ Command `ProCmdModelSave` ;")
    assert session.macros == ["~ Command `ProCmdModelSave` ;"]


def test_without_windows_gives_clear_message():
    with pytest.raises(VbApiUnavailable) as exc:
        VbApiSession.connect(platform="linux")
    assert "Windows" in str(exc.value)
