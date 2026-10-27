
"""Load generated logistics datasets into a relational SQLite database."""

import json
import sqlite3
from pathlib import Path


# Parent tables must be loaded before tables that reference them.
TABLE_MAPPING = [
    ("Facility", "facilities"),
    ("Carrier", "carriers"),
    ("ServiceLevel", "service_levels"),
    ("Route", "routes"),
    ("Shipment", "shipments"),
    ("ShipmentLeg", "shipment_legs"),
    ("TrackingEvent", "tracking_events"),
    ("FacilityQueue", "facility_queues"),
    ("WeatherEvent", "weather_events"),
    ("ETAEstimate", "eta_estimates"),
    ("DelayReason", "delay_reasons"),
]


def load_database(database_path, data_directory, schema_path=None):
    """Create a fresh SQLite database and load the generated JSON records."""
    database_path = Path(database_path)
    data_directory = Path(data_directory)

    if schema_path is None:
        project_root = Path(__file__).resolve().parents[2]
        schema_path = project_root / "sql" / "schema.sql"
    else:
        schema_path = Path(schema_path)

    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    if not data_directory.is_dir():
        raise FileNotFoundError(
            f"Generated data directory not found: {data_directory}"
        )

    database_path.parent.mkdir(parents=True, exist_ok=True)

    # This output database is rebuilt from the exported data each time.
    if database_path.exists():
        database_path.unlink()

    connection = sqlite3.connect(database_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        schema_sql = schema_path.read_text(encoding="utf-8")
        connection.executescript(schema_sql)

        loaded_counts = {}

        with connection:
            for json_name, table_name in TABLE_MAPPING:
                json_path = data_directory / f"{json_name}.json"

                if not json_path.is_file():
                    raise FileNotFoundError(
                        f"Dataset file not found: {json_path}"
                    )

                with json_path.open("r", encoding="utf-8") as file:
                    records = json.load(file)

                if not records:
                    loaded_counts[table_name] = 0
                    continue

                columns = list(records[0].keys())
                placeholders = ", ".join("?" for _ in columns)
                column_sql = ", ".join(columns)

                insert_sql = (
                    f"INSERT INTO {table_name} ({column_sql}) "
                    f"VALUES ({placeholders})"
                )

                values = []
                for record in records:
                    row = []
                    for column in columns:
                        value = record.get(column)

                        # SQLite CHECK constraints expect 0 or 1 for booleans.
                        if isinstance(value, bool):
                            value = int(value)

                        row.append(value)

                    values.append(tuple(row))

                connection.executemany(insert_sql, values)
                loaded_counts[table_name] = len(records)

        # Confirm that the foreign-key relationships are valid.
        violations = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if violations:
            raise ValueError(
                f"Foreign-key violations found: {violations[:10]}"
            )

        return loaded_counts

    finally:
        connection.close()
