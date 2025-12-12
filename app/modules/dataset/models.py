from datetime import datetime
from enum import Enum

from flask import request
from sqlalchemy import Enum as SQLAlchemyEnum

from app import db


class PublicationType(Enum):
    NONE = "none"
    AVAILABLE_TO_BUY_CARS = "availabletobuy"
    MISSING_CARS = "missing"
    REGISTERED_CARS = "registered"
    SOLD_CARS = "sold"
    FINED_CARS = "fined"
    SEEN_CARS = "seen"
    PARKED_CARS = "parked"
    PERSONAL_CARS = "personal"
    OTHER = "other"


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    affiliation = db.Column(db.String(120))
    orcid = db.Column(db.String(120))
    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey("ds_meta_data.id"))
    fm_meta_data_id = db.Column(
        db.Integer, db.ForeignKey("fm_meta_data.id")
    )  # Legacy - still used by featuremodel module

    def to_dict(self):
        return {"name": self.name, "affiliation": self.affiliation, "orcid": self.orcid}


class Coche(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("data_set.id", ondelete="CASCADE"), nullable=False)
    modelo = db.Column(db.String(120), nullable=False)
    marca = db.Column(db.String(120), nullable=False)
    motor = db.Column(db.String(120), nullable=False)
    consumo = db.Column(db.Float, nullable=False)
    combustible = db.Column(db.String(120), nullable=False)
    comienzo_de_produccion = db.Column(db.Integer, nullable=False)
    fin_de_produccion = db.Column(db.Integer, nullable=True)
    asientos = db.Column(db.Integer, nullable=False)
    puertas = db.Column(db.Integer, nullable=False)
    peso = db.Column(db.Integer, nullable=False)
    carga_max = db.Column(db.Integer, nullable=False)
    pais_de_origen = db.Column(db.String(120), nullable=False)
    precio_estimado = db.Column(db.Integer, nullable=False)
    matricula = db.Column(db.String(7), nullable=False)
    fecha_matriculacion = db.Column(db.DateTime, nullable=False)

    # Relationship to DataSet
    dataset = db.relationship("DataSet", backref=db.backref("coches", passive_deletes=True))

    def __repr__(self):
        return f"Coche<{self.modelo} {self.marca} {self.matricula}>"


class DSMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number_of_models = db.Column(db.String(120))
    number_of_features = db.Column(db.String(120))
    average_engine_size = db.Column(db.Float, nullable=True)
    average_consumption = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return (
            f"DSMetrics<models={self.number_of_models}, "
            f"features={self.number_of_features}, "
            f"avg_engine={self.average_engine_size}>"
        )


class DSMetaData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deposition_id = db.Column(db.Integer)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    publication_type = db.Column(SQLAlchemyEnum(PublicationType), nullable=False)
    publication_doi = db.Column(db.String(120))
    dataset_doi = db.Column(db.String(120))
    tags = db.Column(db.String(120))
    ds_metrics_id = db.Column(db.Integer, db.ForeignKey("ds_metrics.id"))
    ds_metrics = db.relationship("DSMetrics", uselist=False, backref="ds_meta_data", cascade="all, delete")
    authors = db.relationship("Author", backref="ds_meta_data", lazy=True, cascade="all, delete")


