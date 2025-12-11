from datetime import datetime

from app import create_app


class DummyCommunity:
    def __init__(self, id=1, name="Test Community", description="desc", logo=None):
        self.id = id
        self.name = name
        self.description = description
        self.logo = logo
        # add common timestamp fields and others that templates might access
        # templates expect datetime-like objects (may call strftime)
        self.created_at = datetime(2025, 1, 1, 0, 0, 0)
        self.updated_at = datetime(2025, 1, 1, 0, 0, 0)


def setup_app(monkeypatch):
    app = create_app()
    # register blueprint explicitly in case ModuleManager isn't run in tests
    try:
        from app.modules.community.routes import community_bp

        app.register_blueprint(community_bp)
    except Exception:
        pass
    app.config.update({"TESTING": True})
    return app


def test_index_route_returns_200(monkeypatch):
    app = setup_app(monkeypatch)

    # avoid DB calls by stubbing service method
    from app.modules.community.services import CommunityService

    monkeypatch.setattr(CommunityService, "get_all_communities", lambda self: [])

    with app.test_client() as client:
        rv = client.get("/community")
        assert rv.status_code == 200


def test_detail_route_404_when_missing(monkeypatch):
    app = setup_app(monkeypatch)
    from app.modules.community.services import CommunityService

    monkeypatch.setattr(CommunityService, "get_by_id", lambda self, cid: None)

    with app.test_client() as client:
        rv = client.get("/community/99999")
        assert rv.status_code == 404


def test_detail_route_renders_when_present(monkeypatch):
    app = setup_app(monkeypatch)
    from app.modules.community.services import CommunityService

    dummy = DummyCommunity(id=7, name="MyCommunity")
    monkeypatch.setattr(CommunityService, "get_by_id", lambda self, cid: dummy)
    monkeypatch.setattr(CommunityService, "get_community_curators", lambda self, cid: [])
    monkeypatch.setattr(CommunityService, "is_curator", lambda self, uid, cid: False)

    with app.test_client() as client:
        rv = client.get("/community/7")
        assert rv.status_code == 200
        # page should include community name
        assert b"MyCommunity" in rv.data


def test_remove_curator_requires_login(monkeypatch):
    app = setup_app(monkeypatch)
    with app.test_client() as client:
        rv = client.post("/community/1/curators/2/remove")
        # without login, should redirect to login (302)
        assert rv.status_code in (302, 401)


def test_remove_curator_aborts_403_when_login_disabled(monkeypatch):
    # If LOGIN_DISABLED is True, login_required is bypassed and the route itself aborts 403
    app = setup_app(monkeypatch)
    app.config["LOGIN_DISABLED"] = True

    with app.test_client() as client:
        rv = client.post("/community/1/curators/2/remove")
        assert rv.status_code == 403


# ========== Tests for dataset routes ==========


class DummyDataset:
    def __init__(self, id=1, title="Test Dataset"):
        self.id = id
        self.title = title
        self.description = "Test description"
        self.created_at = datetime(2025, 1, 1)

        # Create ds_meta_data as an object with attributes
        class DummyDSMetaData:
            def __init__(self):
                self.title = title
                self.description = "Test description"
                self.dataset_doi = None

        self.ds_meta_data = DummyDSMetaData()

    def get_files_count(self):
        return 0

    def get_file_total_size_for_human(self):
        return "0 B"

    def get_dataset_url(self):
        return "#"


class DummyCommunityDataset:
    def __init__(self, dataset_id=1, community_id=1):
        self.dataset_id = dataset_id
        self.community_id = community_id
        self.dataset = DummyDataset(id=dataset_id)


