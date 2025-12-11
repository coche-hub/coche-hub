import types

import pytest

from app.modules.community.services import CommunityService


class DummyCommunity:
    def __init__(self, id=1, name="c1", description="d", logo=None):
        self.id = id
        self.name = name
        self.description = description
        self.logo = logo


class DummyCurator:
    def __init__(self, user_id, community_id):
        self.user_id = user_id
        self.community_id = community_id


def test_create_community_calls_repositories_and_commits(monkeypatch):
    service = CommunityService()

    created = DummyCommunity(id=42)

    # replace repository.create to return our dummy
    monkeypatch.setattr(service, "repository", types.SimpleNamespace(create=lambda **kw: created))

    called = {}

    def fake_add_curator(community_id, creator_id):
        called["add_curator"] = (community_id, creator_id)
        return DummyCurator(user_id=creator_id, community_id=community_id)

    monkeypatch.setattr(service, "curator_repository", types.SimpleNamespace(add_curator=fake_add_curator))

    # patch db.session.flush and commit to no-ops
    from app import db

    monkeypatch.setattr(db.session, "flush", lambda: None)
    monkeypatch.setattr(db.session, "commit", lambda: None)

    result = service.create_community(name="n", description="d", creator_id=7)

    assert result is created
    assert called["add_curator"] == (42, 7)


def test_update_community_sets_fields_and_calls_update(monkeypatch):
    service = CommunityService()
    community = DummyCommunity(id=5, name="old", description="old desc")

    # get_by_id should return the community
    monkeypatch.setattr(service, "get_by_id", lambda cid: community)

    committed = {"ok": False}

    def fake_commit():
        committed["ok"] = True

    from app import db

    monkeypatch.setattr(db.session, "commit", fake_commit)

    updated = service.update_community(5, name="new", description="new desc", logo="logo.png")

    assert community.name == "new"
    assert community.description == "new desc"
    assert community.logo == "logo.png"
    assert updated is community
    assert committed["ok"] is True


def test_delete_community_delegates_to_base_delete(monkeypatch):
    service = CommunityService()
    # ensure get_by_id returns something
    monkeypatch.setattr(service, "get_by_id", lambda cid: DummyCommunity(id=cid))

    monkeypatch.setattr(service, "delete", lambda cid: True)

    assert service.delete_community(10) is True


def test_add_curator_commits_and_returns_curator(monkeypatch):
    service = CommunityService()

    def fake_add_curator(community_id, user_id):
        return DummyCurator(user_id=user_id, community_id=community_id)

    monkeypatch.setattr(service, "curator_repository", types.SimpleNamespace(add_curator=fake_add_curator))

    from app import db

    committed = {"ok": False}

    def fake_commit():
        committed["ok"] = True

    monkeypatch.setattr(db.session, "commit", fake_commit)

    curator = service.add_curator(1, 2)
    assert isinstance(curator, DummyCurator)
    assert committed["ok"] is True


def test_remove_curator_checks_last_curator_and_calls_remove(monkeypatch):
    service = CommunityService()

    # case: only one curator -> should raise
    monkeypatch.setattr(service, "curator_repository", types.SimpleNamespace(get_curators_by_community=lambda cid: [1]))
    with pytest.raises(ValueError):
        service.remove_curator(1, 1, requester_id=2)

    # case: multiple curators -> call remove_curator
    def fake_get(cid):
        return [1, 2]

    removed = {"ok": False}

    def fake_remove(community_id, user_id):
        removed["ok"] = True
        return True

    ns = types.SimpleNamespace(get_curators_by_community=fake_get, remove_curator=fake_remove)
    monkeypatch.setattr(service, "curator_repository", ns)
    assert service.remove_curator(1, 2, requester_id=1) is True
    assert removed["ok"] is True


def test_is_curator_delegates(monkeypatch):
    service = CommunityService()
    monkeypatch.setattr(service, "curator_repository", types.SimpleNamespace(is_curator=lambda u, c: True))
    assert service.is_curator(1, 2) is True