class DataSet(db.Model):
    __tablename__ = "data_set"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    ds_meta_data_id = db.Column(db.Integer, db.ForeignKey("ds_meta_data.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    version = db.Column(db.Integer, nullable=False, default=1)
    DataSetType = db.Column(db.String(50))

    ds_meta_data = db.relationship("DSMetaData", backref=db.backref("data_set", uselist=False))

    # Relación directa con archivos (reemplaza feature_models)
    files = db.relationship("Hubfile", backref="dataset", lazy=True, cascade="all, delete")

    __mapper_args__ = {
        "polymorphic_identity": "data_set",
        "polymorphic_on": DataSetType,
    }

    # ELIMINAR ESTE MÉTODO - causa duplicación
    # def files(self):
    #     """Return all files associated with this dataset"""
    #     from app.modules.hubfile.models import Hubfile
    #     return Hubfile.query.filter_by(data_set_id=self.id).all()

    def get_dataset_type(self):
        return "dataset"

    def increment_dataset_version(self):
        self.version = (self.version or 1) + 1

    def get_version(self):
        return self.version

    def name(self):
        return self.ds_meta_data.title

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def get_cleaned_publication_type(self):
        return self.ds_meta_data.publication_type.name.replace("_", " ").title()

    def get_zenodo_url(self):
        return f"https://zenodo.org/record/{self.ds_meta_data.deposition_id}" if self.ds_meta_data.dataset_doi else None

    def get_files_count(self):
        return len(self.files)

    def get_file_total_size(self):
        return sum(file.size for file in self.files)

    def get_file_total_size_for_human(self):
        from app.modules.dataset.services import SizeService

        return SizeService().get_human_readable_size(self.get_file_total_size())

    def get_dataset_url(self):
        from app.modules.dataset.services import DataSetService

        return DataSetService().get_dataset_url(self)

    def to_dict(self):
        return {
            "title": self.ds_meta_data.title,
            "id": self.id,
            "created_at": self.created_at,
            "created_at_timestamp": int(self.created_at.timestamp()),
            "description": self.ds_meta_data.description,
            "authors": [author.to_dict() for author in self.ds_meta_data.authors],
            "publication_type": self.get_cleaned_publication_type(),
            "publication_doi": self.ds_meta_data.publication_doi,
            "dataset_doi": self.ds_meta_data.dataset_doi,
            "tags": self.ds_meta_data.tags.split(",") if self.ds_meta_data.tags else [],
            "url": self.get_dataset_url(),
            "download": f'{request.host_url.rstrip("/")}/dataset/download/{self.id}',
            "zenodo": self.get_zenodo_url(),
            "files": [file.to_dict() for file in self.files],
            "files_count": self.get_files_count(),
            "total_size_in_bytes": self.get_file_total_size(),
            "total_size_in_human_format": self.get_file_total_size_for_human(),
        }

    def __repr__(self):
        return f"DataSet<{self.id}>"


# class UVLDataSet(DataSet):
#     __tablename__ = "uvl_data_set"

#     id = db.Column(db.Integer, db.ForeignKey("data_set.id"), primary_key=True)

#     __mapper_args__ = {
#         "polymorphic_identity": "uvl_data_set",
#     }


class CSVDataSet(DataSet):
    __tablename__ = "csv_data_set"

    id = db.Column(db.Integer, db.ForeignKey("data_set.id"), primary_key=True)

    delimiter = db.Column(db.String(5), nullable=False, default=",")
    has_header = db.Column(db.Boolean, nullable=False, default=True)

    __mapper_args__ = {
        "polymorphic_identity": "csv_data_set",
    }


class DSDownloadRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("data_set.id"))
    download_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    download_cookie = db.Column(db.String(36), nullable=False)  # Assuming UUID4 strings

    def __repr__(self):
        return (
            f"<Download id={self.id} "
            f"dataset_id={self.dataset_id} "
            f"date={self.download_date} "
            f"cookie={self.download_cookie}>"
        )


class DSViewRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("data_set.id"))
    view_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    view_cookie = db.Column(db.String(36), nullable=False)  # Assuming UUID4 strings

    def __repr__(self):
        return f"<View id={self.id} dataset_id={self.dataset_id} date={self.view_date} cookie={self.view_cookie}>"


class DOIMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_doi_old = db.Column(db.String(120))
    dataset_doi_new = db.Column(db.String(120))


# Este código hace que se incremente la versión antes del update
# pero NO cuando se crea una nueva versión manualmente


def increment_dataset_version(mapper, connection, target):
    # Only increment if version change was not manual (i.e., if it's the same)
    # When creating a new version manually, we set the version explicitly
    # so we need to check if the version was already incremented
    pass  # Disabled automatic increment - version is now managed explicitly


# Commented out to disable automatic version increment
# event.listen(DataSet, "before_update", increment_dataset_version)
