import csv
import os
import re
from datetime import datetime

from app import create_app, db
from app.modules.dataset.models import Coche, DataSet

app = create_app()


def extract_engine_size(motor_str):
    if not motor_str or not isinstance(motor_str, str):
        return None
    match = re.match(r"^(\d+[.,]\d+|\d+)", motor_str.strip())
    if match:
        try:
            return float(match.group(1).replace(",", "."))
        except ValueError:
            return None
    return None


with app.app_context():
    datasets = DataSet.query.all()

    for dataset in datasets:
        print(f"\n=== Dataset {dataset.id} ===")
        print(f"Files: {len(dataset.files)}")

        if not dataset.files:
            print("No files, skipping")
            continue

        coches = Coche.query.filter_by(dataset_id=dataset.id).all()
        print(f"Existing coches: {len(coches)}")

        if coches:
            engine_sizes = [extract_engine_size(c.motor) for c in coches]
            engine_sizes = [s for s in engine_sizes if s is not None]
            if engine_sizes:
                average = sum(engine_sizes) / len(engine_sizes)
                dataset.ds_meta_data.ds_metrics.average_engine_size = average
                print(f"Average: {average}")
        else:
            for hubfile in dataset.files:
                if not hubfile.name.endswith(".csv"):
                    continue

                working_dir = os.getenv("WORKING_DIR", "")
                file_path = os.path.join(
                    working_dir, "uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}", hubfile.name
                )

                if not os.path.exists(file_path):
                    print(f"File not found: {file_path}")
                    continue

                print(f"Parsing {hubfile.name}...")

                has_header = dataset.has_header if hasattr(dataset, "has_header") else True
                delimiter = dataset.delimiter if hasattr(dataset, "delimiter") else ","

                coches_count = 0
                engine_sizes = []

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        reader = (
                            csv.DictReader(f, delimiter=delimiter) if has_header else csv.reader(f, delimiter=delimiter)
                        )

                        for row in reader:
                            try:
                                if has_header:
                                    coche = Coche(
                                        dataset_id=dataset.id,
                                        modelo=row.get("Modelo", "").strip(),
                                        marca=row.get("Marca", "").strip(),
                                        motor=row.get("Motor", "").strip(),
                                        consumo=float(row.get("Consumo", 0)),
                                        combustible=row.get("Combustible", "").strip(),
                                        comienzo_de_produccion=int(row.get("Comienzo de producción", 0)),
                                        fin_de_produccion=(
                                            int(row.get("Fin de producción", 0))
                                            if row.get("Fin de producción", "").strip()
                                            else 9999
                                        ),
                                        asientos=int(row.get("Asientos", 0)),
                                        puertas=int(row.get("Puertas", 0)),
                                        peso=int(row.get("Peso (kg)", 0)),
                                        carga_max=int(row.get("Carga máxima (kg)", 0)),
                                        pais_de_origen=row.get("País de origen", "").strip(),
                                        precio_estimado=int(row.get("Precio estimado (€)", 0)),
                                        matricula=row.get("Matrícula", "").strip(),
                                        fecha_matriculacion=datetime.strptime(
                                            row.get("Fecha de matriculación", ""), "%d/%m/%Y"
                                        ),
                                    )
                                    motor_str = row.get("Motor", "").strip()
                                else:
                                    coche = Coche(
                                        dataset_id=dataset.id,
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
                                        fecha_matriculacion=datetime.strptime(row[14], "%d/%m/%Y"),
                                    )
                                    motor_str = row[2].strip()

                                db.session.add(coche)
                                coches_count += 1

                                size = extract_engine_size(motor_str)
                                if size is not None:
                                    engine_sizes.append(size)
                            except Exception as e:
                                print(f"Error in row: {e}")
                                continue
                except Exception as e:
                    print(f"Error parsing CSV: {e}")

                print(f"Created {coches_count} coches")

                if engine_sizes:
                    average = sum(engine_sizes) / len(engine_sizes)
                    dataset.ds_meta_data.ds_metrics.average_engine_size = average
                    print(f"Average engine size: {average}")

    db.session.commit()
    print("\n=== All datasets processed! ===")
