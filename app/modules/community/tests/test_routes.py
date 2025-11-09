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
