
"""Command-line entry point for synthetic logistics data generation."""

import argparse
import json
import sys
from pathlib import Path

# Add the project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.logistics_eta.generator import generate_data, export_datasets


def main():
    parser = argparse.ArgumentParser(
        description="Generate reproducible synthetic logistics datasets."
    )
    parser.add_argument(
        "--config",
        default="config/starter.json",
        help="Path to the JSON configuration file.",
    )
    args = parser.parse_args()

    config_path = PROJECT_ROOT / args.config
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    print("Generating synthetic logistics data...")
    print(f"Seed: {config['seed']}")
    print(f"Shipments requested: {config['shipments']}")

    datasets = generate_data(config)

    output_directory = PROJECT_ROOT / config["export_directory"]
    manifest = export_datasets(datasets, output_directory)

    print("\nGeneration completed.")
    print(f"Output directory: {output_directory}")

    print("\nDataset row counts:")
    for name, details in manifest["datasets"].items():
        print(f"  {name}: {details['row_count']} rows")

    print("\nManifest saved to:")
    print(output_directory / "manifest.json")


if __name__ == "__main__":
    main()
