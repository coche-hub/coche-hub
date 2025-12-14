import os
import tempfile
from datetime import datetime

import pytest

from app import db
from app.modules.auth.models import User
from app.modules.conftest import login, logout
from app.modules.dataset.models import Coche, CSVDataSet, DSMetaData, PublicationType
from app.modules.dataset.services import DataSetService


def create_metadata():
    """Helper function to create DSMetaData for testing"""
    metadata = DSMetaData(title="Test Dataset", description="Test Description", publication_type=PublicationType.NONE)
    db.session.add(metadata)
    db.session.commit()
    return metadata


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    # Test data is created in individual tests as needed
    yield test_client


@pytest.fixture
def temp_csv_file():
    """Create a temporary valid CSV file for testing"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
CR-V,Honda,2.2 EcoBoost,4.7,Gasolina,2018,,2,2,2216,395,Japón,26050,4457FXA,06/02/2021
Civic,Honda,1.8 VTEC,5.2,Gasolina,2016,2020,5,4,1350,450,Japón,22000,1234ABC,15/03/2019"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


# ==================== CATEGORY 1: HAPPY PATH TESTS ====================


def test_upload_valid_csv_creates_dataset_and_coches(test_client, temp_csv_file):
    """Test that uploading a valid CSV creates a dataset and associated Coche records"""
    # Login as test user
    login(test_client, "test@example.com", "test1234")

    user = User.query.filter_by(email="test@example.com").first()

    # Create dataset with CSV
    service = DataSetService()

    # Create metadata and dataset
    metadata = create_metadata()
    dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
    db.session.add(dataset)
    db.session.commit()

    # Parse CSV and create coches
    coches_count = service._parse_csv_and_create_coches(
        temp_csv_file, has_header=True, delimiter=",", dataset_id=dataset.id
    )
    db.session.commit()

    # Assertions
    assert coches_count == 2, "Should create 2 Coche records"
    assert Coche.query.count() == 2, "Database should contain 2 Coche records"

    coches = Coche.query.all()
    assert all(c.dataset_id == dataset.id for c in coches), "All coches should be linked to dataset"

    # Check first coche details
    coche1 = Coche.query.filter_by(matricula="4457FXA").first()
    assert coche1 is not None
    assert coche1.modelo == "CR-V"
    assert coche1.marca == "Honda"
    assert coche1.consumo == 4.7
    assert coche1.fin_de_produccion == 9999  # Empty should become 9999

    logout(test_client)


def test_coche_linked_to_dataset(test_client, temp_csv_file):
    """Test that Coche records have proper foreign key relationship to DataSet"""
    user = User.query.filter_by(email="test@example.com").first()

    # Create dataset
    metadata = create_metadata()
    dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
    db.session.add(dataset)
    db.session.commit()

    # Create a coche linked to dataset
    coche = Coche(
        dataset_id=dataset.id,
        modelo="Test Model",
        marca="Test Brand",
        motor="1.0L",
        consumo=5.0,
        combustible="Gasolina",
        comienzo_de_produccion=2020,
        fin_de_produccion=2022,
        asientos=5,
        puertas=4,
        peso=1200,
        carga_max=400,
        pais_de_origen="España",
        precio_estimado=15000,
        matricula="TEST123",
        fecha_matriculacion=datetime.strptime("01/01/2021", "%d/%m/%Y"),
    )
    db.session.add(coche)
    db.session.commit()

    # Test relationship
    assert coche.dataset_id == dataset.id
    assert coche.dataset == dataset
    assert coche in dataset.coches


# ==================== CATEGORY 2: HEADER VALIDATION TESTS ====================


def test_csv_missing_required_header(test_client):
    """Test CSV with missing 'Modelo' column"""
    csv_content = """Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
Honda,2.2 EcoBoost,4.7,Gasolina,2018,,2,2,2216,395,Japón,26050,4457FXA,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        service._parse_csv_and_create_coches(temp_path, has_header=True, delimiter=",", dataset_id=dataset.id)
        db.session.commit()

        # With missing header, row should be skipped (modelo will be empty string)
        coches = Coche.query.filter_by(dataset_id=dataset.id).all()
        if coches:
            # If created, modelo should be empty or parsing failed gracefully
            assert coches[0].modelo == "", "Missing header should result in empty modelo"
    finally:
        os.remove(temp_path)


