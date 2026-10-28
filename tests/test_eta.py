
import sqlite3
import unittest

from src.logistics_eta.evaluation import evaluate_predictions
from src.logistics_eta.eta_engine import predict_shipment_eta


class TestEvaluation(unittest.TestCase):

    def test_evaluation_metrics(self):
        predictions = [
            {
                "shipment_id": "SHP-001",
                "predicted_eta": "2026-10-10T11:00:00Z",
                "predicted_delay": 1,
            },
            {
                "shipment_id": "SHP-002",
                "predicted_eta": "2026-10-10T12:00:00Z",
                "predicted_delay": 0,
            },
        ]

        ground_truth = [
            {
                "shipment_id": "SHP-001",
                "actual_delivery_time": "2026-10-10T10:00:00Z",
                "actual_delay_minutes": 120,
                "is_delayed": True,
            },
            {
                "shipment_id": "SHP-002",
                "actual_delivery_time": "2026-10-10T12:00:00Z",
                "actual_delay_minutes": 0,
                "is_delayed": False,
            },
        ]

        metrics = evaluate_predictions(predictions, ground_truth)

        self.assertEqual(metrics["evaluated_shipments"], 2)
        self.assertEqual(metrics["mae_minutes"], 30.0)
        self.assertEqual(metrics["rmse_minutes"], 42.43)
        self.assertEqual(metrics["precision"], 1.0)
        self.assertEqual(metrics["recall"], 1.0)
        self.assertEqual(metrics["f1"], 1.0)

    def test_undelivered_shipments_are_excluded(self):
        predictions = []

        ground_truth = [
            {
                "shipment_id": "SHP-003",
                "actual_delivery_time": "",
                "actual_delay_minutes": "",
                "is_delayed": "",
            }
        ]

        metrics = evaluate_predictions(predictions, ground_truth)

        self.assertEqual(metrics["evaluated_shipments"], 0)
        self.assertIsNone(metrics["mae_minutes"])


class TestPredictionNoLeakage(unittest.TestCase):

    def test_delivered_event_does_not_replace_predicted_eta(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row

        try:
            connection.execute("""
                CREATE TABLE service_levels (
                    service_level_id TEXT PRIMARY KEY,
                    delay_threshold_minutes INTEGER NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE shipments (
                    shipment_id TEXT PRIMARY KEY,
                    service_level_id TEXT NOT NULL
                )
            """)

            connection.execute("""
                INSERT INTO service_levels
                VALUES ('SLA-TEST', 60)
            """)

            connection.execute("""
                INSERT INTO shipments
                VALUES ('SHP-TEST', 'SLA-TEST')
            """)

            connection.execute("""
                CREATE TABLE tracking_events (
                    shipment_id TEXT,
                    event_type TEXT,
                    event_time TEXT,
                    ingestion_time TEXT
                )
            """)

            connection.execute("""
                CREATE TABLE weather_events (
                    facility_id TEXT,
                    severity TEXT,
                    start_time TEXT,
                    end_time TEXT
                )
            """)

            connection.execute("""
                CREATE TABLE facility_queues (
                    facility_id TEXT,
                    estimated_wait_minutes INTEGER,
                    observed_at TEXT,
                    valid_until TEXT
                )
            """)

            connection.execute("""
                INSERT INTO tracking_events
                VALUES (?, ?, ?, ?)
            """, (
                "SHP-TEST",
                "delivered",
                "2026-10-10T10:00:00Z",
                "2026-10-10T10:05:00Z",
            ))

            shipment = {
                "shipment_id": "SHP-TEST",
                "planned_departure_time": "2026-10-10T09:00:00Z",
                "planned_eta": "2026-10-10T12:00:00Z",
                "destination_facility_id": "FAC-TEST",
            }

            prediction = predict_shipment_eta(
                connection,
                shipment,
                "2026-10-10T10:30:00Z",
            )

            self.assertEqual(
                prediction["predicted_eta"],
                "2026-10-10T12:00:00Z",
            )

        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
