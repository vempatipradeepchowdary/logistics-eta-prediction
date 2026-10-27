
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path

from src.logistics_eta.validation import validate_database


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "outputs" / "starter" / "logistics.db"

REQUIRED_TABLES = {
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
}


class TestDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not DATABASE_PATH.exists():
            raise FileNotFoundError(
                f"Database not found: {DATABASE_PATH}. "
                "Run the starter pipeline first."
            )

    def test_required_tables_exist(self):
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            rows = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()

        table_names = {row[0] for row in rows}
        self.assertTrue(REQUIRED_TABLES.issubset(table_names))

    def test_shipments_are_present(self):
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM shipments"
            ).fetchone()[0]

        self.assertEqual(count, 200)

    def test_every_shipment_has_an_eta_estimate(self):
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            shipment_count = connection.execute(
                "SELECT COUNT(*) FROM shipments"
            ).fetchone()[0]

            estimate_count = connection.execute(
                "SELECT COUNT(*) FROM eta_estimates"
            ).fetchone()[0]

        self.assertEqual(estimate_count, shipment_count)

    def test_foreign_key_integrity(self):
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            violations = connection.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()

        self.assertEqual(violations, [])

    def test_database_integrity(self):
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            result = connection.execute(
                "PRAGMA integrity_check"
            ).fetchone()[0]

        self.assertEqual(result, "ok")

    def test_database_validation_passes(self):
        result = validate_database(str(DATABASE_PATH))

        self.assertTrue(
            result["passed"],
            msg=f"Validation errors: {result['errors']}",
        )


if __name__ == "__main__":
    unittest.main()