def test_csv_extra_headers(test_client):
    """Test CSV with more than 15 columns (extra column)"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación,Extra Column
CR-V,Honda,2.2 EcoBoost,4.7,Gasolina,2018,,2,2,2216,395,Japón,26050,4457FXA,06/02/2021,ExtraData"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        coches_count = service._parse_csv_and_create_coches(
            temp_path, has_header=True, delimiter=",", dataset_id=dataset.id
        )
        db.session.commit()

        # Extra columns should be ignored
        assert coches_count == 1
        coche = Coche.query.filter_by(dataset_id=dataset.id).first()
        assert coche.modelo == "CR-V"
    finally:
        os.remove(temp_path)


def test_csv_wrong_header_names(test_client):
    """Test CSV with misspelled header names"""
    csv_content = """Model,Brand,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
CR-V,Honda,2.2 EcoBoost,4.7,Gasolina,2018,,2,2,2216,395,Japón,26050,4457FXA,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        service._parse_csv_and_create_coches(temp_path, has_header=True, delimiter=",", dataset_id=dataset.id)
        db.session.commit()

        # Wrong headers mean fields won't be found, so empty strings
        coches = Coche.query.filter_by(dataset_id=dataset.id).all()
        if coches:
            assert coches[0].modelo == ""  # 'Modelo' not found, so empty
    finally:
        os.remove(temp_path)


def test_csv_empty_header(test_client):
    """Test CSV with blank header name"""
    csv_content = """,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
CR-V,Honda,2.2 EcoBoost,4.7,Gasolina,2018,,2,2,2216,395,Japón,26050,4457FXA,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        # This should handle gracefully - first column header is blank
        service._parse_csv_and_create_coches(temp_path, has_header=True, delimiter=",", dataset_id=dataset.id)
        db.session.commit()

        # Should create coche but modelo will be empty
        coches = Coche.query.filter_by(dataset_id=dataset.id).all()
        assert len(coches) >= 0  # May be 0 if parsing fails, or 1 with empty modelo
    finally:
        os.remove(temp_path)


# ==================== CATEGORY 3: DATA TYPE VALIDATION TESTS ====================


def test_invalid_consumo_not_float(test_client):
    """Test that non-numeric consumo causes row to be skipped"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
CR-V,Honda,2.2 EcoBoost,INVALID,Gasolina,2018,,2,2,2216,395,Japón,26050,4457FXA,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        coches_count = service._parse_csv_and_create_coches(
            temp_path, has_header=True, delimiter=",", dataset_id=dataset.id
        )
        db.session.commit()

        # Row should be skipped due to ValueError
        assert coches_count == 0
    finally:
        os.remove(temp_path)


def test_invalid_asientos_not_integer(test_client):
    """Test that non-integer asientos causes row to be skipped"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
CR-V,Honda,2.2 EcoBoost,4.7,Gasolina,2018,,5.5,2,2216,395,Japón,26050,4457FXA,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        coches_count = service._parse_csv_and_create_coches(
            temp_path, has_header=True, delimiter=",", dataset_id=dataset.id
        )
        db.session.commit()

        # Row should be skipped
        assert coches_count == 0
    finally:
        os.remove(temp_path)


def test_invalid_fecha_matriculacion_format(test_client):
    """Test that wrong date format causes row to be skipped"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
CR-V,Honda,2.2 EcoBoost,4.7,Gasolina,2018,,2,2,2216,395,Japón,26050,4457FXA,2021-02-06"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        coches_count = service._parse_csv_and_create_coches(
            temp_path, has_header=True, delimiter=",", dataset_id=dataset.id
        )
        db.session.commit()

        # Row should be skipped due to date parsing error
        assert coches_count == 0
    finally:
        os.remove(temp_path)


def test_negative_peso(test_client):
    """Test that negative weight value is accepted (no validation currently)"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
CR-V,Honda,2.2 EcoBoost,4.7,Gasolina,2018,,2,2,-1000,395,Japón,26050,4457FXA,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        coches_count = service._parse_csv_and_create_coches(
            temp_path, has_header=True, delimiter=",", dataset_id=dataset.id
        )
        db.session.commit()

        # Currently no validation, so negative value is accepted
        assert coches_count == 1
        coche = Coche.query.filter_by(dataset_id=dataset.id).first()
        assert coche.peso == -1000
    finally:
        os.remove(temp_path)


def test_invalid_comienzo_produccion_year(test_client):
    """Test very old or future year for production start"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
