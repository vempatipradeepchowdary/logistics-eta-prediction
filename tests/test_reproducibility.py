
import copy
import json
import unittest
from pathlib import Path

from src.logistics_eta.generator import generate_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_starter_config():
    config_path = PROJECT_ROOT / "config" / "starter.json"

    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)


class TestReproducibility(unittest.TestCase):

    def test_same_seed_produces_identical_data(self):
        config = load_starter_config()

        first_run = generate_data(copy.deepcopy(config))
        second_run = generate_data(copy.deepcopy(config))

        self.assertEqual(first_run, second_run)

    def test_different_seed_changes_generated_data(self):
        config_one = load_starter_config()
        config_two = copy.deepcopy(config_one)

        config_two["seed"] = config_one["seed"] + 1

        first_run = generate_data(config_one)
        second_run = generate_data(config_two)

        self.assertNotEqual(
            first_run["Shipment"],
            second_run["Shipment"],
        )

    def test_config_seed_is_documented(self):
        config = load_starter_config()

        self.assertEqual(config["seed"], 20261022)


if __name__ == "__main__":
    unittest.main()
