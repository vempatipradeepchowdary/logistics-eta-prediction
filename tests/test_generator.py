
import json
import unittest
from pathlib import Path

from src.logistics_eta.generator import generate_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_starter_config():
    config_path = PROJECT_ROOT / "config" / "starter.json"

    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)


class TestDatasetGenerator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = load_starter_config()
        cls.datasets = generate_data(cls.config)

    def test_required_datasets_exist(self):
        required_datasets = {
            "Carrier",
            "Facility",
            "Route",
            "ServiceLevel",
            "Shipment",
            "ShipmentLeg",
            "TrackingEvent",
            "FacilityQueue",
            "WeatherEvent",
            "ETAEstimate",
            "DelayReason",
            "ground_truth",
        }

        self.assertTrue(
            required_datasets.issubset(self.datasets.keys())
        )

    def test_shipment_count_matches_config(self):
        self.assertEqual(
            len(self.datasets["Shipment"]),
            self.config["shipments"],
        )

    def test_facility_count_matches_config(self):
        self.assertEqual(
            len(self.datasets["Facility"]),
            self.config["facilities"],
        )

    def test_carrier_count_matches_config(self):
        self.assertEqual(
            len(self.datasets["Carrier"]),
            self.config["carriers"],
        )

    def test_shipment_ids_are_unique(self):
        shipment_ids = [
            shipment["shipment_id"]
            for shipment in self.datasets["Shipment"]
        ]

        self.assertEqual(len(shipment_ids), len(set(shipment_ids)))

    def test_shipment_ids_are_not_empty(self):
        for shipment in self.datasets["Shipment"]:
            self.assertTrue(shipment["shipment_id"])

    def test_tracking_events_have_required_fields(self):
        required_fields = {
            "event_id",
            "shipment_id",
            "event_type",
            "event_time",
            "ingestion_time",
        }

        for event in self.datasets["TrackingEvent"]:
            self.assertTrue(required_fields.issubset(event.keys()))

    def test_tracking_event_ids_are_unique(self):
        event_ids = [
            event["event_id"]
            for event in self.datasets["TrackingEvent"]
        ]

        self.assertEqual(len(event_ids), len(set(event_ids)))

    def test_ground_truth_contains_anomaly_labels(self):
        issue_types = {
            row.get("issue_type")
            for row in self.datasets["ground_truth"]
        }

        expected_anomalies = {
            "late_ingestion",
            "duplicate_event",
            "impossible_route_order",
            "future_event_leakage",
            "delivered_but_in_transit",
        }

        self.assertTrue(expected_anomalies.issubset(issue_types))


if __name__ == "__main__":
    unittest.main()