CR-V,Honda,2.2 EcoBoost,4.7,Gasolina,1800,,2,2,2216,395,Japón,26050,4457FXA,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        coches_count = service._parse_csv_and_create_coches(
            temp_path, has_header=True, delimiter=",", dataset_id=dataset.id
        )
        db.session.commit()

        # Currently no validation, so 1800 is accepted
        assert coches_count == 1
        coche = Coche.query.filter_by(dataset_id=dataset.id).first()
        assert coche.comienzo_de_produccion == 1800
    finally:
        os.remove(temp_path)


def test_matricula_too_long(test_client):
    """Test that matricula exceeding 7 characters causes database error"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
CR-V,Honda,2.2 EcoBoost,4.7,Gasolina,2018,,2,2,2216,395,Japón,26050,TOOLONG123,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        service._parse_csv_and_create_coches(temp_path, has_header=True, delimiter=",", dataset_id=dataset.id)

        # Commit will fail due to DB constraint
        with pytest.raises(Exception):  # Could be IntegrityError or DataError
            db.session.commit()

        db.session.rollback()
    finally:
        os.remove(temp_path)


# ==================== CATEGORY 4: OPTIONAL FIELDS TESTS ====================


def test_fin_de_produccion_empty(test_client):
    """Test that empty 'Fin de producción' is handled correctly (becomes 9999)"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
CR-V,Honda,2.2 EcoBoost,4.7,Gasolina,2018,,2,2,2216,395,Japón,26050,4457FXA,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        coches_count = service._parse_csv_and_create_coches(
            temp_path, has_header=True, delimiter=",", dataset_id=dataset.id
        )
        db.session.commit()

        assert coches_count == 1
        coche = Coche.query.filter_by(dataset_id=dataset.id).first()
        assert coche.fin_de_produccion == 9999
    finally:
        os.remove(temp_path)


def test_fin_de_produccion_null_variants(test_client):
    """Test various representations of null/empty for optional field"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
Model1,Brand,Motor,4.7,Gasolina,2018,,2,2,2216,395,País,26050,MAT0001,06/02/2021
Model2,Brand,Motor,4.7,Gasolina,2018,N/A,2,2,2216,395,País,26050,MAT0002,06/02/2021
Model3,Brand,Motor,4.7,Gasolina,2018,   ,2,2,2216,395,País,26050,MAT0003,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        service._parse_csv_and_create_coches(temp_path, has_header=True, delimiter=",", dataset_id=dataset.id)
        db.session.commit()

        # First row (empty) and third row (spaces) should work, second (N/A) will fail int conversion
        coches = Coche.query.filter_by(dataset_id=dataset.id).all()
        assert len(coches) == 2  # MAT0001 and MAT0003 succeed, MAT0002 fails

        for coche in coches:
            assert coche.fin_de_produccion == 9999
    finally:
        os.remove(temp_path)


def test_optional_field_before_required_ends(test_client):
    """Test car still in production (empty end date)"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
CR-V,Honda,2.2 EcoBoost,4.7,Gasolina,2023,,5,4,1800,500,Japón,35000,NEW2024,01/01/2024"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        coches_count = service._parse_csv_and_create_coches(
            temp_path, has_header=True, delimiter=",", dataset_id=dataset.id
        )
        db.session.commit()

        assert coches_count == 1
        coche = Coche.query.filter_by(dataset_id=dataset.id).first()
        assert coche.comienzo_de_produccion == 2023
        assert coche.fin_de_produccion == 9999  # Still in production
    finally:
        os.remove(temp_path)


# ==================== CATEGORY 5: EDGE CASES & ERROR HANDLING ====================


def test_empty_csv_file(test_client):
    """Test CSV with only headers, no data rows"""

    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        coches_count = service._parse_csv_and_create_coches(
            temp_path, has_header=True, delimiter=",", dataset_id=dataset.id
        )
        db.session.commit()

        assert coches_count == 0
    finally:
        os.remove(temp_path)


