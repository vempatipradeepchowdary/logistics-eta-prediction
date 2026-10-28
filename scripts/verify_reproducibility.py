
import copy
import json
import sys
from pathlib import Path

# Locate the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.logistics_eta.generator import generate_data


def main():
    config_path = PROJECT_ROOT / "config" / "starter.json"

    with config_path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    # Check that the expected seed is configured.
    if config["seed"] != 20261022:
        raise AssertionError("Unexpected random seed.")

    print("PASS: Configured seed is 20261022.")

    # Generate data twice with the same configuration.
    first_run = generate_data(copy.deepcopy(config))
    second_run = generate_data(copy.deepcopy(config))

    if first_run != second_run:
        raise AssertionError(
            "Identical configurations produced different datasets."
        )

    print("PASS: Same seed produces identical datasets.")

    # Change the seed and check that generated shipments change.
    changed_config = copy.deepcopy(config)
    changed_config["seed"] += 1

    changed_run = generate_data(changed_config)

    if first_run["Shipment"] == changed_run["Shipment"]:
        raise AssertionError(
            "Changing the seed did not change shipment data."
        )

    print("PASS: Different seed changes shipment data.")
    print("Reproducibility verification completed successfully.")


if __name__ == "__main__":
    main()
