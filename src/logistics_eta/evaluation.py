
"""Evaluate ETA predictions against separate delivery ground truth."""
import json
from datetime import datetime
import math


def parse_timestamp(value):
    """Parse an ISO timestamp, including UTC timestamps ending in Z."""
    if not value:
        return None

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        from datetime import timezone
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed


def evaluate_predictions(predictions, ground_truth):
    """
    Calculate ETA error and binary delay-detection metrics.

    Ground-truth records without an actual delivery time are excluded.
    Anomaly-only records are also excluded from delivery evaluation.
    """
    prediction_by_shipment = {
        row["shipment_id"]: row
        for row in predictions
    }

    actual_rows = [
        row for row in ground_truth
        if row.get("actual_delivery_time")
        and row.get("is_delayed") in (True, False, 0, 1)
        and "issue_type" not in row
    ]

    evaluated = []
    missing_predictions = []

    for actual in actual_rows:
        shipment_id = actual["shipment_id"]
        prediction = prediction_by_shipment.get(shipment_id)

        if prediction is None:
            missing_predictions.append(shipment_id)
            continue

        actual_time = parse_timestamp(actual["actual_delivery_time"])
        predicted_time = parse_timestamp(prediction["predicted_eta"])

        if actual_time is None or predicted_time is None:
            continue

        error_minutes = (
            predicted_time - actual_time
        ).total_seconds() / 60

        evaluated.append({
            "shipment_id": shipment_id,
            "error_minutes": error_minutes,
            "actual_delayed": bool(actual["is_delayed"]),
            "predicted_delayed": bool(prediction["predicted_delay"]),
        })

    if not evaluated:
        return {
            "evaluated_shipments": 0,
            "missing_predictions": missing_predictions,
            "mae_minutes": None,
            "rmse_minutes": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "confusion_matrix": {
                "true_positive": 0,
                "false_positive": 0,
                "true_negative": 0,
                "false_negative": 0,
            },
        }

    errors = [row["error_minutes"] for row in evaluated]
    mae = sum(abs(error) for error in errors) / len(errors)
    rmse = math.sqrt(sum(error ** 2 for error in errors) / len(errors))

    true_positive = sum(
        row["actual_delayed"] and row["predicted_delayed"]
        for row in evaluated
    )
    false_positive = sum(
        not row["actual_delayed"] and row["predicted_delayed"]
        for row in evaluated
    )
    true_negative = sum(
        not row["actual_delayed"] and not row["predicted_delayed"]
        for row in evaluated
    )
    false_negative = sum(
        row["actual_delayed"] and not row["predicted_delayed"]
        for row in evaluated
    )

    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive else 0.0
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    return {
        "evaluated_shipments": len(evaluated),
        "missing_predictions": missing_predictions,
        "mae_minutes": round(mae, 2),
        "rmse_minutes": round(rmse, 2),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "confusion_matrix": {
            "true_positive": int(true_positive),
            "false_positive": int(false_positive),
            "true_negative": int(true_negative),
            "false_negative": int(false_negative),
        },
    }


def print_evaluation_report(metrics):
    """Print evaluation metrics in a readable format."""
    print("\n=== ETA Prediction Evaluation ===")
    print("Evaluated shipments:", metrics["evaluated_shipments"])
    print("Missing predictions:", len(metrics["missing_predictions"]))
    print("MAE (minutes):", metrics["mae_minutes"])
    print("RMSE (minutes):", metrics["rmse_minutes"])
    print("Delay precision:", metrics["precision"])
    print("Delay recall:", metrics["recall"])
    print("Delay F1 score:", metrics["f1"])
    print("Confusion matrix:", metrics["confusion_matrix"])


def save_evaluation_report(metrics, output_path):
    """Save evaluation metrics as a JSON file."""
    import json
    from pathlib import Path

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)

    print(f"Evaluation report saved to: {output_path}")
