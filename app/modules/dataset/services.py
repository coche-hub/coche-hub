import hashlib
import logging
import os
import shutil
import uuid
from typing import Optional

from flask import request

from app.modules.auth.services import AuthenticationService
from app.modules.dataset.models import CSVDataSet, DataSet, DSMetaData, DSViewRecord, UVLDataSet
from app.modules.dataset.repositories import (
    AuthorRepository,
    DataSetRepository,
    DOIMappingRepository,
    DSDownloadRecordRepository,
    DSMetaDataRepository,
    DSViewRecordRepository,
)
from app.modules.featuremodel.repositories import FeatureModelRepository, FMMetaDataRepository
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

    def move_feature_models(self, dataset: DataSet):
        current_user = AuthenticationService().get_authenticated_user()
        source_dir = current_user.temp_folder()

        working_dir = os.getenv("WORKING_DIR", "")
        dest_dir = os.path.join(working_dir, "uploads", f"user_{current_user.id}", f"dataset_{dataset.id}")

        os.makedirs(dest_dir, exist_ok=True)

        for feature_model in dataset.feature_models:
            uvl_filename = feature_model.fm_meta_data.uvl_filename
            shutil.move(os.path.join(source_dir, uvl_filename), dest_dir)

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

    def create_from_form(self, form, current_user, csv_form=None) -> DataSet:
        main_author = {
            "name": f"{current_user.profile.surname}, {current_user.profile.name}",
            "affiliation": current_user.profile.affiliation,
            "orcid": current_user.profile.orcid,
        }
        try:
            logger.info(f"Creating dsmetadata...: {form.get_dsmetadata()}")
            dsmetadata = self.dsmetadata_repository.create(**form.get_dsmetadata())
            for author_data in [main_author] + form.get_authors():
                author = self.author_repository.create(commit=False, ds_meta_data_id=dsmetadata.id, **author_data)
                dsmetadata.authors.append(author)

            # Create the appropriate DataSet subclass depending on dataset_type
            dataset_type = getattr(form, "dataset_type", None)
            selected_type = dataset_type.data if dataset_type is not None else "uvl"

            if selected_type == "csv":
                dataset = CSVDataSet(user_id=current_user.id, ds_meta_data_id=dsmetadata.id)
                # try to read csv-specific fields from csv_form if provided
                if csv_form is not None:
                    dataset.has_header = csv_form.has_header.data
                    dataset.delimiter = csv_form.delimiter.data
                else:
                    # fallback to request.form values if csv_form not passed
                    dataset.has_header = request.form.get("has_header", "y") in ["y", "true", "True", "on", "1"]
                    dataset.delimiter = request.form.get("delimiter", ",")
            else:
                dataset = UVLDataSet(user_id=current_user.id, ds_meta_data_id=dsmetadata.id)

            # add dataset to session and flush to get dataset.id for related records
            self.repository.session.add(dataset)
            self.repository.session.flush()

            for feature_model in form.feature_models:
                uvl_filename = feature_model.uvl_filename.data
                fmmetadata = self.fmmetadata_repository.create(commit=False, **feature_model.get_fmmetadata())
                for author_data in feature_model.get_authors():
                    author = self.author_repository.create(commit=False, fm_meta_data_id=fmmetadata.id, **author_data)
                    fmmetadata.authors.append(author)

                fm = self.feature_model_repository.create(
                    commit=False, data_set_id=dataset.id, fm_meta_data_id=fmmetadata.id
                )

                # associated files in feature model
                file_path = os.path.join(current_user.temp_folder(), uvl_filename)
                checksum, size = calculate_checksum_and_size(file_path)

                file = self.hubfilerepository.create(
                    commit=False, name=uvl_filename, checksum=checksum, size=size, feature_model_id=fm.id
                )
                fm.files.append(file)
            self.repository.session.commit()
        except Exception as exc:
            logger.info(f"Exception creating dataset from form...: {exc}")
            self.repository.session.rollback()
            raise exc
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

            # Determine dataset type
            dataset_type = dataset.get_dataset_type()
            is_csv = dataset_type == "csv_data_set"

            # Create the new dataset with incremented version
            if is_csv:
                new_dataset = CSVDataSet(
                    user_id=current_user.id, ds_meta_data_id=dsmetadata.id, version=dataset.version + 1
                )
                if csv_form is not None:
                    new_dataset.has_header = csv_form.has_header.data
                    new_dataset.delimiter = csv_form.delimiter.data
                else:
                    new_dataset.has_header = dataset.has_header
                    new_dataset.delimiter = dataset.delimiter
            else:
                new_dataset = UVLDataSet(
                    user_id=current_user.id, ds_meta_data_id=dsmetadata.id, version=dataset.version + 1
                )

            self.repository.session.add(new_dataset)
            self.repository.session.flush()

            # Copy existing files from the old dataset to the new dataset location
            working_dir = os.getenv("WORKING_DIR", "")
            old_dataset_dir = os.path.join(working_dir, "uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}")
            new_dataset_dir = os.path.join(
                working_dir, "uploads", f"user_{current_user.id}", f"dataset_{new_dataset.id}"
            )

            os.makedirs(new_dataset_dir, exist_ok=True)

            # Copy existing feature models and files
            for old_fm in dataset.feature_models:
                # Create new FMMetaData
                new_fmmetadata = self.fmmetadata_repository.create(
                    commit=False,
                    uvl_filename=old_fm.fm_meta_data.uvl_filename,
                    title=old_fm.fm_meta_data.title,
                    description=old_fm.fm_meta_data.description,
                    publication_type=old_fm.fm_meta_data.publication_type.name,
                    publication_doi=old_fm.fm_meta_data.publication_doi,
                    tags=old_fm.fm_meta_data.tags,
                    uvl_version=old_fm.fm_meta_data.uvl_version,
                )

                # Copy authors
                for author in old_fm.fm_meta_data.authors:
                    new_author = self.author_repository.create(
                        commit=False,
                        fm_meta_data_id=new_fmmetadata.id,
                        name=author.name,
                        affiliation=author.affiliation,
                        orcid=author.orcid,
                    )
                    new_fmmetadata.authors.append(new_author)

                # Create new feature model
                new_fm = self.feature_model_repository.create(
                    commit=False, data_set_id=new_dataset.id, fm_meta_data_id=new_fmmetadata.id
                )

                # Copy files
                for old_file in old_fm.files:
                    # Copy physical file
                    old_file_path = os.path.join(old_dataset_dir, old_file.name)
                    new_file_path = os.path.join(new_dataset_dir, old_file.name)

                    if os.path.exists(old_file_path):
                        shutil.copy2(old_file_path, new_file_path)

                        # Create new file record
                        new_file = self.hubfilerepository.create(
                            commit=False,
                            name=old_file.name,
                            checksum=old_file.checksum,
                            size=old_file.size,
                            feature_model_id=new_fm.id,
                        )
                        new_fm.files.append(new_file)

            # Add new uploaded files from temp folder
            temp_folder = current_user.temp_folder()
            if os.path.exists(temp_folder):
                temp_files = os.listdir(temp_folder)
                for filename in temp_files:
                    file_path = os.path.join(temp_folder, filename)
                    if os.path.isfile(file_path):
                        # Create simple metadata for new files
                        new_fmmetadata = self.fmmetadata_repository.create(
                            commit=False,
                            uvl_filename=filename,
                            title=filename.rsplit(".", 1)[0],
                            description="Added in version update",
                            publication_type="NONE",
                            publication_doi="",
                            tags="",
                            uvl_version="",
                        )

                        new_fm = self.feature_model_repository.create(
                            commit=False, data_set_id=new_dataset.id, fm_meta_data_id=new_fmmetadata.id
                        )

                        checksum, size = calculate_checksum_and_size(file_path)
                        new_file = self.hubfilerepository.create(
                            commit=False, name=filename, checksum=checksum, size=size, feature_model_id=new_fm.id
                        )
                        new_fm.files.append(new_file)

                        # Move the file from temp folder to new dataset directory
                        # Only if it doesn't already exist in the destination
                        new_file_destination = os.path.join(new_dataset_dir, filename)
                        if not os.path.exists(new_file_destination):
                            shutil.move(file_path, new_file_destination)
                        else:
                            # File already exists, just remove from temp
                            os.remove(file_path)

            self.repository.session.commit()
            logger.info(f"Successfully created new version: {new_dataset.id} with version {new_dataset.version}")

        except Exception as exc:
            logger.error(f"Exception creating new version of dataset: {exc}")
            self.repository.session.rollback()
            raise exc

        return new_dataset

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
