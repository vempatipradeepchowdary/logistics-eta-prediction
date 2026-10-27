
"""Run the complete starter logistics ETA prediction pipeline."""

import json
import sys
from pathlib import Path

# Allow the script to run directly from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.logistics_eta.generator import generate_data, export_datasets
from src.logistics_eta.database import load_database
from src.logistics_eta.validation import (
    validate_database,
    print_validation_report,
)
from src.logistics_eta.eta_engine import predict_all_shipments
from src.logistics_eta.evaluation import (
    evaluate_predictions,
    print_evaluation_report,
    save_evaluation_report,
)


def main():
    """Generate data, load SQLite, validate, predict, and evaluate."""
    config_path = PROJECT_ROOT / (sys.argv[1] if len(sys.argv) > 1 else "config/starter.json")
    with config_path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    output_directory = PROJECT_ROOT / config["export_directory"]
    database_path = PROJECT_ROOT / config["database_path"]
    ground_truth_path = output_directory / "ground_truth.json"

    print("\nSTEP 1: Generating deterministic datasets")
    datasets = generate_data(config)
    export_datasets(datasets, output_directory)
    print("Datasets exported to:", output_directory)

    print("\nSTEP 2: Loading SQLite database")
    loaded_counts = load_database(
        database_path,
        output_directory,
    )
    for table_name, count in loaded_counts.items():
        print(f"{table_name}: {count} rows")

    print("\nSTEP 3: Validating database")
    validation = validate_database(database_path)
    print_validation_report(validation)

    if validation.get("errors"):
        raise RuntimeError(
            "Database validation failed. Fix the reported errors first."
        )

    print("\nSTEP 4: Generating ETA predictions")
    predictions = predict_all_shipments(
        database_path,
        prediction_hours_before_eta=config.get(
            "prediction_hours_before_eta", 24
        ),
    )

    predictions_json = output_directory / "predictions.json"
    with predictions_json.open("w", encoding="utf-8") as file:
        json.dump(predictions, file, indent=2)

    predictions_csv = output_directory / "predictions.csv"
    if predictions:
        import csv

        with predictions_csv.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=list(predictions[0].keys()),
            )
            writer.writeheader()
            writer.writerows(predictions)

    print("Predictions generated:", len(predictions))
    print("JSON predictions:", predictions_json)
    print("CSV predictions:", predictions_csv)

    print("\nSTEP 5: Evaluating predictions")
    with ground_truth_path.open("r", encoding="utf-8") as file:
        ground_truth = json.load(file)

    metrics = evaluate_predictions(predictions, ground_truth)
    print_evaluation_report(metrics)

    save_evaluation_report(
        metrics,
        output_directory / "evaluation.json",
    )

    print("\nPipeline completed successfully.")


if __name__ == "__main__":
    main()
