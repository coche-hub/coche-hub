import hashlib
import logging
import os
import shutil
import uuid
from typing import Optional

from flask import request

from app.modules.auth.services import AuthenticationService
from app.modules.dataset.models import Author, CSVDataSet, DataSet, DSMetaData, DSMetrics, DSViewRecord, Coche
from app.modules.dataset.repositories import (
    AuthorRepository,
    DataSetRepository,
    DOIMappingRepository,
    DSDownloadRecordRepository,
    DSMetaDataRepository,
    DSViewRecordRepository,
)
from app.modules.featuremodel.repositories import FeatureModelRepository, FMMetaDataRepository
from app.modules.hubfile.models import Hubfile
from app.modules.hubfile.repositories import (
    HubfileDownloadRecordRepository,
    HubfileRepository,
    HubfileViewRecordRepository,
)
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


def calculate_checksum_and_size(file_path):
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as file:
        content = file.read()
        hash_md5 = hashlib.md5(content).hexdigest()
        return hash_md5, file_size


class DataSetService(BaseService):
    def __init__(self):
        super().__init__(DataSetRepository())
        self.feature_model_repository = FeatureModelRepository()
        self.author_repository = AuthorRepository()
        self.dsmetadata_repository = DSMetaDataRepository()
        self.fmmetadata_repository = FMMetaDataRepository()
        self.dsdownloadrecord_repository = DSDownloadRecordRepository()
        self.hubfiledownloadrecord_repository = HubfileDownloadRecordRepository()
        self.hubfilerepository = HubfileRepository()
        self.dsviewrecord_repostory = DSViewRecordRepository()
        self.hubfileviewrecord_repository = HubfileViewRecordRepository()

    # Removed: move_feature_models - replaced by move_files

    def move_files(self, dataset: DataSet):
        """
        Move uploaded files from temp folder to dataset folder
        """
        current_user = dataset.user
        source_dir = current_user.temp_folder()

        # Create destination directory
        dest_dir = os.path.join("uploads", f"user_{current_user.id}", f"dataset_{dataset.id}")
        os.makedirs(dest_dir, exist_ok=True)

        # Move all CSV files
        if os.path.exists(source_dir):
            for filename in os.listdir(source_dir):
                if filename.endswith(".csv"):
                    source_path = os.path.join(source_dir, filename)
                    dest_path = os.path.join(dest_dir, filename)
                    shutil.move(source_path, dest_path)
                    logger.info(f"Moved {filename} to {dest_dir}")

    def get_synchronized(self, current_user_id: int) -> DataSet:
        return self.repository.get_synchronized(current_user_id)

    def get_unsynchronized(self, current_user_id: int) -> DataSet:
        return self.repository.get_unsynchronized(current_user_id)

    def get_unsynchronized_dataset(self, current_user_id: int, dataset_id: int) -> DataSet:
        return self.repository.get_unsynchronized_dataset(current_user_id, dataset_id)

    def latest_synchronized(self):
        return self.repository.latest_synchronized()

    def count_synchronized_datasets(self):
        return self.repository.count_synchronized_datasets()

    def count_feature_models(self):
        return self.feature_model_service.count_feature_models()

    def count_authors(self) -> int:
        return self.author_repository.count()

    def count_dsmetadata(self) -> int:
        return self.dsmetadata_repository.count()

    def total_dataset_downloads(self) -> int:
        return self.dsdownloadrecord_repository.total_dataset_downloads()

    def total_dataset_views(self) -> int:
        return self.dsviewrecord_repostory.total_dataset_views()

    def create_from_form(self, form, current_user) -> DataSet:
        """
        Create a new CSV dataset from form data
        """
        logger.info(f"Creating dataset from form...")

        # Validate that files were uploaded
        temp_folder = current_user.temp_folder()
        if not os.path.exists(temp_folder) or not os.listdir(temp_folder):
            raise Exception("No files uploaded. Please upload at least one CSV file.")

        # Get CSV-specific fields
        has_header = form.has_header.data if hasattr(form, "has_header") else True
        delimiter = form.delimiter.data if hasattr(form, "delimiter") and form.delimiter.data else ","

        # Count files and calculate metrics
        csv_files = [f for f in os.listdir(temp_folder) if f.endswith(".csv")]
        num_files = len(csv_files)

        # Read first CSV to get number of columns
        num_columns = 0
        if csv_files:
            first_csv_path = os.path.join(temp_folder, csv_files[0])
            try:
                import csv

                with open(first_csv_path, "r", encoding="utf-8") as f:
                    reader = csv.reader(f, delimiter=delimiter)
                    rows = list(reader)
                    if rows:
                        num_columns = len(rows[0])
            except Exception as e:
                logger.warning(f"Could not read CSV for metrics: {e}")
                num_columns = 0

        # Create metrics
        ds_metrics = DSMetrics(
            number_of_models=str(num_files), number_of_features=str(num_columns)
        )

        # Get authors
        authors = []
        for author_data in form.get_authors():
            if author_data.get("name"):  # Only add if name is provided
                author = Author(
                    name=author_data.get("name"),
                    affiliation=author_data.get("affiliation", ""),
                    orcid=author_data.get("orcid", ""),
                )
                authors.append(author)

        # Create metadata
        ds_meta_data = DSMetaData(
            **form.get_dsmetadata(), ds_metrics=ds_metrics
        )
        ds_meta_data.authors = authors

        # Save metadata first to get an ID
        self.repository.session.add(ds_meta_data)
        self.repository.session.flush()

        # Create CSV dataset
        dataset = CSVDataSet(
            user_id=current_user.id,
            ds_meta_data_id=ds_meta_data.id,
            has_header=has_header,
            delimiter=delimiter,
        )

        self.repository.session.add(dataset)
        self.repository.session.flush()

        # Validate CSV files format
        validation_errors = []
        for filename in csv_files:
            file_path = os.path.join(temp_folder, filename)
            errors = self._validate_csv_format(file_path, has_header, delimiter)
            if errors:
                validation_errors.extend([f"{filename}: {error}" for error in errors])
        
        if validation_errors:
            error_msg = "CSV validation errors found:\n" + "\n".join(validation_errors)
            logger.error(error_msg)
            raise Exception(error_msg)

        # Create hubfiles for uploaded CSV files
        total_coches_created = 0
        for filename in csv_files:
            file_path = os.path.join(temp_folder, filename)
            file_size = os.path.getsize(file_path)

            # Calculate checksum
            import hashlib

            with open(file_path, "rb") as f:
                file_checksum = hashlib.md5(f.read()).hexdigest()

            hubfile = Hubfile(
                name=filename,
                checksum=file_checksum,
                size=file_size,
                data_set_id=dataset.id,
            )
            self.repository.session.add(hubfile)

            # Parse CSV and create Coche models
            coches_created = self._parse_csv_and_create_coches(file_path, has_header, delimiter)
            total_coches_created += coches_created

        self.repository.session.commit()
        logger.info(f"Dataset created successfully with {num_files} CSV files and {total_coches_created} coches")
        return dataset

    def create_new_version(self, dataset: DataSet, form, current_user, csv_form=None) -> DataSet:
        """
        Create a new version of an existing dataset with updated metadata and files.
        The new version will include existing files plus any newly uploaded files.
        """

        try:
            logger.info(f"Creating new version of dataset {dataset.id}...")

            # Create new metadata for the new version
            dsmetadata = self.dsmetadata_repository.create(**form.get_dsmetadata())

            # Copy authors from original dataset
            for author in dataset.ds_meta_data.authors:
                new_author = self.author_repository.create(
                    commit=False,
                    ds_meta_data_id=dsmetadata.id,
                    name=author.name,
                    affiliation=author.affiliation,
                    orcid=author.orcid,
                )
                dsmetadata.authors.append(new_author)

            # Create the new CSV dataset with incremented version
            new_dataset = CSVDataSet(
                user_id=current_user.id, ds_meta_data_id=dsmetadata.id, version=dataset.version + 1
            )
            if csv_form is not None:
                new_dataset.has_header = csv_form.has_header.data
                new_dataset.delimiter = csv_form.delimiter.data
            else:
                new_dataset.has_header = dataset.has_header
                new_dataset.delimiter = dataset.delimiter

            self.repository.session.add(new_dataset)
            self.repository.session.flush()

            # Copy existing files from the old dataset to the new dataset location
            working_dir = os.getenv("WORKING_DIR", "")
            old_dataset_dir = os.path.join(working_dir, "uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}")
            new_dataset_dir = os.path.join(
                working_dir, "uploads", f"user_{current_user.id}", f"dataset_{new_dataset.id}"
            )

            os.makedirs(new_dataset_dir, exist_ok=True)

            # Copy existing files directly from old dataset
            for old_file in dataset.files:
                # Copy physical file
                old_file_path = os.path.join(old_dataset_dir, old_file.name)
                new_file_path = os.path.join(new_dataset_dir, old_file.name)

                if os.path.exists(old_file_path):
                    shutil.copy2(old_file_path, new_file_path)

                    # Create new file record linked to new dataset
                    new_file = Hubfile(
                        name=old_file.name,
                        checksum=old_file.checksum,
                        size=old_file.size,
                        data_set_id=new_dataset.id,
                    )
                    self.repository.session.add(new_file)

            # Add new uploaded files from temp folder
            total_coches_created = 0
            temp_folder = current_user.temp_folder()
            
            # Validate CSV files format before processing
            validation_errors = []
            if os.path.exists(temp_folder):
                temp_files = [f for f in os.listdir(temp_folder) if f.endswith('.csv')]
                for filename in temp_files:
                    file_path = os.path.join(temp_folder, filename)
                    errors = self._validate_csv_format(file_path, new_dataset.has_header, new_dataset.delimiter)
                    if errors:
                        validation_errors.extend([f"{filename}: {error}" for error in errors])
            
            if validation_errors:
                error_msg = "CSV validation errors found:\n" + "\n".join(validation_errors)
                logger.error(error_msg)
                raise Exception(error_msg)
            
            if os.path.exists(temp_folder):
                temp_files = os.listdir(temp_folder)
                for filename in temp_files:
                    file_path = os.path.join(temp_folder, filename)
                    if os.path.isfile(file_path):
                        checksum, size = calculate_checksum_and_size(file_path)
                        
                        # Create new file record linked to dataset
                        new_file = Hubfile(
                            name=filename,
                            checksum=checksum,
                            size=size,
                            data_set_id=new_dataset.id,
                        )
                        self.repository.session.add(new_file)

                        # Move the file from temp folder to new dataset directory
                        new_file_destination = os.path.join(new_dataset_dir, filename)
                        if not os.path.exists(new_file_destination):
                            shutil.move(file_path, new_file_destination)
                        else:
                            # File already exists, just remove from temp
                            os.remove(file_path)
                        
                        # Parse CSV and create Coche models for new files
                        if filename.endswith('.csv'):
                            coches_created = self._parse_csv_and_create_coches(
                                new_file_destination, 
                                new_dataset.has_header, 
                                new_dataset.delimiter
                            )
                            total_coches_created += coches_created

            self.repository.session.commit()
            logger.info(f"Successfully created new version: {new_dataset.id} with version {new_dataset.version} and {total_coches_created} new coches")

        except Exception as exc:
            logger.error(f"Exception creating new version of dataset: {exc}")
            self.repository.session.rollback()
            raise exc

        return new_dataset

    def _parse_csv_and_create_coches(self, file_path: str, has_header: bool, delimiter: str) -> int:
        """
        Parse CSV file and create Coche models for each row.
        Returns the number of coches created.
        """
        import csv
        from datetime import datetime
        
        coches_created = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=delimiter) if has_header else csv.reader(f, delimiter=delimiter)
                
                for row in reader:
                    try:
                        if has_header:
                            # Map CSV columns to Coche model fields
                            coche = Coche(
                                modelo=row.get('Modelo', '').strip(),
                                marca=row.get('Marca', '').strip(),
                                motor=row.get('Motor', '').strip(),
                                consumo=float(row.get('Consumo', 0)),
                                combustible=row.get('Combustible', '').strip(),
                                comienzo_de_produccion=int(row.get('Comienzo de producción', 0)),
                                fin_de_produccion=int(row.get('Fin de producción', 0)) if row.get('Fin de producción', '').strip() else 9999,
                                asientos=int(row.get('Asientos', 0)),
                                puertas=int(row.get('Puertas', 0)),
                                peso=int(row.get('Peso (kg)', 0)),
                                carga_max=int(row.get('Carga máxima (kg)', 0)),
                                pais_de_origen=row.get('País de origen', '').strip(),
                                precio_estimado=int(row.get('Precio estimado (€)', 0)),
                                matricula=row.get('Matrícula', '').strip(),
                                fecha_matriculacion=datetime.strptime(row.get('Fecha de matriculación', ''), '%d/%m/%Y')
                            )
                        else:
                            # If no header, assume columns are in order
                            coche = Coche(
                                modelo=row[0].strip(),
                                marca=row[1].strip(),
                                motor=row[2].strip(),
                                consumo=float(row[3]),
                                combustible=row[4].strip(),
                                comienzo_de_produccion=int(row[5]),
                                fin_de_produccion=int(row[6]) if row[6].strip() else 9999,
                                asientos=int(row[7]),
                                puertas=int(row[8]),
                                peso=int(row[9]),
                                carga_max=int(row[10]),
                                pais_de_origen=row[11].strip(),
                                precio_estimado=int(row[12]),
                                matricula=row[13].strip(),
                                fecha_matriculacion=datetime.strptime(row[14], '%d/%m/%Y')
                            )
                        
                        self.repository.session.add(coche)
                        coches_created += 1
                        
                    except (ValueError, KeyError, IndexError) as e:
                        logger.warning(f"Skipping row due to parsing error: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error parsing CSV file {file_path}: {e}")
            
        return coches_created
    
    def _validate_csv_format(self, file_path: str, has_header: bool, delimiter: str) -> list:
        """
        Validate CSV file format and structure.
        Returns a list of error messages (empty list if valid).
        """
        import csv
        from io import StringIO
        
        errors = []
        
        try:
            # Try to read the file with different encodings
            content = None
            for encoding in ['utf-8', 'latin-1', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                errors.append("Unable to read file with common encodings (UTF-8, Latin-1, ISO-8859-1)")
                return errors
            
            # Parse CSV
            reader = csv.reader(StringIO(content), delimiter=delimiter)
            rows = list(reader)
            
            if not rows:
                errors.append("File is empty")
                return errors
            
            # Check for consistent column count
            non_empty_rows = [row for row in rows if any(cell.strip() for cell in row)]
            if not non_empty_rows:
                errors.append("File contains no data")
                return errors
            
            expected_cols = len(non_empty_rows[0])
            for i, row in enumerate(non_empty_rows[1:], start=2):
                if len(row) != expected_cols:
                    errors.append(f"Line {i}: Expected {expected_cols} columns, found {len(row)}")
            
        except Exception as e:
            errors.append(f"Error validating file: {str(e)}")
        
        return errors

    def update_dsmetadata(self, id, **kwargs):
        return self.dsmetadata_repository.update(id, **kwargs)

    def get_uvlhub_doi(self, dataset: DataSet) -> str:
        domain = os.getenv("DOMAIN", "localhost")
        return f"http://{domain}/doi/{dataset.ds_meta_data.dataset_doi}"


class AuthorService(BaseService):
    def __init__(self):
        super().__init__(AuthorRepository())


class DSDownloadRecordService(BaseService):
    def __init__(self):
        super().__init__(DSDownloadRecordRepository())


class DSMetaDataService(BaseService):
    def __init__(self):
        super().__init__(DSMetaDataRepository())

    def update(self, id, **kwargs):
        return self.repository.update(id, **kwargs)

    def filter_by_doi(self, doi: str) -> Optional[DSMetaData]:
        return self.repository.filter_by_doi(doi)


class DSViewRecordService(BaseService):
    def __init__(self):
        super().__init__(DSViewRecordRepository())

    def the_record_exists(self, dataset: DataSet, user_cookie: str):
        return self.repository.the_record_exists(dataset, user_cookie)

    def create_new_record(self, dataset: DataSet, user_cookie: str) -> DSViewRecord:
        return self.repository.create_new_record(dataset, user_cookie)

    def create_cookie(self, dataset: DataSet) -> str:

        user_cookie = request.cookies.get("view_cookie")
        if not user_cookie:
            user_cookie = str(uuid.uuid4())

        existing_record = self.the_record_exists(dataset=dataset, user_cookie=user_cookie)

        if not existing_record:
            self.create_new_record(dataset=dataset, user_cookie=user_cookie)

        return user_cookie


class DOIMappingService(BaseService):
    def __init__(self):
        super().__init__(DOIMappingRepository())

    def get_new_doi(self, old_doi: str) -> str:
        doi_mapping = self.repository.get_new_doi(old_doi)
        if doi_mapping:
            return doi_mapping.dataset_doi_new
        else:
            return None


class SizeService:

    def __init__(self):
        pass

    def get_human_readable_size(self, size: int) -> str:
        if size < 1024:
            return f"{size} bytes"
        elif size < 1024**2:
            return f"{round(size / 1024, 2)} KB"
        elif size < 1024**3:
            return f"{round(size / (1024 ** 2), 2)} MB"
        else:
            return f"{round(size / (1024 ** 3), 2)} GB"