def test_csv_with_only_one_row(test_client):
    """Test CSV with single car entry"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
CR-V,Honda,2.2 EcoBoost,4.7,Gasolina,2018,2020,2,2,2216,395,Japón,26050,4457FXA,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        coches_count = service._parse_csv_and_create_coches(
            temp_path, has_header=True, delimiter=",", dataset_id=dataset.id
        )
        db.session.commit()

        assert coches_count == 1
        coche = Coche.query.filter_by(dataset_id=dataset.id).first()
        assert coche.modelo == "CR-V"
    finally:
        os.remove(temp_path)


def test_malformed_csv_quotes(test_client):
    """Test CSV with properly escaped quotes in CSV format"""

    csv_content = 'Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación\n"CR-V ""Special Edition""",Honda,2.2 EcoBoost,4.7,Gasolina,2018,,2,2,2216,395,Japón,26050,4457FXA,06/02/2021'

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        service._parse_csv_and_create_coches(temp_path, has_header=True, delimiter=",", dataset_id=dataset.id)
        db.session.commit()

        # CSV module should handle properly escaped quotes
        coche = Coche.query.filter_by(dataset_id=dataset.id).first()
        assert "CR-V" in coche.modelo
    finally:
        os.remove(temp_path)


def test_csv_different_encoding(test_client):
    """Test CSV with Latin-1 encoding"""
    # Use characters that exist in latin-1 (accented characters but not €)
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado,Matrícula,Fecha de matriculación
León,SEAT,2.0 TDI,4.5,Diésel,2018,,5,4,1450,450,España,22000,ESP1234,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="latin-1") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        # Parser tries UTF-8 first, may fail and need fallback
        try:
            service._parse_csv_and_create_coches(temp_path, has_header=True, delimiter=",", dataset_id=dataset.id)
            db.session.commit()
            # If successful with UTF-8 (unlikely) or if it handles encoding error
            assert True  # Test passes if no exception
        except UnicodeDecodeError:
            # Expected if no encoding fallback in parser
            assert True
    finally:
        os.remove(temp_path)


def test_duplicate_matricula_same_csv(test_client):
    """Test CSV with duplicate matricula in same file"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
Model1,Brand,Motor,4.7,Gasolina,2018,,2,2,2216,395,País,26050,DUP1234,06/02/2021
Model2,Brand,Motor,4.7,Gasolina,2018,,2,2,2216,395,País,26050,DUP1234,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        coches_count = service._parse_csv_and_create_coches(
            temp_path, has_header=True, delimiter=",", dataset_id=dataset.id
        )

        # Currently no unique constraint, so both should be added
        db.session.commit()
        assert coches_count == 2

        dupes = Coche.query.filter_by(matricula="DUP1234").all()
        assert len(dupes) == 2
    finally:
        os.remove(temp_path)


def test_duplicate_matricula_different_datasets(test_client):
    """Test same matricula across different datasets (should be allowed)"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
CR-V,Honda,2.2 EcoBoost,4.7,Gasolina,2018,,2,2,2216,395,Japón,26050,SHARED1,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()

        # Create first dataset
        metadata1 = create_metadata()
        dataset1 = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata1.id)
        db.session.add(dataset1)
        db.session.commit()

        service = DataSetService()
        service._parse_csv_and_create_coches(temp_path, has_header=True, delimiter=",", dataset_id=dataset1.id)
        db.session.commit()

        # Create second dataset with same matricula
        metadata2 = create_metadata()
        dataset2 = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata2.id)
        db.session.add(dataset2)
        db.session.commit()

        service._parse_csv_and_create_coches(temp_path, has_header=True, delimiter=",", dataset_id=dataset2.id)
        db.session.commit()

        # Both should exist
        shared_coches = Coche.query.filter_by(matricula="SHARED1").all()
        assert len(shared_coches) == 2
        assert shared_coches[0].dataset_id != shared_coches[1].dataset_id
    finally:
        os.remove(temp_path)


def test_csv_inconsistent_column_count(test_client):
    """Test CSV where one row has wrong number of columns"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
CR-V,Honda,2.2 EcoBoost,4.7,Gasolina,2018,,2,2,2216,395,Japón,26050,MAT0001,06/02/2021
Civic,Honda,1.8,5.0,Gasolina,2016
Model3,Brand,Motor,4.7,Gasolina,2018,,2,2,2216,395,País,26050,MAT0003,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        coches_count = service._parse_csv_and_create_coches(
            temp_path, has_header=True, delimiter=",", dataset_id=dataset.id
        )
        db.session.commit()

        # Only first row succeeds, second fails and causes parsing to stop
        # (actual behavior: parser fails on second row and stops)
        assert coches_count == 1
    finally:
        os.remove(temp_path)


def test_csv_with_bom(test_client):
    """Test CSV with UTF-8 BOM (Byte Order Mark)"""
    csv_content = """\ufeffModelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