def test_view_datasets_returns_200_for_valid_community(monkeypatch):
    app = setup_app(monkeypatch)
    from app.modules.community.services import CommunityService

    dummy_community = DummyCommunity(id=1, name="Test Community")
    monkeypatch.setattr(CommunityService, "get_by_id", lambda self, cid: dummy_community)
    monkeypatch.setattr(CommunityService, "get_community_datasets", lambda self, cid: [])
    monkeypatch.setattr(CommunityService, "is_curator", lambda self, uid, cid: False)

    with app.test_client() as client:
        rv = client.get("/community/1/datasets")
        assert rv.status_code == 200


def test_view_datasets_returns_404_for_invalid_community(monkeypatch):
    app = setup_app(monkeypatch)
    from app.modules.community.services import CommunityService

    monkeypatch.setattr(CommunityService, "get_by_id", lambda self, cid: None)

    with app.test_client() as client:
        rv = client.get("/community/999/datasets")
        assert rv.status_code == 404


def test_view_datasets_shows_assigned_datasets(monkeypatch):
    app = setup_app(monkeypatch)
    from app.modules.community.services import CommunityService

    dummy_community = DummyCommunity(id=1, name="Test Community")
    dataset = DummyDataset(id=1, title="My Dataset")
    dataset_assignment = DummyCommunityDataset(dataset_id=1, community_id=1)
    dataset_assignment.dataset = dataset

    monkeypatch.setattr(CommunityService, "get_by_id", lambda self, cid: dummy_community)
    monkeypatch.setattr(CommunityService, "get_community_datasets", lambda self, cid: [dataset_assignment])
    monkeypatch.setattr(CommunityService, "is_curator", lambda self, uid, cid: False)

    with app.test_client() as client:
        rv = client.get("/community/1/datasets")
        assert rv.status_code == 200
        assert b"My Dataset" in rv.data


def test_manage_datasets_requires_login(monkeypatch):
    app = setup_app(monkeypatch)
    with app.test_client() as client:
        rv = client.get("/community/1/datasets/manage")
        # without login, should redirect to login (302)
        assert rv.status_code in (302, 401)


def test_manage_datasets_requires_curator_permission(monkeypatch):
    app = setup_app(monkeypatch)
    app.config["LOGIN_DISABLED"] = True
    from app.modules.community.services import CommunityService

    # Mock current_user for authentication check
    class MockUser:
        id = 1
        is_authenticated = True

        class MockProfile:
            name = "Test"
            surname = "User"

        profile = MockProfile()

    monkeypatch.setattr("flask_login.utils._get_user", lambda: MockUser())

    dummy_community = DummyCommunity(id=1, name="Test Community")
    monkeypatch.setattr(CommunityService, "get_by_id", lambda self, cid: dummy_community)
    monkeypatch.setattr(CommunityService, "is_curator", lambda self, uid, cid: False)

    with app.test_client() as client:
        rv = client.get("/community/1/datasets/manage")
        assert rv.status_code == 403


def test_manage_datasets_returns_200_for_curator(monkeypatch):
    app = setup_app(monkeypatch)
    app.config["LOGIN_DISABLED"] = True
    from app.modules.community.services import CommunityService

    class MockUser:
        id = 1
        is_authenticated = True

        class MockProfile:
            name = "Test"
            surname = "User"

        profile = MockProfile()

    monkeypatch.setattr("flask_login.utils._get_user", lambda: MockUser())

    dummy_community = DummyCommunity(id=1, name="Test Community")
    monkeypatch.setattr(CommunityService, "get_by_id", lambda self, cid: dummy_community)
    monkeypatch.setattr(CommunityService, "is_curator", lambda self, uid, cid: True)
    monkeypatch.setattr(CommunityService, "get_community_datasets", lambda self, cid: [])
    monkeypatch.setattr(CommunityService, "get_available_datasets_for_community", lambda self, cid: [])

    with app.test_client() as client:
        rv = client.get("/community/1/datasets/manage")
        assert rv.status_code == 200


