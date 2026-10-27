
import unittest
from datetime import datetime, timedelta, timezone

from src.logistics_eta.generator import inject_tracking_anomalies


def create_sample_events():
    """Create simple tracking events for five shipments."""
    events = []

    for number in range(1, 6):
        shipment_id = f"SHP-{number:06d}"

        second_event_type = (
            "delivered" if number == 5 else "picked_up"
        )

        events.extend([
            {
                "event_id": f"EVT-{shipment_id}-000001",
                "shipment_id": shipment_id,
                "event_type": "shipment_created",
                "event_time": "2026-10-01T10:00:00Z",
                "ingestion_time": "2026-10-01T10:05:00Z",
                "facility_id": "FAC-001",
                "source": "test",
            },
            {
                "event_id": f"EVT-{shipment_id}-000002",
                "shipment_id": shipment_id,
                "event_type": second_event_type,
                "event_time": "2026-10-01T12:00:00Z",
                "ingestion_time": "2026-10-01T12:05:00Z",
                "facility_id": "FAC-002",
                "source": "test",
            },
        ])

    return events


class TestTrackingEventAnomalies(unittest.TestCase):

    def setUp(self):
        self.original_events = create_sample_events()
        self.modified_events = inject_tracking_anomalies(
            self.original_events
        )

    def test_injects_duplicate_event(self):
        duplicate = next(
            event for event in self.modified_events
            if event["event_id"] == "ANOMALY-DUPLICATE-001"
        )

        original = next(
            event for event in self.original_events
            if event["shipment_id"] == "SHP-000002"
            and event["event_id"].endswith("000001")
        )

        duplicate_without_id = {
            key: value for key, value in duplicate.items()
            if key != "event_id"
        }
        original_without_id = {
            key: value for key, value in original.items()
            if key != "event_id"
        }

        self.assertEqual(duplicate_without_id, original_without_id)

    def test_injects_future_event(self):
        future_event = next(
            event for event in self.modified_events
            if event["event_id"] == "ANOMALY-FUTURE-001"
        )

        self.assertEqual(
            future_event["event_time"],
            "2027-01-01T00:00:00Z",
        )

    def test_injects_late_ingestion(self):
        event = next(
            event for event in self.modified_events
            if event["shipment_id"] == "SHP-000001"
            and event["event_id"].endswith("000001")
        )

        event_time = datetime.fromisoformat(
            event["event_time"].replace("Z", "+00:00")
        )
        ingestion_time = datetime.fromisoformat(
            event["ingestion_time"].replace("Z", "+00:00")
        )

        self.assertEqual(
            ingestion_time - event_time,
            timedelta(hours=12),
        )

    def test_injects_impossible_event_order(self):
        first_event = next(
            event for event in self.modified_events
            if event["shipment_id"] == "SHP-000003"
            and event["event_id"].endswith("000001")
        )
        second_event = next(
            event for event in self.modified_events
            if event["shipment_id"] == "SHP-000003"
            and event["event_id"].endswith("000002")
        )

        first_time = datetime.fromisoformat(
            first_event["event_time"].replace("Z", "+00:00")
        )
        second_time = datetime.fromisoformat(
            second_event["event_time"].replace("Z", "+00:00")
        )

        self.assertLess(second_time, first_time)

    def test_injects_delivered_but_in_transit(self):
        original_delivered = next(
            event for event in self.original_events
            if event["event_type"] == "delivered"
        )

        modified_event = next(
            event for event in self.modified_events
            if event["event_id"] == original_delivered["event_id"]
        )

        self.assertEqual(modified_event["event_type"], "in_transit")
        self.assertEqual(original_delivered["event_type"], "delivered")

    def test_adds_exactly_two_event_records(self):
        self.assertEqual(
            len(self.modified_events),
            len(self.original_events) + 2,
        )

    def test_does_not_modify_original_events(self):
        self.assertEqual(len(self.original_events), 10)

        original_delivered = next(
            event for event in self.original_events
            if event["shipment_id"] == "SHP-000005"
            and event["event_type"] == "delivered"
        )

        self.assertEqual(original_delivered["event_type"], "delivered")


if __name__ == "__main__":
    unittest.main()