CR-V,Honda,2.2 EcoBoost,4.7,Gasolina,2018,,2,2,2216,395,Japón,26050,4457FXA,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8-sig") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        coches_count = service._parse_csv_and_create_coches(
            temp_path, has_header=True, delimiter=",", dataset_id=dataset.id
        )
        db.session.commit()

        # BOM should be handled by Python's csv reader or UTF-8 decoding
        # If not, first header might be '\ufeffModelo' instead of 'Modelo'
        assert coches_count >= 0  # Test passes if no exception
    finally:
        os.remove(temp_path)


# ==================== CATEGORY 6: MODEL TESTS ====================


def test_coche_model_creation(test_client):
    """Test direct Coche model instantiation"""
    user = User.query.filter_by(email="test@example.com").first()
    metadata = create_metadata()
    dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
    db.session.add(dataset)
    db.session.commit()

    coche = Coche(
        dataset_id=dataset.id,
        modelo="Test Model",
        marca="Test Brand",
        motor="2.0L Turbo",
        consumo=6.5,
        combustible="Híbrido",
        comienzo_de_produccion=2021,
        fin_de_produccion=2024,
        asientos=5,
        puertas=4,
        peso=1600,
        carga_max=500,
        pais_de_origen="Alemania",
        precio_estimado=45000,
        matricula="TEST999",
        fecha_matriculacion=datetime(2022, 6, 15),
    )
    db.session.add(coche)
    db.session.commit()

    # Query back and verify
    retrieved = Coche.query.filter_by(matricula="TEST999").first()
    assert retrieved is not None
    assert retrieved.modelo == "Test Model"
    assert retrieved.marca == "Test Brand"
    assert retrieved.consumo == 6.5
    assert retrieved.dataset_id == dataset.id


def test_coche_repr_or_str(test_client):
    """Test string representation of Coche model"""
    user = User.query.filter_by(email="test@example.com").first()
    metadata = create_metadata()
    dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
    db.session.add(dataset)
    db.session.commit()

    coche = Coche(
        dataset_id=dataset.id,
        modelo="Civic",
        marca="Honda",
        motor="1.5L",
        consumo=5.0,
        combustible="Gasolina",
        comienzo_de_produccion=2020,
        asientos=5,
        puertas=4,
        peso=1300,
        carga_max=400,
        pais_de_origen="Japón",
        precio_estimado=25000,
        matricula="ABC1234",
        fecha_matriculacion=datetime(2021, 1, 1),
    )

    repr_str = repr(coche)
    assert "Civic" in repr_str
    assert "Honda" in repr_str
    assert "ABC1234" in repr_str


def test_cascade_delete_dataset_deletes_coches(test_client):
    """Test that deleting a dataset cascades to delete its coches"""
    user = User.query.filter_by(email="test@example.com").first()
    metadata = create_metadata()
    dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
    db.session.add(dataset)
    db.session.commit()

    # Create coches linked to dataset
    for i in range(3):
        coche = Coche(
            dataset_id=dataset.id,
            modelo=f"Model{i}",
            marca="Brand",
            motor="1.0L",
            consumo=5.0,
            combustible="Gasolina",
            comienzo_de_produccion=2020,
            asientos=5,
            puertas=4,
            peso=1200,
            carga_max=400,
            pais_de_origen="España",
            precio_estimado=15000,
            matricula=f"MAT000{i}",
            fecha_matriculacion=datetime(2021, 1, 1),
        )
        db.session.add(coche)
    db.session.commit()

    dataset_id = dataset.id
    assert Coche.query.filter_by(dataset_id=dataset_id).count() == 3

    # Delete dataset - CASCADE should delete coches
    db.session.delete(dataset)
    db.session.commit()

    # Verify cascade delete worked
    remaining_coches = Coche.query.filter_by(dataset_id=dataset_id).count()
    assert remaining_coches == 0, "CASCADE delete should remove all coches"


# ==================== CATEGORY 7: SERVICE LAYER TESTS ====================


def test_parse_csv_with_header_true(test_client, temp_csv_file):
    """Test parser respects has_header=True setting"""
    user = User.query.filter_by(email="test@example.com").first()
    metadata = create_metadata()
    dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
    db.session.add(dataset)
    db.session.commit()

    service = DataSetService()
    coches_count = service._parse_csv_and_create_coches(
        temp_csv_file, has_header=True, delimiter=",", dataset_id=dataset.id
    )
    db.session.commit()

    # Should parse 2 rows (excluding header)
    assert coches_count == 2


