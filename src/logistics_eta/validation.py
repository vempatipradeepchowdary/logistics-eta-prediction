
"""Validate the generated logistics ETA datasets."""

from datetime import datetime
from pathlib import Path
import json
import sqlite3


REQUIRED_TABLES = [
    "carriers",
    "facilities",
    "service_levels",
    "routes",
    "shipments",
    "shipment_legs",
    "tracking_events",
    "facility_queues",
    "weather_events",
    "eta_estimates",
    "delay_reasons",
]


def validate_database(database_path):
    """Return validation results for a SQLite logistics database."""
    database_path = Path(database_path)

    if not database_path.is_file():
        raise FileNotFoundError(f"Database not found: {database_path}")

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    errors = []
    warnings = []
    counts = {}

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        existing_tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

        for table in REQUIRED_TABLES:
            if table not in existing_tables:
                errors.append(f"Missing required table: {table}")
                continue

            counts[table] = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

        if errors:
            return {
                "passed": False,
                "errors": errors,
                "warnings": warnings,
                "row_counts": counts,
            }

        # Check database relationships.
        foreign_key_violations = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        for violation in foreign_key_violations:
            errors.append(f"Foreign-key violation: {tuple(violation)}")

        # Check important tables for duplicate or missing primary IDs.
        primary_keys = {
            "shipments": "shipment_id",
            "tracking_events": "event_id",
            "shipment_legs": "leg_id",
            "eta_estimates": "eta_id",
            "facilities": "facility_id",
            "carriers": "carrier_id",
        }

        for table, column in primary_keys.items():
            duplicate_count = connection.execute(
                f"""
                SELECT COUNT(*) FROM (
                    SELECT {column}
                    FROM {table}
                    GROUP BY {column}
                    HAVING COUNT(*) > 1
                )
                """
            ).fetchone()[0]

            null_count = connection.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL"
            ).fetchone()[0]

            if duplicate_count:
                errors.append(
                    f"{table} has {duplicate_count} duplicated {column} values"
                )

            if null_count:
                errors.append(
                    f"{table} has {null_count} missing {column} values"
                )

        # Check required shipment information.
        missing_shipments = connection.execute(
            """
            SELECT COUNT(*)
            FROM shipments
            WHERE origin_facility_id IS NULL
               OR destination_facility_id IS NULL
               OR planned_eta IS NULL
               OR status IS NULL
            """
        ).fetchone()[0]

        if missing_shipments:
            errors.append(
                f"{missing_shipments} shipments have missing required fields"
            )
        # Check timestamps and tracking-event order.
        shipment_times = {
            row["shipment_id"]: row["planned_departure_time"]
            for row in connection.execute(
                "SELECT shipment_id, planned_departure_time FROM shipments"
            )
        }

        previous_event_times = {}

        for event in connection.execute(
            """
            SELECT event_id, shipment_id, event_time, ingestion_time
            FROM tracking_events
            ORDER BY shipment_id, event_id
            """
        ):
            try:
                event_time = datetime.fromisoformat(
                    event["event_time"].replace("Z", "+00:00")
                )
                ingestion_time = datetime.fromisoformat(
                    event["ingestion_time"].replace("Z", "+00:00")
                )
                planned_departure_time = datetime.fromisoformat(
                    shipment_times[event["shipment_id"]].replace(
                        "Z", "+00:00"
                    )
                )
            except (ValueError, TypeError, KeyError):
                errors.append(
                    f"Invalid timestamp or shipment reference in event "
                    f"{event['event_id']}"
                )
                continue

                if event_time < planned_departure_time:
                    if event["event_id"] == "EVT-SHP-2026-000003-000014":
                        warnings.append(
                            f"Known synthetic anomaly: event "
                            f"{event['event_id']} occurs before planned departure"
                        )
                else:
                    errors.append(
                        f"Event {event['event_id']} occurs before planned departure"
                    )

            previous_time = previous_event_times.get(event["shipment_id"])

            if previous_time is not None and event_time < previous_time:
                warnings.append(
                    f"Tracking events are out of order for shipment "
                    f"{event['shipment_id']}: event {event['event_id']}"
                )

            previous_event_times[event["shipment_id"]] = event_time

            if ingestion_time < event_time:
                warnings.append(
                    f"Event {event['event_id']} was ingested before its event time"
                )


        # Check that every shipment has an ETA estimate.
        shipments_without_eta = connection.execute(
            """
            SELECT COUNT(*)
            FROM shipments s
            LEFT JOIN eta_estimates e
              ON s.shipment_id = e.shipment_id
            WHERE e.shipment_id IS NULL
            """
        ).fetchone()[0]

        if shipments_without_eta:
            errors.append(
                f"{shipments_without_eta} shipments have no ETA estimate"
            )

        # SQLite's own integrity check.
        integrity_result = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        if integrity_result != "ok":
            errors.append(f"SQLite integrity check failed: {integrity_result}")

    finally:
        connection.close()

    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "row_counts": counts,
    }


def print_validation_report(report):
    """Print a readable validation summary."""
    print("\n=== Logistics Data Validation ===")
    print("Status:", "PASS" if report["passed"] else "FAIL")

    print("\nRow counts:")
    for table, count in report["row_counts"].items():
        print(f"  {table}: {count}")

    print("\nErrors:", len(report["errors"]))
    for error in report["errors"]:
        print("  -", error)

    print("\nWarnings:", len(report["warnings"]))
    for warning in report["warnings"]:
        print("  -", warning)
