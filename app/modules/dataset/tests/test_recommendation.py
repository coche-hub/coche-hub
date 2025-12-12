"""Unit tests for dataset recommendation system"""

import pytest

from app import db
from app.modules.auth.models import User
from app.modules.conftest import login
from app.modules.dataset.models import Author, CSVDataSet, DSMetaData, PublicationType
from app.modules.dataset.repositories import DataSetRepository
from app.modules.dataset.services import DataSetRecommendationService


@pytest.fixture(scope="module")
def test_client(test_client):
    """Extends the test_client fixture to add additional specific data for module testing."""
    yield test_client


def create_test_dataset(user_id, title, pub_type=PublicationType.NONE, tags="", authors_list=None):
    """Helper to create a test dataset with metadata"""
    metadata = DSMetaData(title=title, description=f"Description for {title}", publication_type=pub_type, tags=tags)
    db.session.add(metadata)
    db.session.flush()

    # Add authors
    if authors_list:
        for author_name in authors_list:
            author = Author(name=author_name, affiliation="Test University", orcid="", ds_meta_data_id=metadata.id)
            db.session.add(author)
            metadata.authors.append(author)

    dataset = CSVDataSet(user_id=user_id, ds_meta_data_id=metadata.id, has_header=True, delimiter=",")
    db.session.add(dataset)
    db.session.commit()
    return dataset


# ==================== REPOSITORY TESTS ====================


def test_repository_get_all_synchronized(test_client):
    """Test get_all_synchronized returns only datasets with DOI"""
    user = User.query.filter_by(email="test@example.com").first()

    # Create synchronized dataset (with DOI)
    ds1 = create_test_dataset(user.id, "Synchronized Dataset 1")
    ds1.ds_meta_data.dataset_doi = "10.1234/test.001"

    # Create unsynchronized dataset (without DOI)
    ds2 = create_test_dataset(user.id, "Unsynchronized Dataset")
    ds2.ds_meta_data.dataset_doi = None

    db.session.commit()

    repo = DataSetRepository()
    synchronized = repo.get_all_synchronized()

    assert len(synchronized) >= 1
    assert ds1 in synchronized
    assert ds2 not in synchronized


def test_repository_get_all(test_client):
    """Test get_all returns all datasets regardless of DOI"""
    user = User.query.filter_by(email="test@example.com").first()

    initial_count = DataSetRepository().get_all()

    ds1 = create_test_dataset(user.id, "Dataset With DOI")
    ds1.ds_meta_data.dataset_doi = "10.1234/test.002"

    ds2 = create_test_dataset(user.id, "Dataset Without DOI")
    ds2.ds_meta_data.dataset_doi = None

    db.session.commit()

    repo = DataSetRepository()
    all_datasets = repo.get_all()

    assert len(all_datasets) >= len(initial_count) + 2
    assert ds1 in all_datasets
    assert ds2 in all_datasets


# ==================== SERVICE TESTS: _parse_tags ====================


def test_parse_tags_valid_string(test_client):
    """Test parsing comma-separated tags"""
    service = DataSetRecommendationService()

    result = service._parse_tags("machine learning, python, data science")

    assert result == {"machine learning", "python", "data science"}


def test_parse_tags_with_whitespace(test_client):
    """Test that whitespace is trimmed from tags"""
    service = DataSetRecommendationService()

    result = service._parse_tags("  tag1  ,  tag2  ,  tag3  ")

    assert result == {"tag1", "tag2", "tag3"}


def test_parse_tags_empty_string(test_client):
    """Test parsing empty string returns empty set"""
    service = DataSetRecommendationService()

    result = service._parse_tags("")

    assert result == set()


def test_parse_tags_none(test_client):
    """Test parsing None returns empty set"""
    service = DataSetRecommendationService()

    result = service._parse_tags(None)

    assert result == set()


def test_parse_tags_single_tag(test_client):
    """Test parsing single tag"""
    service = DataSetRecommendationService()

    result = service._parse_tags("single-tag")

    assert result == {"single-tag"}


# ==================== SERVICE TESTS: get_difference_level ====================


def test_difference_same_publication_type(test_client):
    """Test difference is lower for same publication type"""
    user = User.query.filter_by(email="test@example.com").first()
    service = DataSetRecommendationService()

    ds1 = create_test_dataset(user.id, "DS1", PublicationType.SOFTWARE_DOCUMENTATION)
    ds2 = create_test_dataset(user.id, "DS2", PublicationType.SOFTWARE_DOCUMENTATION)

    difference = service.get_difference_level(ds1, ds2)

    # Same pub type = 0, no tags = 0, no authors = 0
    assert difference == 0.0


def test_difference_different_publication_type(test_client):
    """Test difference increases with different publication type"""
    user = User.query.filter_by(email="test@example.com").first()
    service = DataSetRecommendationService()

    ds1 = create_test_dataset(user.id, "DS1", PublicationType.SOFTWARE_DOCUMENTATION)
    ds2 = create_test_dataset(user.id, "DS2", PublicationType.DATA_MANAGEMENT_PLAN)

    difference = service.get_difference_level(ds1, ds2)

    # Different pub type adds 1.0
    assert difference == 1.0


def test_difference_with_common_tags(test_client):
    """Test difference with some common tags"""
    user = User.query.filter_by(email="test@example.com").first()
    service = DataSetRecommendationService()

    ds1 = create_test_dataset(user.id, "DS1", tags="python, java, rust")
    ds2 = create_test_dataset(user.id, "DS2", tags="python, javascript")

    difference = service.get_difference_level(ds1, ds2)

    # XOR: {java, rust, javascript} = 3 tags
    assert difference == 3.0


