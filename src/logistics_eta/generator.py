
"""Generate deterministic synthetic logistics data for the ETA challenge."""

import csv
import hashlib
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


BASE_TIME = datetime(2026, 10, 1, 8, 0, tzinfo=timezone.utc)


def make_id(prefix, number, width=6):
    """Create stable, zero-padded identifiers."""
    return f"{prefix}{number:0{width}d}"


def iso_time(value):
    """Convert a datetime into a consistent ISO-8601 timestamp."""
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")



def write_csv(path, rows):
    """Write dictionaries to CSV, including all fields across all records."""
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        path.write_text("", encoding="utf-8")
        return

    # Collect every column name, including fields found only in anomaly records.
    fieldnames = list(dict.fromkeys(
        key
        for row in rows
        for key in row.keys()
    ))

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)



def write_json(path, rows):
    """Write records to a readable JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def generate_data(config):
    """Generate all starter or full-scale synthetic datasets."""
    rng = random.Random(config["seed"])
    shipment_count = config["shipments"]
    facility_count = config["facilities"]
    carrier_count = config["carriers"]
    events_per_shipment = config["tracking_events_per_shipment"]
    disruption_count = config["disruption_windows"]

    facilities = []
    for i in range(1, facility_count + 1):
        facilities.append({
            "facility_id": make_id("FAC-", i),
            "facility_name": f"Facility {i:03d}",
            "city": rng.choice([
                "Hyderabad", "Bengaluru", "Chennai", "Mumbai",
                "Delhi", "Pune", "Kolkata", "Jaipur",
            ]),
            "facility_type": rng.choice(["warehouse", "hub", "distribution_center"]),
            "timezone": "UTC",
            "operating_start_hour": 6,
            "operating_end_hour": 22,
        })

    carriers = []
    for i in range(1, carrier_count + 1):
        carriers.append({
            "carrier_id": make_id("CAR-", i),
            "carrier_name": f"Carrier {i:03d}",
            "service_level": rng.choice(["standard", "express"]),
            "active": True,
        })

    service_levels = [
        {
            "service_level_id": "SLA-000001",
            "service_name": "standard",
            "max_transit_hours": 72,
            "delay_threshold_minutes": 60,
        },
        {
            "service_level_id": "SLA-000002",
            "service_name": "express",
            "max_transit_hours": 36,
            "delay_threshold_minutes": 30,
        },
    ]

    routes = []
    for i in range(1, facility_count + 1):
        destination = (i % facility_count) + 1
        routes.append({
            "route_id": make_id("RTE-", i),
            "origin_facility_id": make_id("FAC-", i),
            "destination_facility_id": make_id("FAC-", destination),
            "distance_km": rng.randint(50, 1500),
            "planned_duration_hours": rng.randint(3, 30),
            "active": True,
        })

    shipments = []
    shipment_legs = []
    tracking_events = []
    facility_queues = []
    weather_events = []
    eta_estimates = []
    delay_reasons = []
    ground_truth = []

    event_counter = 0
    delay_counter = 0

    for i in range(1, shipment_count + 1):
        shipment_id = f"SHP-2026-{i:06d}"
        carrier = rng.choice(carriers)
        service_name = carrier["service_level"]
        sla = next(s for s in service_levels if s["service_name"] == service_name)

        origin_number = rng.randint(1, facility_count)
        destination_number = ((origin_number - 1 + rng.randint(1, facility_count - 1))
                              % facility_count) + 1
        origin_id = make_id("FAC-", origin_number)
        destination_id = make_id("FAC-", destination_number)

        planned_departure = BASE_TIME + timedelta(hours=rng.randint(0, 24 * 20))
        planned_hours = rng.randint(8, min(60, sla["max_transit_hours"]))
        planned_eta = planned_departure + timedelta(hours=planned_hours)

        is_delayed = rng.random() < 0.25
        delay_minutes = rng.randint(61, 360) if is_delayed else rng.randint(0, 45)
        actual_delivery = planned_eta + timedelta(minutes=delay_minutes)

        # Some shipments are not yet delivered at the prediction point.
        is_delivered = rng.random() < 0.90
        status = "delivered" if is_delivered else "in_transit"

        shipments.append({
            "shipment_id": shipment_id,
            "carrier_id": carrier["carrier_id"],
            "origin_facility_id": origin_id,
            "destination_facility_id": destination_id,
            "service_level_id": sla["service_level_id"],
            "planned_departure_time": iso_time(planned_departure),
            "planned_eta": iso_time(planned_eta),
            "actual_delivery_time": iso_time(actual_delivery) if is_delivered else "",
            "status": status,
            "distance_km": rng.randint(50, 2000),
        })

        # Every shipment has at least one leg. Some have two legs.
        leg_count = 2 if rng.random() < 0.30 else 1
        previous_facility = origin_id

        for leg_number in range(1, leg_count + 1):
            final_leg = leg_number == leg_count
            next_facility = destination_id if final_leg else make_id(
                "FAC-", rng.randint(1, facility_count)
            )
            route_number = ((origin_number - 1 + leg_number - 1) % facility_count) + 1

            shipment_legs.append({
                "leg_id": f"LEG-{shipment_id}-{leg_number:02d}",
                "shipment_id": shipment_id,
                "leg_number": leg_number,
                "route_id": make_id("RTE-", route_number),
                "carrier_id": carrier["carrier_id"],
                "origin_facility_id": previous_facility,
                "destination_facility_id": next_facility,
                "planned_departure_time": iso_time(
                    planned_departure + timedelta(hours=(leg_number - 1) * planned_hours / leg_count)
                ),
                "planned_arrival_time": iso_time(
                    planned_departure + timedelta(hours=leg_number * planned_hours / leg_count)
                ),
            })
            previous_facility = next_facility

        # Generate chronologically ordered tracking events.
        event_types = [
            "shipment_created", "picked_up", "arrived_at_hub",
            "departed_hub", "out_for_delivery", "delivered",
        ]
        for event_number in range(events_per_shipment):
            event_counter += 1
            event_type = event_types[min(event_number, len(event_types) - 1)]

            if not is_delivered and event_type == "delivered":
                event_type = "in_transit"
            event_time = planned_departure + timedelta(
                hours=planned_hours * (event_number + 1) / (events_per_shipment + 1)
            )
            if event_type == "delivered":
                event_time = actual_delivery

            # Ingestion can happen after the real event time.
            ingestion_time = event_time + timedelta(minutes=rng.randint(0, 180))
            tracking_events.append({
                "event_id": f"EVT-{shipment_id}-{event_counter:06d}",
                "shipment_id": shipment_id,
                "event_type": event_type,
                "event_time": iso_time(event_time),
                "ingestion_time": iso_time(ingestion_time),
                "facility_id": destination_id if event_type == "delivered" else origin_id,
                "source": "synthetic_carrier_feed",
            })

        # ETA prediction is made 24 hours before planned ETA.
        prediction_time = planned_eta - timedelta(
            hours=config["prediction_hours_before_eta"]
        )
        eta_estimates.append({
            "eta_id": f"ETA-{shipment_id}-{prediction_time.strftime('%Y%m%dT%H%M%S')}",
            "shipment_id": shipment_id,
            "prediction_time": iso_time(prediction_time),
            "predicted_eta": iso_time(planned_eta),
            "predicted_delay": False,
            "model_version": "rule-baseline-v1",
        })

        if is_delivered:
            delay_minutes_actual = max(
                0, int((actual_delivery - planned_eta).total_seconds() / 60)
            )
            delayed_by_sla = delay_minutes_actual > sla["delay_threshold_minutes"]

            if delayed_by_sla:
                delay_counter += 1
                delay_reasons.append({
                    "delay_id": make_id("DLY-2026-", delay_counter),
                    "shipment_id": shipment_id,
                    "reason_code": "TRANSIT_DELAY",
                    "delay_minutes": delay_minutes_actual,
                    "rule": f"delay exceeds {sla['delay_threshold_minutes']} minutes",
                })

            ground_truth.append({
                "shipment_id": shipment_id,
                "actual_delivery_time": iso_time(actual_delivery),
                "actual_delay_minutes": delay_minutes_actual,
                "is_delayed": delayed_by_sla,
                "label_rule": f"actual delay > {sla['delay_threshold_minutes']} minutes",
            })
        else:
            ground_truth.append({
                "shipment_id": shipment_id,
                "actual_delivery_time": "",
                "actual_delay_minutes": "",
                "is_delayed": "",
                "label_rule": "not delivered; final delay label unavailable",
            })

    for i in range(1, disruption_count + 1):
        facility = rng.choice(facilities)
        start = BASE_TIME + timedelta(hours=rng.randint(0, 24 * 25))
        duration = rng.randint(1, 12)
        disruption_type = rng.choice(["weather", "facility_queue"])

        if disruption_type == "weather":
            weather_events.append({
                "weather_event_id": make_id("WTH-", i),
                "facility_id": facility["facility_id"],
                "condition": rng.choice(["heavy_rain", "storm", "fog"]),
                "severity": rng.choice(["moderate", "high"]),
                "start_time": iso_time(start),
                "end_time": iso_time(start + timedelta(hours=duration)),
            })
        else:
            facility_queues.append({
                "queue_id": make_id("QUE-", i),
                "facility_id": facility["facility_id"],
                "queue_length": rng.randint(1, 30),
                "estimated_wait_minutes": rng.randint(10, 240),
                "observed_at": iso_time(start),
                "valid_until": iso_time(start + timedelta(hours=duration)),
            })

    # Keep deliberate anomalies separate from normal source records.
    anomaly_types = [
        "late_ingestion",
        "duplicate_event",
        "impossible_route_order",
        "future_event_leakage",
        "delivered_but_in_transit",
    ]
    for index, anomaly_type in enumerate(anomaly_types, start=1):
        ground_truth.append({
            "shipment_id": f"SHP-2026-{index:06d}",
            "actual_delivery_time": "",
            "actual_delay_minutes": "",
            "is_delayed": "",
            "label_rule": "anomaly case; inspect issue_type",
            "issue_type": anomaly_type,
        })

    datasets = {
        "Carrier": carriers,
        "Facility": facilities,
        "Route": routes,
        "ServiceLevel": service_levels,
        "Shipment": shipments,
        "ShipmentLeg": shipment_legs,
        "TrackingEvent": tracking_events,
        "FacilityQueue": facility_queues,
        "WeatherEvent": weather_events,
        "ETAEstimate": eta_estimates,
        "DelayReason": delay_reasons,
        "ground_truth": ground_truth,
    }

    datasets["TrackingEvent"] = inject_tracking_anomalies(
        datasets["TrackingEvent"]
    )
    return datasets


def export_datasets(datasets, output_directory):
    """Export every dataset as both CSV and JSON, plus a checksum manifest."""
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    manifest = {
        "datasets": {},
        "note": "Synthetic data; ground_truth is kept separate from model inputs.",
    }

    for name, rows in datasets.items():
        csv_path = output_path / f"{name}.csv"
        json_path = output_path / f"{name}.json"
        write_csv(csv_path, rows)
        write_json(json_path, rows)

        csv_hash = hashlib.sha256(csv_path.read_bytes()).hexdigest()
        manifest["datasets"][name] = {
            "row_count": len(rows),
            "csv_sha256": csv_hash,
        }

    (output_path / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    return manifest



def inject_tracking_anomalies(tracking_events):
    """Inject five deterministic anomalies into tracking-event records."""
    import copy
    from datetime import datetime, timedelta, timezone

    events = copy.deepcopy(tracking_events)

    if len(events) < 5:
        raise ValueError("At least five tracking events are required.")

    # Group events by shipment, preserving the generated order.
    by_shipment = {}
    for event in events:
        by_shipment.setdefault(event["shipment_id"], []).append(event)

    shipment_ids = sorted(by_shipment)

    if len(shipment_ids) < 5:
        raise ValueError("At least five shipments are required.")

    # 1. Late ingestion: the event arrives much later than it occurred.
    late_event = by_shipment[shipment_ids[0]][0]
    event_time = datetime.fromisoformat(
        late_event["event_time"].replace("Z", "+00:00")
    )
    late_event["ingestion_time"] = (
        event_time + timedelta(hours=12)
    ).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    # 2. Duplicate event: same event content, unique record ID.
    original = by_shipment[shipment_ids[1]][0]
    duplicate = copy.deepcopy(original)
    duplicate["event_id"] = "ANOMALY-DUPLICATE-001"
    events.append(duplicate)

    # 3. Impossible order: the second event occurs before the first.
    sequence = by_shipment[shipment_ids[2]]
    if len(sequence) >= 2:
        first_time = datetime.fromisoformat(
            sequence[0]["event_time"].replace("Z", "+00:00")
        )
        impossible_time = first_time - timedelta(hours=2)
        sequence[1]["event_time"] = (
            impossible_time.astimezone(timezone.utc)
            .isoformat().replace("+00:00", "Z")
        )
        sequence[1]["ingestion_time"] = (
            impossible_time + timedelta(minutes=5)
        ).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    # 4. Future event: timestamp lies beyond the synthetic data period.
    future = copy.deepcopy(by_shipment[shipment_ids[3]][-1])
    future["event_id"] = "ANOMALY-FUTURE-001"
    future["event_time"] = "2027-01-01T00:00:00Z"
    future["ingestion_time"] = "2027-01-01T00:05:00Z"
    events.append(future)

    # 5. Delivered-but-in-transit: retain a delivered shipment's
    # delivered status in the shipment table but change its final
    # delivered tracking event to an in-transit event.
    delivered_event = next(
        (
            event for event in events
            if event["event_type"] == "delivered"
        ),
        None,
    )

    if delivered_event is not None:
        delivered_event["event_type"] = "in_transit"
    else:
        raise ValueError(
            "Cannot inject delivered-but-in-transit anomaly: "
            "no delivered tracking event exists."
        )

    return events