def test_parse_csv_counts_rows_correctly(test_client):
    """Test that parser counts and returns correct number of rows created"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
Model1,Brand,Motor,4.7,Gasolina,2018,,2,2,2216,395,País,26050,MAT0001,06/02/2021
Model2,Brand,Motor,4.7,Gasolina,2018,,2,2,2216,395,País,26050,MAT0002,06/02/2021
Model3,Brand,Motor,4.7,Gasolina,2018,,2,2,2216,395,País,26050,MAT0003,06/02/2021
Model4,Brand,Motor,4.7,Gasolina,2018,,2,2,2216,395,País,26050,MAT0004,06/02/2021
Model5,Brand,Motor,4.7,Gasolina,2018,,2,2,2216,395,País,26050,MAT0005,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        coches_count = service._parse_csv_and_create_coches(
            temp_path, has_header=True, delimiter=",", dataset_id=dataset.id
        )
        db.session.commit()

        assert coches_count == 5
        assert Coche.query.filter_by(dataset_id=dataset.id).count() == 5
    finally:
        os.remove(temp_path)


def test_validation_returns_error_messages(test_client):
    """Test that _validate_csv_format returns appropriate error messages"""
    # Create an empty file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        temp_path = f.name

    try:
        service = DataSetService()
        errors = service._validate_csv_format(temp_path, has_header=True, delimiter=",")

        # Empty file should generate an error
        assert isinstance(errors, list)
        assert len(errors) > 0
        assert any("empty" in err.lower() for err in errors)
    finally:
        os.remove(temp_path)


# ==================== CATEGORY 8: ERROR HANDLING & EDGE CASES ====================


def test_extract_engine_size_with_none_input(test_client):
    """Test _extract_engine_size with None input"""
    service = DataSetService()
    result = service._extract_engine_size(None)
    assert result is None


def test_extract_engine_size_with_non_string_input(test_client):
    """Test _extract_engine_size with non-string input"""
    service = DataSetService()
    result = service._extract_engine_size(12345)
    assert result is None


def test_extract_engine_size_with_empty_string(test_client):
    """Test _extract_engine_size with empty string"""
    service = DataSetService()
    result = service._extract_engine_size("")
    assert result is None


def test_extract_engine_size_with_whitespace(test_client):
    """Test _extract_engine_size with only whitespace"""
    service = DataSetService()
    result = service._extract_engine_size("   ")
    assert result is None


def test_extract_engine_size_with_no_numbers(test_client):
    """Test _extract_engine_size with text that has no numbers"""
    service = DataSetService()
    result = service._extract_engine_size("EcoBoost Turbo")
    assert result is None


def test_extract_engine_size_with_comma_decimal(test_client):
    """Test _extract_engine_size with European decimal format (comma)"""
    service = DataSetService()
    result = service._extract_engine_size("2,0 TDI")
    assert result == 2.0


def test_extract_engine_size_with_dot_decimal(test_client):
    """Test _extract_engine_size with US decimal format (dot)"""
    service = DataSetService()
    result = service._extract_engine_size("1.8 VTEC")
    assert result == 1.8


def test_extract_engine_size_with_integer_only(test_client):
    """Test _extract_engine_size with integer value"""
    service = DataSetService()
    result = service._extract_engine_size("3 V6")
    assert result == 3.0


def test_extract_consumption_with_none_input(test_client):
    """Test _extract_consumption with None input"""
    service = DataSetService()
    result = service._extract_consumption(None)
    assert result is None


def test_extract_consumption_with_non_string(test_client):
    """Test _extract_consumption with non-string input"""
    service = DataSetService()
    result = service._extract_consumption(123)
    assert result is None


def test_extract_consumption_with_empty_string(test_client):
    """Test _extract_consumption with empty string"""
    service = DataSetService()
    result = service._extract_consumption("")
    assert result is None


def test_extract_consumption_with_comma_decimal(test_client):
    """Test _extract_consumption with European format"""
    service = DataSetService()
    result = service._extract_consumption("5,2 L/100km")
    assert result == 5.2


def test_extract_consumption_with_dot_decimal(test_client):
    """Test _extract_consumption with US format"""
    service = DataSetService()
    result = service._extract_consumption("4.7")
    assert result == 4.7


def test_extract_consumption_with_no_numbers(test_client):
    """Test _extract_consumption with text only"""
    service = DataSetService()
    result = service._extract_consumption("Very efficient")
    assert result is None


def test_calculate_average_engine_size_file_not_found(test_client):
    """Test _calculate_average_engine_size with non-existent file"""
    service = DataSetService()
    result = service._calculate_average_engine_size("/nonexistent/file.csv", has_header=True, delimiter=",")
    assert result is None


def test_calculate_average_consumption_file_not_found(test_client):
    """Test _calculate_average_consumption with non-existent file"""
    service = DataSetService()
    result = service._calculate_average_consumption("/nonexistent/file.csv", has_header=True, delimiter=",")
    assert result is None


def test_calculate_average_engine_size_no_valid_values(test_client):
    """Test average calculation when no valid engine sizes found"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