def test_manage_datasets_shows_assigned_and_available(monkeypatch):
    app = setup_app(monkeypatch)
    app.config["LOGIN_DISABLED"] = True
    from app.modules.community.services import CommunityService

    class MockUser:
        id = 1
        is_authenticated = True

        class MockProfile:
            name = "Test"
            surname = "User"

        profile = MockProfile()

    monkeypatch.setattr("flask_login.utils._get_user", lambda: MockUser())

    dummy_community = DummyCommunity(id=1, name="Test Community")
    assigned = DummyCommunityDataset(dataset_id=1, community_id=1)
    assigned.dataset = DummyDataset(id=1, title="Assigned Dataset")
    available = DummyDataset(id=2, title="Available Dataset")

    monkeypatch.setattr(CommunityService, "get_by_id", lambda self, cid: dummy_community)
    monkeypatch.setattr(CommunityService, "is_curator", lambda self, uid, cid: True)
    monkeypatch.setattr(CommunityService, "get_community_datasets", lambda self, cid: [assigned])
    monkeypatch.setattr(CommunityService, "get_available_datasets_for_community", lambda self, cid: [available])

    with app.test_client() as client:
        rv = client.get("/community/1/datasets/manage")
        assert rv.status_code == 200
        assert b"Assigned Dataset" in rv.data
        assert b"Available Dataset" in rv.data


def test_assign_dataset_requires_login(monkeypatch):
    app = setup_app(monkeypatch)
    with app.test_client() as client:
        rv = client.post("/community/1/datasets/assign", data={"dataset_id": "1"})
        assert rv.status_code in (302, 401)


def test_assign_dataset_requires_curator_permission(monkeypatch):
    app = setup_app(monkeypatch)
    app.config["LOGIN_DISABLED"] = True
    from app.modules.community.services import CommunityService

    class MockUser:
        id = 1
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", lambda: MockUser())
    monkeypatch.setattr(CommunityService, "is_curator", lambda self, uid, cid: False)

    with app.test_client() as client:
        rv = client.post("/community/1/datasets/assign", data={"dataset_id": "1"})
        assert rv.status_code == 403


def test_assign_dataset_success(monkeypatch):
    app = setup_app(monkeypatch)
    app.config["LOGIN_DISABLED"] = True
    from app.modules.community.services import CommunityService

    class MockUser:
        id = 1
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", lambda: MockUser())
    monkeypatch.setattr(CommunityService, "is_curator", lambda self, uid, cid: True)
    monkeypatch.setattr(CommunityService, "assign_dataset_to_community", lambda self, cid, did, uid: None)

    with app.test_client() as client:
        rv = client.post("/community/1/datasets/assign", data={"dataset_id": "1"}, follow_redirects=False)
        assert rv.status_code == 302  # redirect after success
        assert b"/community/1/datasets/manage" in rv.data


def test_assign_dataset_missing_dataset_id(monkeypatch):
    app = setup_app(monkeypatch)
    app.config["LOGIN_DISABLED"] = True
    from app.modules.community.services import CommunityService

    class MockUser:
        id = 1
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", lambda: MockUser())
    monkeypatch.setattr(CommunityService, "is_curator", lambda self, uid, cid: True)

    with app.test_client() as client:
        rv = client.post("/community/1/datasets/assign", data={}, follow_redirects=False)
        assert rv.status_code == 302  # redirect with error flash


def test_unassign_dataset_success(monkeypatch):
    app = setup_app(monkeypatch)
    app.config["LOGIN_DISABLED"] = True
    from app.modules.community.services import CommunityService

    class MockUser:
        id = 1
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", lambda: MockUser())
    monkeypatch.setattr(CommunityService, "is_curator", lambda self, uid, cid: True)
    monkeypatch.setattr(CommunityService, "unassign_dataset_from_community", lambda self, cid, did, uid: None)

    with app.test_client() as client:
        rv = client.post("/community/1/datasets/1/unassign", follow_redirects=False)
        assert rv.status_code == 302  # redirect after success
        assert b"/community/1/datasets/manage" in rv.data