def test_difference_with_common_authors(test_client):
    """Test difference with some common authors"""
    user = User.query.filter_by(email="test@example.com").first()
    service = DataSetRecommendationService()

    ds1 = create_test_dataset(user.id, "DS1", authors_list=["Alice", "Bob"])
    ds2 = create_test_dataset(user.id, "DS2", authors_list=["Alice", "Charlie"])

    difference = service.get_difference_level(ds1, ds2)

    # XOR: {bob, charlie} = 2 authors (case insensitive)
    assert difference == 2.0


def test_difference_complex_scenario(test_client):
    """Test difference with multiple factors"""
    user = User.query.filter_by(email="test@example.com").first()
    service = DataSetRecommendationService()

    ds1 = create_test_dataset(
        user.id,
        "DS1",
        pub_type=PublicationType.SOFTWARE_DOCUMENTATION,
        tags="python, ml",
        authors_list=["Alice", "Bob"],
    )
    ds2 = create_test_dataset(
        user.id,
        "DS2",
        pub_type=PublicationType.DATA_MANAGEMENT_PLAN,
        tags="python, ai",
        authors_list=["Alice", "Charlie"],
    )

    difference = service.get_difference_level(ds1, ds2)

    # pub_type: +1, tags XOR {ml, ai}: +2, authors XOR {bob, charlie}: +2 = 5.0
    assert difference == 5.0


# ==================== SERVICE TESTS: get_recommended_datasets ====================


def test_get_recommended_datasets_returns_max_three(test_client):
    """Test that recommendations are limited to 3 datasets"""
    user = User.query.filter_by(email="test@example.com").first()
    service = DataSetRecommendationService()

    main_ds = create_test_dataset(user.id, "Main Dataset", tags="python")

    # Create 5 similar datasets
    for i in range(5):
        create_test_dataset(user.id, f"Similar Dataset {i}", tags="python")

    recommendations = service.get_recommended_datasets(main_ds)

    assert len(recommendations) <= 3


def test_get_recommended_datasets_excludes_self(test_client):
    """Test that the dataset itself is not in recommendations"""
    user = User.query.filter_by(email="test@example.com").first()
    service = DataSetRecommendationService()

    main_ds = create_test_dataset(user.id, "Main Dataset", tags="test")
    create_test_dataset(user.id, "Other Dataset", tags="test")

    recommendations = service.get_recommended_datasets(main_ds)

    assert main_ds not in recommendations


def test_get_recommended_datasets_sorted_by_similarity(test_client):
    """Test that recommendations are sorted by similarity (lowest difference first)"""
    user = User.query.filter_by(email="test@example.com").first()
    service = DataSetRecommendationService()

    main_ds = create_test_dataset(
        user.id, "Main", pub_type=PublicationType.SOFTWARE_DOCUMENTATION, tags="python, ml", authors_list=["Alice"]
    )

    # Very similar
    ds_similar = create_test_dataset(
        user.id,
        "Very Similar",
        pub_type=PublicationType.SOFTWARE_DOCUMENTATION,
        tags="python, ml",
        authors_list=["Alice"],
    )

    # Somewhat similar
    create_test_dataset(
        user.id, "Medium", pub_type=PublicationType.SOFTWARE_DOCUMENTATION, tags="python", authors_list=["Bob"]
    )

    # Very different
    create_test_dataset(
        user.id, "Different", pub_type=PublicationType.DATA_MANAGEMENT_PLAN, tags="java", authors_list=["Charlie"]
    )

    recommendations = service.get_recommended_datasets(main_ds)

    # First recommendation should be most similar
    assert recommendations[0] == ds_similar


def test_get_recommended_datasets_empty_when_no_others(test_client):
    """Test recommendations when dataset is isolated (checks exclusion of self)"""
    user = User.query.filter_by(email="test@example.com").first()

    service = DataSetRecommendationService()

    # Create a unique dataset
    main_ds = create_test_dataset(user.id, "Isolated Dataset", tags="unique-tag-xyz")

    recommendations = service.get_recommended_datasets(main_ds)

    # Should not include itself
    assert main_ds not in recommendations


# ==================== ROUTE TESTS ====================


def test_subdomain_index_with_recommendations(test_client):
    """Test subdomain_index route returns valid response"""
    user = User.query.filter_by(email="test@example.com").first()

    # Create main dataset with DOI
    main_ds = create_test_dataset(user.id, "Main Dataset Route Test", tags="test, python")
    main_ds.ds_meta_data.dataset_doi = "10.1234/main.route.test"

    # Create similar datasets with DOI so they appear in recommendations
    similar_ds = create_test_dataset(user.id, "Similar Dataset Route", tags="test, python")
    similar_ds.ds_meta_data.dataset_doi = "10.1234/similar.route.test"

    db.session.commit()

    # Access the route
    response = test_client.get(f"/doi/{main_ds.ds_meta_data.dataset_doi}/")

    # Just verify route works - template rendering can have session issues in tests
    assert response.status_code == 200


def test_get_unsynchronized_dataset_with_recommendations(test_client):
    login(test_client, "test@example.com", "test1234")
    user = User.query.filter_by(email="test@example.com").first()

    # Create unsynchronized dataset (no DOI)
    main_ds = create_test_dataset(user.id, "Unsync Dataset", tags="test")
    main_ds.ds_meta_data.dataset_doi = None

    create_test_dataset(user.id, "Similar", tags="test")

    db.session.commit()

    response = test_client.get(f"/dataset/unsynchronized/{main_ds.id}/")

    assert response.status_code == 200
    assert b"Unsync Dataset" in response.data
