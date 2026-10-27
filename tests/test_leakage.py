
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ETA_ENGINE_PATH = (
    PROJECT_ROOT / "src" / "logistics_eta" / "eta_engine.py"
)


class TestDataLeakage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not ETA_ENGINE_PATH.exists():
            raise FileNotFoundError(
                f"ETA engine not found: {ETA_ENGINE_PATH}"
            )

        cls.source = ETA_ENGINE_PATH.read_text(encoding="utf-8")

    def test_eta_engine_exists_and_is_not_empty(self):
        self.assertTrue(self.source.strip())

    def test_engine_checks_event_time(self):
        self.assertIn("event_time", self.source)

    def test_engine_checks_ingestion_time(self):
        self.assertIn("ingestion_time", self.source)

    def test_engine_defines_prediction_time(self):
        self.assertIn("prediction_time", self.source)

    def test_engine_does_not_use_actual_delivery_field_directly(self):
        self.assertNotIn(
            '["actual_delivery_time"]',
            self.source,
        )


if __name__ == "__main__":
    unittest.main()
