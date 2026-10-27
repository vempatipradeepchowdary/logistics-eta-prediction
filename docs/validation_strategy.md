
# Validation Strategy

## 1. Objective

The validation strategy checks data quality, database integrity, reproducibility, ETA prediction behavior, and evaluation calculations for the Logistics ETA Prediction & Delay Detection project.

## 2. Automated Unit Tests

Tests are located in the `tests/` directory.

| Test module | Purpose |
|---|---|
| `test_generator.py` | Checks generated datasets, configured counts, required fields, and identifier uniqueness |
| `test_anomalies.py` | Checks anomaly injection, expected extra records, and preservation of the original event list |
| `test_database.py` | Checks required tables, shipment records, ETA-estimate coverage, foreign keys, and database integrity |
| `test_reproducibility.py` | Checks same-seed reproducibility and verifies that changing the seed changes generated data |
| `test_leakage.py` | Checks for prediction-time fields and relevant event-time and ingestion-time filtering in the ETA engine |
| `test_eta.py` | Checks evaluation metrics, exclusion of undelivered records, and the delivered-event ETA behavior |

Run the complete test suite:

```powershell
python -m unittest discover -s tests -v
```

The current verified result is 33 passing tests.

## 3. Database Validation

The database validator checks:

- Required tables exist.
- Expected records are present.
- Required identifiers are not missing or duplicated where checked.
- Required shipment fields are populated.
- Foreign-key relationships are valid.
- Tracking timestamps and event ordering are checked.
- Each shipment has an ETA estimate.
- SQLite's integrity check succeeds.

A validation status of `PASS` means no blocking errors were found. Warnings can still be present.

## 4. Anomaly Testing

The generator injects deterministic examples of:

- Late ingestion
- Duplicate tracking event
- Impossible event order
- Future-dated event
- Delivered shipment with an `in_transit` tracking event

The anomaly tests verify that the intended anomaly patterns exist.

These tests do not, by themselves, prove that every anomaly will be automatically detected or corrected in production.

## 5. Reproducibility

The configured seed is `20261022`.

Reproducibility tests check that repeated generation with the same seed produces equivalent data and that a different seed changes the generated shipment data.

For repeatable results, use the same configuration and unchanged generator code.

## 6. ETA Evaluation

The evaluation component reports:

- MAE in minutes
- RMSE in minutes
- Delay precision
- Delay recall
- Delay F1 score
- Confusion matrix
- Evaluated shipment count
- Missing predictions

The evaluation unit tests use a small known example to verify the calculations.

## 7. Latest Starter Pipeline Results

The latest verified starter pipeline run produced the following results:

| Check | Result |
|---|---:|
| Shipments | 200 |
| Tracking events | 1,202 |
| Database validation errors | 0 |
| Database validation warnings | 2 |
| Predictions generated | 200 |
| Evaluated shipments | 181 |
| MAE | 70.28 minutes |
| RMSE | 116.63 minutes |
| Delay precision | 0.5000 |
| Delay recall | 0.0556 |
| Delay F1 score | 0.1000 |

The two event-order warnings correspond to deliberately injected impossible-order anomalies.

The low delay recall indicates that the baseline misses many delayed shipments. This limitation must be acknowledged rather than hidden.

## 8. Re-running Validation

Run the starter pipeline:

```powershell
python scripts\run_pipeline.py
```

Run the full configuration:

```powershell
python scripts\run_pipeline.py config/full.json
```

The pipeline generates the data, loads SQLite, validates the database, produces ETA predictions, and writes the evaluation report.

Run the full unit-test suite separately using the command in Section 2.

## 9. Future Validation Improvements

Potential improvements include:

- Add behavioral tests for future events and late ingestion.
- Verify that changing records after prediction time does not change historical predictions.
- Check that injected anomaly labels map to the exact affected records.
- Test the full configuration in a clean environment.
- Add service-level-specific delay thresholds.
- Compare the baseline against simple alternative prediction methods.
- Evaluate on representative real-world historical data before making operational claims.