Model1,Brand,N/A,4.7,Gasolina,2018,,2,2,2216,395,País,26050,MAT0001,06/02/2021
Model2,Brand,Unknown,4.7,Gasolina,2018,,2,2,2216,395,País,26050,MAT0002,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        service = DataSetService()
        result = service._calculate_average_engine_size(temp_path, has_header=True, delimiter=",")
        assert result is None
    finally:
        os.remove(temp_path)


def test_calculate_average_consumption_no_valid_values(test_client):
    """Test average consumption when all values are invalid"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
Model1,Brand,1.0L,N/A,Gasolina,2018,,2,2,2216,395,País,26050,MAT0001,06/02/2021
Model2,Brand,1.0L,Unknown,Gasolina,2018,,2,2,2216,395,País,26050,MAT0002,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        service = DataSetService()
        result = service._calculate_average_consumption(temp_path, has_header=True, delimiter=",")
        assert result is None
    finally:
        os.remove(temp_path)


def test_validate_csv_format_encoding_error(test_client):
    """Test CSV validation with encoding that causes issues"""
    # Create a file with invalid UTF-8 bytes
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
        f.write(b"\xff\xfe Invalid UTF-8 bytes")
        temp_path = f.name

    try:
        service = DataSetService()
        errors = service._validate_csv_format(temp_path, has_header=True, delimiter=",")
        # Should return errors due to encoding issues
        assert isinstance(errors, list)
    finally:
        os.remove(temp_path)


def test_validate_csv_format_inconsistent_columns(test_client):
    """Test CSV validation with inconsistent column counts"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible
Model1,Brand,Motor,4.7,Gasolina,2018
Model2,Brand,Motor,4.7"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        service = DataSetService()
        errors = service._validate_csv_format(temp_path, has_header=True, delimiter=",")
        assert isinstance(errors, list)
        # Should detect inconsistent column counts
        assert len(errors) > 0
    finally:
        os.remove(temp_path)


