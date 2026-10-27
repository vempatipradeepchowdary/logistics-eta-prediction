
# System Architecture

## 1. Project Overview

**Project name:** Logistics ETA Prediction & Delay Detection

This project generates reproducible synthetic logistics data, stores it in SQLite, predicts shipment arrival times using a rule-based baseline, identifies likely delays, validates data quality, and evaluates predictions against separate ground truth.

The project uses Python, SQLite, CSV, and JSON. A frontend is not required for the current version.

## 2. High-Level Architecture

```text
Configuration
(config/starter.json or config/full.json)
             |
             v
    Synthetic Data Generator
             |
             v
       CSV and JSON Data
             |
             v
       SQLite Database
             |
             v
     Data Quality Validation
             |
             v
      Rule-Based ETA Engine
             |
             v
     ETA Predictions (CSV/JSON)
             |
             v
   Evaluation Against Ground Truth
             |
             v
      Evaluation Report (JSON)
```

## 3. Main Components

### Configuration

Configuration files define the random seed, dataset size, number of facilities and carriers, tracking events per shipment, disruption-window count, database path, export directory, and prediction horizon.

The starter configuration is intended for quick testing. The full configuration generates a larger dataset.

### Data Generator

The generator creates synthetic logistics records using a fixed random seed.

It generates carriers, facilities, routes, service levels, shipments, shipment legs, tracking events, facility queues, weather events, initial ETA estimates, delay reasons, and separate ground truth.

Deterministic identifiers and a fixed seed help make repeated runs reproducible.

### Storage Layer

SQLite stores the operational datasets and enforces primary-key, foreign-key, and other schema constraints.

CSV and JSON exports make the generated data available for inspection and further analysis.

Ground truth is kept separate from the operational database to reduce the risk of accidentally using evaluation labels during prediction.

### Validation Layer

The validation component checks database integrity, required tables, record counts, identifiers, required shipment fields, timestamp consistency, tracking-event order, and ETA-estimate coverage.

Some deliberately injected anomalies can produce warnings. A successful validation means there are no blocking validation errors; it does not mean every record is anomaly-free.

### ETA Prediction Engine

The prediction engine uses a rule-based baseline rather than a trained machine-learning model.

It starts with the planned ETA and adjusts it using eligible destination weather disruptions and a valid destination facility-queue observation.

Tracking events are filtered by both event time and ingestion time relative to the prediction time. This prevents events that occurred or arrived later from influencing a historical prediction.

The current baseline uses a fixed 60-minute threshold to classify a predicted delay.

### Evaluation Component

The evaluation component compares predictions with eligible ground-truth records.

It calculates:

- Mean Absolute Error (MAE), in minutes
- Root Mean Squared Error (RMSE), in minutes
- Delay precision
- Delay recall
- Delay F1 score
- Confusion-matrix counts
- Number of evaluated shipments and missing predictions

Undelivered shipments and anomaly-only ground-truth records are excluded when they do not contain the required evaluation labels.

## 4. Data Model

The operational database contains the following main entities:

| Entity | Purpose |
|---|---|
| Carrier | Carrier information |
| Facility | Origin, destination, and hub locations |
| ServiceLevel | Delivery service and delay threshold information |
| Route | Planned movement between facilities |
| Shipment | Shipment status, schedule, and delivery information |
| ShipmentLeg | Individual segments of a shipment journey |
| TrackingEvent | Shipment lifecycle events with event and ingestion timestamps |
| FacilityQueue | Facility waiting-time observations |
| WeatherEvent | Weather disruption windows and severity |
| ETAEstimate | Stored ETA estimates |
| DelayReason | Recorded reasons associated with shipment delays |

Ground truth is exported separately and is used for evaluation rather than as a prediction input.

## 5. Time Handling

Timestamps are normalized to UTC and represented using ISO 8601 format.

Two tracking timestamps have different meanings:

- `event_time`: when the event occurred.
- `ingestion_time`: when the system received the event.

An event is eligible for a prediction only when both timestamps are at or before the prediction time.

The prediction time is calculated from the planned ETA and configured prediction horizon. If that time is earlier than the planned departure, the current implementation moves it forward to the planned departure time.

## 6. Pipeline Execution

Run the starter pipeline:

```powershell
python scripts\run_pipeline.py
```

Run the larger dataset pipeline:

```powershell
python scripts\run_pipeline.py config/full.json
```

The pipeline generates datasets, exports them, loads SQLite, validates the database, creates ETA predictions, evaluates the predictions, and saves the evaluation report.

## 7. Output Files

The starter pipeline writes its outputs under `outputs/starter/`, including:

- `logistics.db` — SQLite database
- Dataset CSV and JSON exports
- `predictions.csv` — predicted shipment arrival times
- `predictions.json` — predictions in JSON format
- `evaluation.json` — evaluation metrics

The full configuration writes to `outputs/full/`.

## 8. Current Limitations

- Data is synthetic and does not establish real-world predictive performance.
- ETA prediction uses hand-written rules rather than a trained forecasting model.
- Weather and queue delays use simplified assumptions.
- The current predicted-delay threshold is fixed at 60 minutes.
- The starter dataset is useful for development but is too small to establish production readiness.
- Injected anomalies may intentionally violate normal data-quality expectations.

These limitations should be considered when interpreting the evaluation results.
```

**Your task now:** Save `docs/architecture.md` and tell me when it is done. We will move to the next documentation file only after that.