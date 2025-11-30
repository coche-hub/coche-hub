import os
from app.modules.auth.models import User
from app.modules.dataset.models import Author, DSMetaData, DSMetrics, DataSet, PublicationType, CSVDataSet
from app.modules.hubfile.models import Hubfile
from core.seeders.BaseSeeder import BaseSeeder


class DataSetSeeder(BaseSeeder):
    priority = 2  # Lower priority

    def run(self):
        # Retrieve seeded users
        user1 = User.query.filter_by(email="user1@example.com").first()
        user2 = User.query.filter_by(email="user2@example.com").first()

        if not user1 or not user2:
            raise Exception("Users not found. Please ensure that UserSeeder has been executed.")

        # Crear datasets CSV de ejemplo
        seeded_datasets = [
            self.seed_csv_dataset(
                user=user1,
                title="Coches Dataset 0",
                description="Example CSV dataset with car information - basic example",
                publication_type=PublicationType.DATA_MANAGEMENT_PLAN,
                tags="cars, csv, example",
                csv_filename="coches0.csv",
                has_header=True,
                delimiter=","
            ),
            self.seed_csv_dataset(
                user=user2,
                title="Coches Dataset 1",
                description="Example CSV dataset with car specifications - extended data",
                publication_type=PublicationType.REPORT,
                tags="automobiles, specifications, csv",
                csv_filename="coches1.csv",
                has_header=True,
                delimiter=","
            ),
            self.seed_csv_dataset(
                user=user1,
                title="Coches Dataset 2",
                description="Example CSV dataset with vehicle details - complete dataset",
                publication_type=PublicationType.SOFTWARE_DOCUMENTATION,
                tags="vehicles, dataset, csv, demo",
                csv_filename="coches2.csv",
                has_header=True,
                delimiter=","
            ),
        ]

    def seed_csv_dataset(
        self,
        user,
        title,
        description,
        publication_type,
        tags,
        csv_filename,
        has_header=True,
        delimiter=","
    ):
        # Get file path first to calculate metrics
        csv_path = os.path.join("app", "modules", "dataset", "csv_examples", csv_filename)
        
        if not os.path.exists(csv_path):
            print(f"Warning: CSV file not found: {csv_path}")
            return None
        
        # Calculate actual CSV metrics
        import csv
        num_columns = 0
        num_rows = 0
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)
                if rows:
                    num_columns = len(rows[0]) if rows else 0
                    num_rows = len(rows) - (1 if has_header else 0)  # Exclude header if present
        except Exception as e:
            print(f"Warning: Could not read CSV file {csv_filename}: {e}")
            num_columns = 1
            num_rows = 1
        
        # Create dataset metadata with calculated metrics
        ds_metrics = DSMetrics(
            number_of_models=str(1),  # For CSV, we consider 1 file = 1 model
            number_of_features=str(num_columns)
        )
        
        ds_meta_data = DSMetaData(
            title=title,
            description=description,
            publication_type=publication_type,
            tags=tags,
            ds_metrics=ds_metrics,
            dataset_doi=f"10.1234/example.{csv_filename.replace('.csv', '')}"  # DOI de ejemplo
        )

        # Add sample authors
        author1 = Author(name="Sample Author", affiliation="Sample University", orcid="0000-0000-0000-0001")
        author2 = Author(name="Another Author", affiliation="Example Institute", orcid="0000-0000-0000-0002")
        ds_meta_data.authors.append(author1)
        ds_meta_data.authors.append(author2)

        # Create CSVDataSet
        dataset = CSVDataSet(
            user=user,
            ds_meta_data=ds_meta_data,
            has_header=has_header,
            delimiter=delimiter
        )
        
        self.db.session.add(dataset)
        self.db.session.flush()  # Obtener el ID del dataset antes de crear hubfile

        # Get file size
        file_size = os.path.getsize(csv_path)

        # Create Hubfile directly linked to dataset
        hubfile = Hubfile(
            name=csv_filename,
            checksum=f"checksum_{csv_filename}",
            size=file_size,
            data_set_id=dataset.id
        )
        
        self.db.session.add(hubfile)

        # Copy file to uploads directory
        user_upload_dir = os.path.join("uploads", f"user_{user.id}", f"dataset_{dataset.id}")
        os.makedirs(user_upload_dir, exist_ok=True)
        
        destination_path = os.path.join(user_upload_dir, csv_filename)
        
        # Copy the file
        import shutil
        shutil.copy2(csv_path, destination_path)

        self.db.session.add(dataset)
        self.db.session.commit()

        return dataset