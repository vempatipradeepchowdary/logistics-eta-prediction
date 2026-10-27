
# Data Dictionary

## 1. Overview

The project generates synthetic logistics datasets and stores operational records in SQLite. CSV and JSON exports are provided for inspection and analysis.

Ground truth is maintained separately from operational prediction inputs.

All timestamps use ISO 8601 format and are normalized to UTC.

## 2. Operational Entities

### Carrier

Represents a logistics carrier.

Typical fields:
- `carrier_id`: unique carrier identifier
- `carrier_name`: carrier name
- Additional attributes describe the synthetic carrier configuration

### Facility

Represents a warehouse, hub, or delivery facility.

Typical fields:
- `facility_id`: unique facility identifier
- Facility attributes describe the generated location

### ServiceLevel

Represents a delivery service category and its intended service rules.

Typical fields:
- `service_level_id`: unique service-level identifier
- Additional attributes describe the synthetic service level and its delay threshold

### Route

Represents a planned route between facilities.

Typical fields:
- `route_id`: unique route identifier
- Origin and destination facility identifiers
- Route attributes used by the synthetic generator

### Shipment

Represents an individual shipment.

Important fields include:
- `shipment_id`: unique shipment identifier
- `carrier_id`: associated carrier
- `route_id`: associated route
- `service_level_id`: associated service level
- `planned_departure_time`: planned departure timestamp
- `planned_eta`: planned arrival timestamp
- `actual_delivery_time`: actual delivery timestamp when available
- `status`: generated shipment status

### ShipmentLeg

Represents one segment of a shipment's journey.

Typical fields:
- `shipment_leg_id`: unique leg identifier
- `shipment_id`: associated shipment
- Route or facility references describing the leg
- Planned and actual leg timing fields, where generated

### TrackingEvent

Represents an event reported by the synthetic carrier feed.

Important fields:
- `event_id`: unique event-record identifier
- `shipment_id`: associated shipment
- `event_type`: lifecycle event type
- `event_time`: time the event occurred
- `ingestion_time`: time the event was received
- `facility_id`: facility associated with the event
- `source`: event source identifier

The distinction between `event_time` and `ingestion_time` supports prediction-time data-availability checks.

### FacilityQueue

Represents an estimated waiting time at a facility.

Important fields:
- `facility_id`: associated facility
- `estimated_wait_minutes`: estimated queue waiting time
- `observed_at`: time the queue observation was recorded
- `valid_until`: end of the observation's validity period

### WeatherEvent

Represents a weather-related disruption window.

Important fields:
- `facility_id`: affected facility
- `severity`: disruption severity
- `start_time`: disruption start
- `end_time`: disruption end

### ETAEstimate

Stores an ETA estimate associated with a shipment.

Typical fields:
- ETA estimate identifier
- `shipment_id`: associated shipment
- Estimated arrival timestamp
- Estimate metadata, where generated

### DelayReason

Represents a recorded reason associated with a shipment delay.

Typical fields:
- Delay-reason identifier
- `shipment_id`: associated shipment
- Reason category or description
- Delay-related metadata, where generated

## 3. Ground Truth

Ground truth is exported separately and used for evaluation.

Important fields include:
- `shipment_id`: shipment being evaluated
- `actual_delivery_time`: actual delivery timestamp, when available
- `actual_delay_minutes`: actual delay in minutes, when available
- `is_delayed`: generated delay classification
- `issue_type`: anomaly category for anomaly-specific records, when present

Records that lack the required delivery or classification fields are not included in the corresponding evaluation metrics.

Ground-truth anomaly records should not be interpreted as ordinary shipment outcomes.

## 4. Prediction Outputs

The prediction output includes:

| Field | Meaning |
|---|---|
| `shipment_id` | Shipment being predicted |
| `prediction_time` | Time at which the prediction is considered to have been made |
| `predicted_eta` | Estimated arrival timestamp |
| `predicted_delay` | 1 if the predicted ETA exceeds the planned ETA by more than 60 minutes; otherwise 0 |
| `model_version` | Identifier for the prediction-rule version |

## 5. Evaluation Output

The evaluation JSON includes:

| Field | Meaning |
|---|---|
| `evaluated_shipments` | Number of shipments included in evaluation |
| `missing_predictions` | Shipment identifiers without matching predictions |
| `mae_minutes` | Mean absolute ETA error in minutes |
| `rmse_minutes` | Root mean squared ETA error in minutes |
| `precision` | Fraction of predicted delays that are actual delays |
| `recall` | Fraction of actual delays identified by the predictor |
| `f1` | Harmonic mean of delay precision and recall |
| `confusion_matrix` | Counts of true positives, false positives, true negatives, and false negatives |

Metrics can be `null` when no eligible records exist or when a metric cannot be calculated.

## 6. Database Constraints

The SQLite schema defines primary keys, foreign keys, and relevant checks for operational entities.

These constraints help prevent invalid references and malformed records from entering the database through the supported loading process.

The separate CSV and JSON exports are useful for inspection but do not independently enforce SQLite constraints.

## 7. Schema Maintenance

This document describes the intended meaning of the generated datasets. For exact column names and database constraints, refer to:

- `sql/schema.sql`
- `src/logistics_eta/generator.py`
- `src/logistics_eta/database.py`

When the implementation changes, update this dictionary to keep it aligned with the actual generated fields and database schema.
