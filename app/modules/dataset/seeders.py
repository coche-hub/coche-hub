import os
import re
import shutil

from app.modules.auth.models import User
from app.modules.dataset.models import Author, CSVDataSet, DSMetaData, DSMetrics, PublicationType
from app.modules.dataset.services import DataSetService
from app.modules.hubfile.models import Hubfile
from core.seeders.BaseSeeder import BaseSeeder


class DataSetSeeder(BaseSeeder):
    priority = 2  # Lower priority

    def __init__(self):
        super().__init__()
        self.dataset_service = DataSetService()  # Instanciar el servicio

    def run(self):
        # Retrieve seeded users
        user1 = User.query.filter_by(email="user1@example.com").first()
        user2 = User.query.filter_by(email="user2@example.com").first()

        if not user1 or not user2:
            raise Exception("Users not found. Please ensure that UserSeeder has been executed.")

        # Crear datasets CSV de ejemplo
        [
            self.seed_csv_dataset(
                user=user1,
                title="Coches Dataset 0",
                description="Example CSV dataset with car information - basic example",
                publication_type=PublicationType.AVAILABLE_TO_BUY_CARS,
                tags="cars, csv, example",
                csv_filename="coches0.csv",
                has_header=True,
                delimiter=",",
            ),
            self.seed_csv_dataset(
                user=user2,
                title="Coches Dataset 1",
                description="Example CSV dataset with car specifications - extended data",
                publication_type=PublicationType.REGISTERED_CARS,
                tags="automobiles, specifications, csv",
                csv_filename="coches1.csv",
                has_header=True,
                delimiter=",",
            ),
            self.seed_csv_dataset(
                user=user1,
                title="Coches Dataset 2",
                description="Example CSV dataset with vehicle details - complete dataset",
                publication_type=PublicationType.PERSONAL_CARS,
                tags="vehicles, dataset, csv, demo",
                csv_filename="coches2.csv",
                has_header=True,
                delimiter=",",
            ),
        ]

    def seed_csv_dataset(
        self, user, title, description, publication_type, tags, csv_filename, has_header=True, delimiter=","
    ):
        # Get file path first to calculate metrics
        csv_path = os.path.join("app", "modules", "dataset", "csv_examples", csv_filename)

        if not os.path.exists(csv_path):
            print(f"Warning: CSV file not found: {csv_path}")
            return None

        # Calculate actual CSV metrics
        import csv

        num_columns = 0
        average_engine_size = None

        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)
                if rows:
                    num_columns = len(rows[0]) if rows else 0
        except Exception as e:
            print(f"Warning: Could not read CSV file {csv_filename}: {e}")
            num_columns = 1

        # Calculate average engine size
        average_engine_size = self._calculate_average_engine_size(csv_path, has_header, delimiter)

        # Create dataset metadata with calculated metrics
        ds_metrics = DSMetrics(
            number_of_models=str(1), number_of_features=str(num_columns), average_engine_size=average_engine_size
        )

        ds_meta_data = DSMetaData(
            title=title,
            description=description,
            publication_type=publication_type,
            tags=tags,
            ds_metrics=ds_metrics,
            dataset_doi=f"10.1234/example.{csv_filename.replace('.csv', '')}",
        )

        # Add sample authors
        author1 = Author(name="Sample Author", affiliation="Sample University", orcid="0000-0000-0000-0001")
        author2 = Author(name="Another Author", affiliation="Example Institute", orcid="0000-0000-0000-0002")
        ds_meta_data.authors.append(author1)
        ds_meta_data.authors.append(author2)

        # Create CSVDataSet
        dataset = CSVDataSet(user=user, ds_meta_data=ds_meta_data, has_header=has_header, delimiter=delimiter)

        self.db.session.add(dataset)
        self.db.session.flush()

        # Get file size
        file_size = os.path.getsize(csv_path)

        # Create Hubfile directly linked to dataset
        hubfile = Hubfile(
            name=csv_filename, checksum=f"checksum_{csv_filename}", size=file_size, data_set_id=dataset.id
        )

        self.db.session.add(hubfile)

        # Copy file to uploads directory
        user_upload_dir = os.path.join("uploads", f"user_{user.id}", f"dataset_{dataset.id}")
        os.makedirs(user_upload_dir, exist_ok=True)

        destination_path = os.path.join(user_upload_dir, csv_filename)
        shutil.copy2(csv_path, destination_path)

        # Use the service method to parse CSV and create Coches
        coches_created = self.dataset_service._parse_csv_and_create_coches(
            destination_path, has_header, delimiter, dataset.id
        )

        print(f"Created {coches_created} coches from {csv_filename}")

        self.db.session.commit()

        return dataset

    def _extract_engine_size(self, motor_str: str) -> float:
        """
        Extract engine size from motor string.
        Examples: "1.6 tdi" -> 1.6, "2.0 gasolina" -> 2.0, "1.6" -> 1.6
        """
        if not motor_str or not isinstance(motor_str, str):
            return None

        # Try to match a decimal number at the start of the string
        match = re.match(r"^(\d+[.,]\d+|\d+)", motor_str.strip())
        if match:
            try:
                # Replace comma with dot for consistency
                size_str = match.group(1).replace(",", ".")
                return float(size_str)
            except ValueError:
                return None

        return None

    def _calculate_average_engine_size(self, file_path: str, has_header: bool, delimiter: str) -> float:
        """
        Calculate the average engine size from all coches in the CSV file.
        Returns the average or None if no valid engine sizes found.
        """
        import csv

        engine_sizes = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=delimiter) if has_header else csv.reader(f, delimiter=delimiter)

                for row in reader:
                    try:
                        if has_header:
                            motor_str = row.get("Motor", "").strip()
                        else:
                            # Assuming motor is the 3rd column (index 2)
                            motor_str = row[2].strip() if len(row) > 2 else ""

                        size = self._extract_engine_size(motor_str)
                        if size is not None:
                            engine_sizes.append(size)
                    except (IndexError, ValueError, AttributeError):
                        continue

        except Exception as e:
            print(f"Warning: Error calculating average engine size from {file_path}: {e}")
            return None

        if engine_sizes:
            average = sum(engine_sizes) / len(engine_sizes)
            print(f"Calculated average engine size: {average} from {len(engine_sizes)} coches")
            return average

        return None
