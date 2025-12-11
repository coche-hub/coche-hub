from unittest.mock import MagicMock, patch

from app.modules.explore.repositories import ExploreRepository


def test_repository_initialization():
    """Test que el repositorio se inicializa correctamente"""
    repo = ExploreRepository()
    assert repo is not None


def test_filter_with_title(monkeypatch):
    """Test filtro por título"""
    repo = ExploreRepository()

    # Mock completo del sistema de queries
    mock_dataset = MagicMock()
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.distinct.return_value = mock_query
    mock_query.all.return_value = [mock_dataset]

    with patch("app.modules.explore.repositories.DataSet") as mock_ds:
        mock_ds.query = mock_query
        repo.filter(title="test")
        assert mock_query.filter.called


def test_filter_with_author(monkeypatch):
    """Test filtro por autor"""
    repo = ExploreRepository()

    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.outerjoin.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.distinct.return_value = mock_query
    mock_query.all.return_value = []

    with patch("app.modules.explore.repositories.DataSet") as mock_ds:
        mock_ds.query = mock_query
        repo.filter(author="john")
        assert mock_query.outerjoin.called


def test_filter_with_single_tag(monkeypatch):
    """Test filtro por un solo tag"""
    repo = ExploreRepository()

    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.distinct.return_value = mock_query
    mock_query.all.return_value = []

    with patch("app.modules.explore.repositories.DataSet") as mock_ds:
        mock_ds.query = mock_query
        repo.filter(tags="python")
        # Debe filtrar al menos una vez
        assert mock_query.filter.call_count >= 1


def test_filter_with_multiple_tags(monkeypatch):
    """Test filtro por múltiples tags"""
    repo = ExploreRepository()

    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.distinct.return_value = mock_query
    mock_query.all.return_value = []

    with patch("app.modules.explore.repositories.DataSet") as mock_ds:
        mock_ds.query = mock_query
        repo.filter(tags="python, ai, ml")
        # Debe filtrar varias veces (una por tag más el filtro base)
        assert mock_query.filter.call_count >= 3


def test_filter_with_valid_community(monkeypatch):
    """Test filtro por comunidad con ID válido"""
    repo = ExploreRepository()

    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.distinct.return_value = mock_query
    mock_query.all.return_value = []

    with patch("app.modules.explore.repositories.DataSet") as mock_ds:
        mock_ds.query = mock_query
        repo.filter(community="5")
        # Debe hacer join con CommunityDataset
        assert mock_query.join.call_count >= 2  # join DSMetaData + join CommunityDataset


def test_filter_with_invalid_community(monkeypatch):
    """Test que comunidad inválida no causa error"""
    repo = ExploreRepository()

    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.distinct.return_value = mock_query
    mock_query.all.return_value = []

    with patch("app.modules.explore.repositories.DataSet") as mock_ds:
        mock_ds.query = mock_query
        # No debe lanzar excepción
        result = repo.filter(community="invalid")
        assert isinstance(result, list)


def test_filter_with_date_from(monkeypatch):
    """Test filtro por fecha desde"""
    repo = ExploreRepository()

    mock_query = MagicMock()
    mock_created_at = MagicMock()
    mock_created_at.__ge__ = MagicMock(return_value=True)

    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.distinct.return_value = mock_query
    mock_query.all.return_value = []

    with patch("app.modules.explore.repositories.DataSet") as mock_ds:
        mock_ds.query = mock_query
        mock_ds.created_at = mock_created_at
        repo.filter(date_from="2024-01-01")
        assert mock_query.filter.call_count >= 2  # Base filter + date_from filter


