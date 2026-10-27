# Logistics ETA Prediction & Delay Detection

A Python-based logistics analytics project that predicts shipment Estimated Time of Arrival (ETA), detects potential delivery delays, and evaluates prediction accuracy using reproducible synthetic data.

## Project Overview

The project combines shipment plans, carrier tracking events, weather disruptions, and facility queue conditions to estimate delivery times and identify shipments that may arrive late.

It includes a deterministic data generator, SQLite database, CSV/JSON exports, data validation, a rule-based ETA prediction engine, evaluation metrics, automated tests, and project documentation.

## Key Features

- Reproducible synthetic logistics data using a fixed random seed.
- SQLite storage with primary keys, foreign keys, constraints, and indexes.
- CSV and JSON dataset exports.
- Shipment ETA prediction using documented business rules.
- Delay detection using a rule-based baseline.
- Separate ground-truth data for model evaluation.
- Tracking-event anomaly injection and validation.
- Evaluation using MAE, RMSE, precision, recall, F1-score, and a confusion matrix.
- Automated tests for data generation, database integrity, reproducibility, anomaly handling, and prediction behavior.

## Technology Stack

- Python
- SQLite
- CSV and JSON
- SQL
- Python unittest framework

## Project Status

The starter pipeline has been executed successfully, database validation has passed with warnings for intentionally injected tracking-event anomalies, and the automated test suite has passed 33 tests.

The ETA predictor is a baseline implementation. Its accuracy and limitations are documented in the evaluation results and project documentation.

## Getting Started

### Prerequisites

- Python 3.13 or a compatible Python 3 version.
- Git (optional, for version control).

### 1. Clone the Repository

```bash
git clone https://github.com/vempatipradeepchowdary/logistics-eta-prediction.git
cd logistics-eta-prediction
```

### 2. Create a Virtual Environment

On Windows PowerShell:

```powershell
python -m venv .venv
```

### 3. Activate the Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Run the Starter Pipeline

```powershell
python scripts\run_pipeline.py
```

The starter configuration generates a smaller dataset for quick testing, loads the data into SQLite, validates the database, generates ETA predictions, and evaluates the results.

### 6. Run the Automated Tests

```powershell
python -m unittest discover -s tests -v
```

### 7. Run the Full Dataset Pipeline

```powershell
python scripts\run_pipeline.py config/full.json
```

The full configuration generates a larger dataset for evaluating the pipeline at a higher volume.

## Configuration

Two configurations are provided:

- **Starter configuration — `config/starter.json`**
  - Shipments: 200
  - Purpose: Quick testing and development.

- **Full configuration — `config/full.json`**
  - Shipments: 50,000
  - Purpose: Larger-scale evaluation.

Both configurations use the fixed random seed `20261022` to support reproducible data generation.

## Output Files

Pipeline outputs are written to the configured output directory.

Typical outputs include:

- `logistics.db` — SQLite database containing generated logistics data.
- `predictions.csv` and `predictions.json` — generated ETA predictions.
- `evaluation.json` — evaluation metrics.
- Dataset CSV and JSON files — exported source datasets.
- `ground_truth.json` — separate reference data used for evaluation.

The starter outputs are stored in `outputs/starter/`, while full-run outputs are stored in `outputs/full/`.

## Evaluation Results

The starter pipeline was executed successfully with 200 generated shipments.

### Starter Dataset Metrics

- **Evaluated shipments:** 181
- **Mean Absolute Error (MAE):** 70.28 minutes
- **Root Mean Squared Error (RMSE):** 116.63 minutes
- **Precision:** 0.5000
- **Recall:** 0.0556
- **F1-score:** 0.1000

### Understanding the Results

- **MAE** measures the average absolute difference between predicted and actual delivery times.
- **RMSE** gives greater weight to larger prediction errors.
- **Precision** measures how many shipments predicted as delayed were actually delayed.
- **Recall** measures how many actual delayed shipments the system successfully detected.
- **F1-score** combines precision and recall into a single metric.

### Current Limitations

The current implementation uses a rule-based baseline rather than a trained machine-learning model. The starter results show low delay recall, meaning many actual delays are not detected.

These results establish a baseline for future improvements. They should not be interpreted as production-level prediction performance.

The pipeline also reports warnings for intentionally injected tracking-event anomalies. These warnings are expected and help demonstrate the validation process.

## Project Documentation

Additional documentation is available in the `docs/` directory:

- `architecture.md` — project architecture and data flow.
- `business_rules.md` — ETA and delay-detection rules.
- `data_dictionary.md` — dataset and field descriptions.
- `assumptions_and_tradeoffs.md` — design decisions and limitations.
- `validation_strategy.md` — validation and testing approach.
- `ai_disclosure.md` — AI assistance disclosure.

## Reproducibility

The project uses a fixed random seed of `20261022` and deterministic ID generation to make dataset generation reproducible under the same configuration and software environment.

## Disclaimer

This project uses synthetic data for demonstration and evaluation. Its predictions are intended for project and learning purposes, not real-world logistics decisions.

## Full Dataset Evaluation

The full pipeline was executed using `config/full.json`.

- **Generated shipments:** 50,000
- **Generated ETA predictions:** 50,000
- **Evaluated shipments:** 44,942
- **Missing predictions:** 0
- **Database validation errors:** 0

### Full Dataset Metrics

- **Mean Absolute Error (MAE):** 80.60 minutes
- **Root Mean Squared Error (RMSE):** 122.55 minutes
- **Delay precision:** 0.3524
- **Delay recall:** 0.1514
- **Delay F1-score:** 0.2118

### Confusion Matrix

- **True positives:** 2,440
- **False positives:** 4,484
- **True negatives:** 24,341
- **False negatives:** 13,677

The full run completed successfully. Database validation reported two warnings for intentionally injected out-of-order tracking events and no validation errors.

The results show that the rule-based baseline has room for improvement, particularly in detecting delayed shipments. These metrics provide a baseline for future enhancements rather than evidence of production readiness.

The evaluation report is available at `outputs/full/evaluation.json`.