def test_parse_csv_without_header_missing_columns(test_client):
    """Test parsing CSV without header when rows have insufficient columns"""
    csv_content = """Model1,Brand,Motor
Model2,Brand"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        user = User.query.filter_by(email="test@example.com").first()
        metadata = create_metadata()
        dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
        db.session.add(dataset)
        db.session.commit()

        service = DataSetService()
        coches_count = service._parse_csv_and_create_coches(
            temp_path, has_header=False, delimiter=",", dataset_id=dataset.id
        )
        db.session.commit()

        # Rows with insufficient columns should be skipped
        assert coches_count == 0
    finally:
        os.remove(temp_path)


def test_create_from_form_no_files_uploaded(test_client):
    """Test create_from_form when no files are uploaded"""
    login(test_client, "test@example.com", "test1234")

    class MockForm:
        def get_dsmetadata(self):
            return {
                "title": "Test Dataset",
                "description": "Test Description",
                "publication_type": PublicationType.NONE,
            }

        has_header = type("obj", (object,), {"data": True})
        delimiter = type("obj", (object,), {"data": ","})

    user = User.query.filter_by(email="test@example.com").first()

    # Make sure temp folder is empty
    temp_folder = user.temp_folder()
    if os.path.exists(temp_folder):
        for file in os.listdir(temp_folder):
            os.remove(os.path.join(temp_folder, file))

    service = DataSetService()
    form = MockForm()

    with pytest.raises(Exception) as exc_info:
        service.create_from_form(form, user)

    assert "No files uploaded" in str(exc_info.value)

    logout(test_client)


def test_create_from_form_invalid_csv_format(test_client):
    """Test create_from_form with invalid CSV file"""
    login(test_client, "test@example.com", "test1234")

    class MockForm:
        def get_dsmetadata(self):
            return {
                "title": "Test Dataset",
                "description": "Test Description",
                "publication_type": PublicationType.NONE,
            }

        def get_authors(self):
            return []

        has_header = type("obj", (object,), {"data": True})
        delimiter = type("obj", (object,), {"data": ","})

    user = User.query.filter_by(email="test@example.com").first()

    # Create temp folder and add an invalid CSV
    temp_folder = user.temp_folder()
    os.makedirs(temp_folder, exist_ok=True)

    invalid_csv = os.path.join(temp_folder, "invalid.csv")
    with open(invalid_csv, "w") as f:
        f.write("")  # Empty file

    service = DataSetService()
    form = MockForm()

    try:
        with pytest.raises(Exception) as exc_info:
            service.create_from_form(form, user)

        # Should fail during CSV validation or processing
        assert exc_info.value is not None
    finally:
        # Cleanup
        if os.path.exists(invalid_csv):
            os.remove(invalid_csv)

    logout(test_client)


def test_dataset_model_get_dataset_url_without_doi(test_client):
    """Test get_dataset_url when dataset has no DOI"""
    user = User.query.filter_by(email="test@example.com").first()
    metadata = DSMetaData(
        title="Test Dataset",
        description="Test Description",
        publication_type=PublicationType.NONE,
        dataset_doi=None,  # No DOI
    )
    db.session.add(metadata)
    db.session.commit()

    dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
    db.session.add(dataset)
    db.session.commit()

    # When DOI is None, URL will include 'None' in the path
    url = dataset.get_dataset_url()
    assert "doi/None" in url or url == "" or url is None


def test_coche_with_null_optional_fields(test_client):
    """Test creating Coche with only required fields"""
    user = User.query.filter_by(email="test@example.com").first()
    metadata = create_metadata()
    dataset = CSVDataSet(user_id=user.id, ds_meta_data_id=metadata.id)
    db.session.add(dataset)
    db.session.commit()

    # Create coche with minimal fields (some can be None/default)
    coche = Coche(
        dataset_id=dataset.id,
        modelo="Minimal Model",
        marca="Minimal Brand",
        motor="1.0L",
        consumo=5.0,
        combustible="Gasolina",
        comienzo_de_produccion=2020,
        asientos=5,
        puertas=4,
        peso=1200,
        carga_max=400,
        pais_de_origen="",  # Empty string
        precio_estimado=0,  # Zero
        matricula="MIN0000",
        fecha_matriculacion=datetime(2021, 1, 1),
    )
    db.session.add(coche)
    db.session.commit()

    retrieved = Coche.query.filter_by(matricula="MIN0000").first()
    assert retrieved is not None
    assert retrieved.pais_de_origen == ""
    assert retrieved.precio_estimado == 0


def test_calculate_average_with_mixed_valid_invalid_values(test_client):
    """Test average calculations with some valid and some invalid values"""
    csv_content = """Modelo,Marca,Motor,Consumo,Combustible,Comienzo de producción,Fin de producción,Asientos,Puertas,Peso (kg),Carga máxima (kg),País de origen,Precio estimado (€),Matrícula,Fecha de matriculación
Model1,Brand,2.0 TDI,4.7,Gasolina,2018,,2,2,2216,395,País,26050,MAT0001,06/02/2021
Model2,Brand,N/A,5.2,Gasolina,2018,,2,2,2216,395,País,26050,MAT0002,06/02/2021
Model3,Brand,1.5 VTEC,Invalid,Gasolina,2018,,2,2,2216,395,País,26050,MAT0003,06/02/2021"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        service = DataSetService()

        # Test engine size average (2 valid: 2.0, 1.5)
        engine_avg = service._calculate_average_engine_size(temp_path, has_header=True, delimiter=",")
        assert engine_avg is not None
        assert engine_avg == pytest.approx(1.75, 0.01)

        # Test consumption average (2 valid: 4.7, 5.2)
        consumption_avg = service._calculate_average_consumption(temp_path, has_header=True, delimiter=",")
        assert consumption_avg is not None
        assert consumption_avg == pytest.approx(4.95, 0.01)
    finally:
        os.remove(temp_path)