def test_filter_with_date_to(monkeypatch):
    """Test filtro por fecha hasta"""
    repo = ExploreRepository()

    mock_query = MagicMock()
    mock_created_at = MagicMock()
    mock_created_at.__lt__ = MagicMock(return_value=True)

    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.distinct.return_value = mock_query
    mock_query.all.return_value = []

    with patch("app.modules.explore.repositories.DataSet") as mock_ds:
        mock_ds.query = mock_query
        mock_ds.created_at = mock_created_at
        repo.filter(date_to="2024-12-31")
        assert mock_query.filter.call_count >= 2


def test_filter_with_date_range(monkeypatch):
    """Test filtro por rango de fechas"""
    repo = ExploreRepository()

    mock_query = MagicMock()
    mock_created_at = MagicMock()
    mock_created_at.__ge__ = MagicMock(return_value=True)
    mock_created_at.__lt__ = MagicMock(return_value=True)

    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.distinct.return_value = mock_query
    mock_query.all.return_value = []

    with patch("app.modules.explore.repositories.DataSet") as mock_ds:
        mock_ds.query = mock_query
        mock_ds.created_at = mock_created_at
        repo.filter(date_from="2024-01-01", date_to="2024-12-31")
        # Base filter + date_from + date_to
        assert mock_query.filter.call_count >= 3


def test_filter_with_engine_size_min(monkeypatch):
    """Test filtro por tamaño mínimo de motor"""
    repo = ExploreRepository()

    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.distinct.return_value = mock_query
    mock_query.all.return_value = []

    with patch("app.modules.explore.repositories.DataSet") as mock_ds:
        mock_ds.query = mock_query
        repo.filter(engine_size_min="2.0")
        assert mock_query.filter.called


def test_filter_with_engine_size_range(monkeypatch):
    """Test filtro por rango de tamaño de motor"""
    repo = ExploreRepository()

    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.distinct.return_value = mock_query
    mock_query.all.return_value = []

    with patch("app.modules.explore.repositories.DataSet") as mock_ds:
        mock_ds.query = mock_query
        repo.filter(engine_size_min="2.0", engine_size_max="5.0")
        assert mock_query.filter.called


def test_filter_with_consumption_min(monkeypatch):
    """Test filtro por consumo mínimo"""
    repo = ExploreRepository()

    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.distinct.return_value = mock_query
    mock_query.all.return_value = []

    with patch("app.modules.explore.repositories.DataSet") as mock_ds:
        mock_ds.query = mock_query
        repo.filter(consumption_min="5.0")
        assert mock_query.filter.called


def test_filter_sorting_newest(monkeypatch):
    """Test ordenamiento por más reciente (default)"""
    repo = ExploreRepository()

    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.distinct.return_value = mock_query
    mock_query.all.return_value = []

    with patch("app.modules.explore.repositories.DataSet") as mock_ds:
        mock_ds.query = mock_query
        repo.filter(sorting="newest")
        assert mock_query.order_by.called


def test_filter_sorting_oldest(monkeypatch):
    """Test ordenamiento por más antiguo"""
    repo = ExploreRepository()

    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.distinct.return_value = mock_query
    mock_query.all.return_value = []

    with patch("app.modules.explore.repositories.DataSet") as mock_ds:
        mock_ds.query = mock_query
        repo.filter(sorting="oldest")
        assert mock_query.order_by.called


def test_filter_combined_filters(monkeypatch):
    """Test con múltiples filtros combinados"""
    repo = ExploreRepository()

    mock_query = MagicMock()
    mock_created_at = MagicMock()
    mock_created_at.__ge__ = MagicMock(return_value=True)

    mock_query.join.return_value = mock_query
    mock_query.outerjoin.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.distinct.return_value = mock_query
    mock_query.all.return_value = []

    with patch("app.modules.explore.repositories.DataSet") as mock_ds:
        mock_ds.query = mock_query
        mock_ds.created_at = mock_created_at
        repo.filter(title="test", author="john", tags="python", date_from="2024-01-01", sorting="oldest")
        # Debe haber múltiples llamadas a filter
        assert mock_query.filter.call_count >= 4
        assert mock_query.order_by.called
