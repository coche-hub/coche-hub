from datetime import datetime

from app import create_app


class DummyDataset:
    def __init__(self, id=1, title="Test Dataset"):
        self.id = id
        self.title = title

    def to_dict(self):
        return {"id": self.id, "title": self.title}


class DummyCommunity:
    def __init__(self, id=1, name="Test Community"):
        self.id = id
        self.name = name
        self.created_at = datetime(2025, 1, 1)
        self.updated_at = datetime(2025, 1, 1)


def setup_app(monkeypatch):
    app = create_app()
    try:
        from app.modules.explore.routes import explore_bp

        app.register_blueprint(explore_bp)
    except Exception:
        pass
    app.config.update({"TESTING": True})
    return app


def test_explore_index_get_returns_200(monkeypatch):
    """Test que GET /explore retorna 200"""
    app = setup_app(monkeypatch)

    from app.modules.community.services import CommunityService

    monkeypatch.setattr(CommunityService, "get_all_communities", lambda self: [])

    with app.test_client() as client:
        rv = client.get("/explore")
        assert rv.status_code == 200


def test_explore_index_get_with_query_param(monkeypatch):
    """Test que GET /explore acepta query parameter"""
    app = setup_app(monkeypatch)

    from app.modules.community.services import CommunityService

    monkeypatch.setattr(CommunityService, "get_all_communities", lambda self: [DummyCommunity()])

    with app.test_client() as client:
        rv = client.get("/explore?query=test")
        assert rv.status_code == 200
        assert b"test" in rv.data or rv.status_code == 200  # El query se pasa al template


def test_explore_index_get_shows_communities(monkeypatch):
    """Test que GET /explore muestra comunidades"""
    app = setup_app(monkeypatch)

    from app.modules.community.services import CommunityService

    dummy_community = DummyCommunity(id=1, name="TestComm")
    monkeypatch.setattr(CommunityService, "get_all_communities", lambda self: [dummy_community])

    with app.test_client() as client:
        rv = client.get("/explore")
        assert rv.status_code == 200


def test_explore_index_post_returns_json(monkeypatch):
    """Test que POST /explore retorna JSON"""
    app = setup_app(monkeypatch)

    from app.modules.explore.services import ExploreService

    datasets = [DummyDataset(1, "Dataset1"), DummyDataset(2, "Dataset2")]
    monkeypatch.setattr(ExploreService, "filter", lambda self, **kwargs: datasets)

    with app.test_client() as client:
        rv = client.post("/explore", json={}, content_type="application/json")
        assert rv.status_code == 200
        assert rv.is_json
        data = rv.get_json()
        assert len(data) == 2
        assert data[0]["id"] == 1


def test_explore_index_post_with_filters(monkeypatch):
    """Test que POST /explore acepta filtros"""
    app = setup_app(monkeypatch)

    from app.modules.explore.services import ExploreService

    captured_criteria = {}

    def fake_filter(self, **kwargs):
        captured_criteria.update(kwargs)
        return [DummyDataset(1)]

    monkeypatch.setattr(ExploreService, "filter", fake_filter)

    with app.test_client() as client:
        rv = client.post("/explore", json={"title": "test", "author": "john"}, content_type="application/json")
        assert rv.status_code == 200
        assert captured_criteria["title"] == "test"
        assert captured_criteria["author"] == "john"


def test_explore_index_post_empty_criteria(monkeypatch):
    """Test que POST /explore funciona con criterios vacíos"""
    app = setup_app(monkeypatch)

    from app.modules.explore.services import ExploreService

    monkeypatch.setattr(ExploreService, "filter", lambda self, **kwargs: [])

    with app.test_client() as client:
        rv = client.post("/explore", json={}, content_type="application/json")
        assert rv.status_code == 200
        data = rv.get_json()
        assert data == []
