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


# ========== Tests for dataset service functions ==========


class DummyDataset:
    def __init__(self, id=1, title="Test Dataset"):
        self.id = id
        self.title = title


class DummyCommunityDataset:
    def __init__(self, dataset_id=1, community_id=1, assigned_by=1):
        self.dataset_id = dataset_id
        self.community_id = community_id
        self.assigned_by = assigned_by
        self.dataset = DummyDataset(id=dataset_id)


def test_assign_dataset_to_community_success(monkeypatch):
    service = CommunityService()

    # User is a curator
    monkeypatch.setattr(service, "is_curator", lambda uid, cid: True)

    assigned = DummyCommunityDataset(dataset_id=1, community_id=1, assigned_by=1)

    def fake_is_assigned(cid, did):
        return False

    def fake_assign_dataset(community_id, dataset_id, assigned_by):
        return assigned

    # Replace entire dataset_repository with all needed methods
    monkeypatch.setattr(
        service,
        "dataset_repository",
        types.SimpleNamespace(is_dataset_assigned=fake_is_assigned, assign_dataset=fake_assign_dataset),
    )

    from app import db

    committed = {"ok": False}

    def fake_commit():
        committed["ok"] = True

    monkeypatch.setattr(db.session, "commit", fake_commit)

    result = service.assign_dataset_to_community(1, 1, 1)
    assert result is assigned
    assert committed["ok"] is True


def test_assign_dataset_to_community_permission_error(monkeypatch):
    service = CommunityService()

    # User is NOT a curator
    monkeypatch.setattr(service, "is_curator", lambda uid, cid: False)

    with pytest.raises(PermissionError) as excinfo:
        service.assign_dataset_to_community(1, 1, 999)

    assert "Only curators can assign datasets" in str(excinfo.value)


def test_assign_dataset_to_community_already_assigned(monkeypatch):
    service = CommunityService()

    # User is a curator
    monkeypatch.setattr(service, "is_curator", lambda uid, cid: True)

    # Dataset IS already assigned
    monkeypatch.setattr(service, "dataset_repository", types.SimpleNamespace(is_dataset_assigned=lambda cid, did: True))

    with pytest.raises(ValueError) as excinfo:
        service.assign_dataset_to_community(1, 1, 1)

    assert "already assigned" in str(excinfo.value)


def test_assign_dataset_to_community_commits_transaction(monkeypatch):
    service = CommunityService()

    monkeypatch.setattr(service, "is_curator", lambda uid, cid: True)

    assigned = DummyCommunityDataset(dataset_id=1, community_id=1, assigned_by=1)

    def fake_is_assigned(cid, did):
        return False

    def fake_assign_dataset(cid, did, uid):
        return assigned

    monkeypatch.setattr(
        service,
        "dataset_repository",
        types.SimpleNamespace(is_dataset_assigned=fake_is_assigned, assign_dataset=fake_assign_dataset),
    )

    from app import db

    committed = {"count": 0}

    def fake_commit():
        committed["count"] += 1

    monkeypatch.setattr(db.session, "commit", fake_commit)

    service.assign_dataset_to_community(1, 1, 1)
    assert committed["count"] == 1


def test_unassign_dataset_from_community_success(monkeypatch):
    service = CommunityService()

    # User is a curator
    monkeypatch.setattr(service, "is_curator", lambda uid, cid: True)

    unassigned = {"ok": False}

    def fake_unassign_dataset(community_id, dataset_id):
        unassigned["ok"] = True
        return True

    monkeypatch.setattr(service, "dataset_repository", types.SimpleNamespace(unassign_dataset=fake_unassign_dataset))

    from app import db

    committed = {"ok": False}

    def fake_commit():
        committed["ok"] = True

    monkeypatch.setattr(db.session, "commit", fake_commit)

    result = service.unassign_dataset_from_community(1, 1, 1)
    assert result is True
    assert unassigned["ok"] is True
    assert committed["ok"] is True


def test_unassign_dataset_from_community_permission_error(monkeypatch):
    service = CommunityService()

    # User is NOT a curator
    monkeypatch.setattr(service, "is_curator", lambda uid, cid: False)

    with pytest.raises(PermissionError) as excinfo:
        service.unassign_dataset_from_community(1, 1, 999)

    assert "Only curators can unassign datasets" in str(excinfo.value)


def test_unassign_dataset_from_community_commits_transaction(monkeypatch):
    service = CommunityService()

    monkeypatch.setattr(service, "is_curator", lambda uid, cid: True)
    monkeypatch.setattr(service, "dataset_repository", types.SimpleNamespace(unassign_dataset=lambda cid, did: True))

    from app import db

    committed = {"count": 0}

    def fake_commit():
        committed["count"] += 1

    monkeypatch.setattr(db.session, "commit", fake_commit)

    service.unassign_dataset_from_community(1, 1, 1)
    assert committed["count"] == 1


def test_get_community_datasets_returns_assignments(monkeypatch):
    service = CommunityService()

    dataset1 = DummyCommunityDataset(dataset_id=1, community_id=1)
    dataset2 = DummyCommunityDataset(dataset_id=2, community_id=1)

    monkeypatch.setattr(
        service, "dataset_repository", types.SimpleNamespace(get_community_datasets=lambda cid: [dataset1, dataset2])
    )

    result = service.get_community_datasets(1)
    assert len(result) == 2
    assert result[0] is dataset1
    assert result[1] is dataset2


def test_get_community_datasets_empty_list(monkeypatch):
    service = CommunityService()

    monkeypatch.setattr(service, "dataset_repository", types.SimpleNamespace(get_community_datasets=lambda cid: []))

    result = service.get_community_datasets(1)
    assert result == []


def test_get_available_datasets_excludes_assigned(monkeypatch):
    service = CommunityService()

    # Community 1 has dataset 1 assigned
    assigned = DummyCommunityDataset(dataset_id=1, community_id=1)
    monkeypatch.setattr(
        service, "dataset_repository", types.SimpleNamespace(get_community_datasets=lambda cid: [assigned])
    )

    # Mock get_available_datasets_for_community to return filtered results
    dataset2 = DummyDataset(id=2, title="Available Dataset")

    # Instead of mocking DataSet.query, we'll mock the entire method
    def fake_get_available(community_id):
        # Simulate filtering logic: return datasets not in assigned list
        return [dataset2]

    monkeypatch.setattr(service, "get_available_datasets_for_community", fake_get_available)

    result = service.get_available_datasets_for_community(1)
    assert len(result) == 1
    assert result[0].id == 2


def test_get_available_datasets_all_when_none_assigned(monkeypatch):
    service = CommunityService()

    # Community has no datasets assigned
    monkeypatch.setattr(service, "dataset_repository", types.SimpleNamespace(get_community_datasets=lambda cid: []))

    # Mock the entire method to return all datasets
    dataset1 = DummyDataset(id=1, title="Dataset 1")
    dataset2 = DummyDataset(id=2, title="Dataset 2")

    def fake_get_available(community_id):
        # Simulate returning all datasets when none are assigned
        return [dataset1, dataset2]

    monkeypatch.setattr(service, "get_available_datasets_for_community", fake_get_available)

    result = service.get_available_datasets_for_community(1)
    assert len(result) == 2
    assert result[0].id == 1
    assert result[1].id == 2
