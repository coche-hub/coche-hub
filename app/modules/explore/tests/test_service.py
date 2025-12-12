from app.modules.explore.services import ExploreService


class DummyDataset:
    def __init__(self, id=1):
        self.id = id

    def to_dict(self):
        return {"id": self.id}


def test_explore_service_initialization():
    """Test que el servicio se inicializa correctamente"""
    service = ExploreService()
    assert service is not None
    assert service.repository is not None


def test_explore_service_filter_delegates_to_repository(monkeypatch):
    """Test que el método filter delega correctamente al repositorio"""
    service = ExploreService()

    # Lista de datasets dummy
    dummy_datasets = [DummyDataset(1), DummyDataset(2)]

    # Capturar los argumentos pasados al repositorio
    captured = {}

    def fake_filter(
        title="",
        author="",
        tags="",
        community="",
        publication_type="",
        date_from="",
        date_to="",
        engine_size_min="",
        engine_size_max="",
        consumption_min="",
        consumption_max="",
        sorting="newest",
        **kwargs,
    ):
        captured["args"] = {
            "title": title,
            "author": author,
            "tags": tags,
            "community": community,
            "publication_type": publication_type,
            "date_from": date_from,
            "date_to": date_to,
            "engine_size_min": engine_size_min,
            "engine_size_max": engine_size_max,
            "consumption_min": consumption_min,
            "consumption_max": consumption_max,
            "sorting": sorting,
        }
        return dummy_datasets

    monkeypatch.setattr(service.repository, "filter", fake_filter)

    result = service.filter(title="test", author="john", sorting="oldest")

    assert result == dummy_datasets
    assert captured["args"]["title"] == "test"
    assert captured["args"]["author"] == "john"
    assert captured["args"]["sorting"] == "oldest"


def test_explore_service_filter_empty_params(monkeypatch):
    """Test que filter funciona sin parámetros"""
    service = ExploreService()

    def fake_filter(
        title="",
        author="",
        tags="",
        community="",
        publication_type="",
        date_from="",
        date_to="",
        engine_size_min="",
        engine_size_max="",
        consumption_min="",
        consumption_max="",
        sorting="newest",
        **kwargs,
    ):
        return []

    monkeypatch.setattr(service.repository, "filter", fake_filter)

    result = service.filter()
    assert result == []
