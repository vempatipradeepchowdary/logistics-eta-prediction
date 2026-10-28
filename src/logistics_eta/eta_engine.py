
"""Rule-based ETA prediction using information available at prediction time."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3


MODEL_VERSION = "rule-baseline-v2"


def parse_timestamp(value):
    """Parse an ISO timestamp and normalize it to UTC."""
    if not value:
        return None

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def to_timestamp(value):
    """Return a consistent ISO-8601 UTC timestamp."""
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def predict_shipment_eta(connection, shipment, prediction_time):

    service_level = connection.execute(
        """
        SELECT sl.delay_threshold_minutes
        FROM service_levels AS sl
        JOIN shipments AS s
          ON s.service_level_id = sl.service_level_id
        WHERE s.shipment_id = ?
        """,
        (shipment["shipment_id"],),
    ).fetchone()

    delay_threshold = (
        int(service_level["delay_threshold_minutes"])
        if service_level
        else 60
    )

    """Estimate one shipment's ETA using only data available at prediction time."""
    planned_eta = parse_timestamp(shipment["planned_eta"])
    departure = parse_timestamp(shipment["planned_departure_time"])

    if planned_eta is None or departure is None:
        raise ValueError(
            f"Shipment {shipment['shipment_id']} has an invalid planned time"
        )

    # Never predict using a timestamp before the shipment's planned departure.
    prediction_time = parse_timestamp(prediction_time)

    if prediction_time is None:
        raise ValueError("prediction_time is required")

    if prediction_time < departure:
        prediction_time = departure

    # Start with the planned ETA.
    estimated_eta = planned_eta
    delay_minutes = 0

    # Find the latest tracking event that had already happened and arrived.
    latest_event = connection.execute(
        """
        SELECT event_type, event_time
        FROM tracking_events
        WHERE shipment_id = ?
          AND event_time <= ?
          AND ingestion_time <= ?
        ORDER BY event_time DESC, ingestion_time DESC
        LIMIT 1
        """,
        (
            shipment["shipment_id"],
            to_timestamp(prediction_time),
            to_timestamp(prediction_time),
        ),
    ).fetchone()

    # Do not use the observed delivery time as a predicted ETA.
    # Keep the planned ETA when the shipment is already delivered
    # at prediction time, so the prediction does not use the answer.
    if latest_event and latest_event["event_type"] == "delivered":
        estimated_eta = planned_eta
    else:
        # Weather disruptions at the destination that overlap the planned ETA.
        weather_rows = connection.execute(
            """
            SELECT severity, start_time, end_time
            FROM weather_events
            WHERE facility_id = ?
              AND start_time <= ?
              AND end_time >= ?
            """,
            (
                shipment["destination_facility_id"],
                to_timestamp(planned_eta),
                to_timestamp(prediction_time),
            ),
        ).fetchall()

        for weather in weather_rows:
            start_time = parse_timestamp(weather["start_time"])
            end_time = parse_timestamp(weather["end_time"])

            # Only count a disruption if it is active at prediction time or
            # starts later but before the planned ETA.
            if start_time and end_time and end_time >= prediction_time:
                severity = str(weather["severity"]).lower()

                if severity in {"severe", "high", "extreme"}:
                    delay_minutes += 180
                elif severity in {"moderate", "medium"}:
                    delay_minutes += 60
                elif severity in {"low", "minor"}:
                    delay_minutes += 15

        # Use the latest valid queue observation at the destination facility.
        queue = connection.execute(
            """
            SELECT estimated_wait_minutes
            FROM facility_queues
            WHERE facility_id = ?
              AND observed_at <= ?
              AND valid_until >= ?
            ORDER BY observed_at DESC
            LIMIT 1
            """,
            (
                shipment["destination_facility_id"],
                to_timestamp(prediction_time),
                to_timestamp(prediction_time),
            ),
        ).fetchone()

        if queue:
            delay_minutes += max(0, int(queue["estimated_wait_minutes"] or 0))

        estimated_eta = planned_eta + timedelta(minutes=delay_minutes)

    return {
        "shipment_id": shipment["shipment_id"],
        "prediction_time": to_timestamp(prediction_time),
        "predicted_eta": to_timestamp(estimated_eta),
        "predicted_delay": int(estimated_eta > planned_eta + timedelta(minutes=delay_threshold)),
        "model_version": MODEL_VERSION,
    }


def predict_all_shipments(database_path, prediction_hours_before_eta=24):
    """Create a rule-based ETA prediction for each shipment."""
    database_path = Path(database_path)

    if not database_path.is_file():
        raise FileNotFoundError(f"Database not found: {database_path}")

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    predictions = []

    try:
        shipments = connection.execute(
            """
            SELECT shipment_id, destination_facility_id,
                   planned_departure_time, planned_eta, status
            FROM shipments
            ORDER BY shipment_id
            """
        ).fetchall()

        for shipment in shipments:
            planned_eta = parse_timestamp(shipment["planned_eta"])

            prediction_time = planned_eta - timedelta(
                hours=prediction_hours_before_eta
            )

            predictions.append(
                predict_shipment_eta(
                    connection,
                    shipment,
                    to_timestamp(prediction_time),
                )
            )
    finally:
        connection.close()

    return predictions
