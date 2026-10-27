
# Assumptions and Trade-offs

## 1. Synthetic Data

**Assumption:** Real carrier, shipment, weather, and facility-queue data is not available for this project.

**Decision:** Generate synthetic data with documented rules and a fixed random seed.

**Trade-off:** Synthetic data makes testing safe, repeatable, and easy to share. However, its patterns may not represent real logistics operations, so its evaluation results cannot establish production performance.

## 2. Python and SQLite

**Assumption:** The project should be easy to run locally without external infrastructure.

**Decision:** Use Python for generation, validation, prediction, and evaluation, with SQLite for structured storage.

**Trade-off:** SQLite is lightweight and requires no separate database server. A production system with concurrent writers, large streaming workloads, or distributed access may require a server database and additional infrastructure.

## 3. CSV and JSON Exports

**Assumption:** Reviewers should be able to inspect the data without special database tools.

**Decision:** Export datasets and predictions in CSV and JSON formats.

**Trade-off:** CSV is convenient for spreadsheets and analysis, while JSON preserves structured records. Maintaining multiple export formats increases storage use and requires care to keep outputs consistent.

## 4. Fixed Random Seed

**Assumption:** The same inputs should reproduce the same generated dataset.

**Decision:** Use seed `20261022` and deterministic identifier-generation rules.

**Trade-off:** Reproducibility makes debugging and testing easier. A fixed seed alone does not guarantee identical outputs if the generator logic, configuration, or execution environment changes.

## 5. Rule-Based ETA Prediction

**Assumption:** A simple baseline is appropriate before introducing a trained forecasting model.

**Decision:** Start from the planned ETA and add estimated delays from eligible weather and facility-queue observations.

**Trade-off:** The model is easy to explain, inspect, and test. It does not learn complex relationships from historical data and may perform poorly when actual delay patterns differ from the chosen rules.

## 6. Simplified Weather Impact

**Assumption:** Weather severity can be represented using fixed delay adjustments for an initial prototype.

**Decision:** Apply documented minute adjustments according to severity.

**Trade-off:** This makes the calculation transparent, but it does not capture weather duration, geographic effects, road conditions, or interactions between disruptions. Multiple matching records can also add up and potentially overestimate delays.

## 7. Facility Queue Estimates

**Assumption:** A recent queue observation that remains valid is a useful signal of potential waiting time.

**Decision:** Use the latest valid destination queue observation available at prediction time.

**Trade-off:** This provides a simple operational signal. Its usefulness depends on the accuracy and freshness of the synthetic queue estimates.

## 8. Prediction-Time Data Availability

**Assumption:** A historical prediction must use only information that was available at the time it was made.

**Decision:** Filter tracking events using both event time and ingestion time. Exclude future observations from the prediction.

**Trade-off:** This avoids a common form of data leakage. Late-arriving events may be excluded even when they describe something that happened earlier, because the system had not received them at prediction time.

## 9. Prediction Horizon

**Assumption:** A 24-hour prediction horizon is a useful initial target.

**Decision:** Calculate prediction time as planned ETA minus 24 hours, moving it forward to planned departure when necessary.

**Trade-off:** This keeps predictions within the shipment's planned journey window. For some shipments, the effective prediction horizon is shorter than 24 hours and should be documented when comparing results.

## 10. Delay Threshold

**Assumption:** A delay exceeding 60 minutes is a useful initial definition of a late shipment.

**Decision:** Use a fixed 60-minute threshold for the baseline classifier.

**Trade-off:** A single threshold is easy to understand and compare. Different service levels may require different thresholds, and the current implementation does not dynamically apply the threshold from each service-level record.

## 11. Separate Ground Truth

**Assumption:** Evaluation labels should not be mixed into the operational prediction inputs.

**Decision:** Export ground truth separately from the operational SQLite tables.

**Trade-off:** This makes the prediction/evaluation boundary clearer. The project still needs tests and careful code review to ensure labels do not influence prediction logic indirectly.

## 12. Injected Anomalies

**Assumption:** The pipeline should demonstrate how it handles common data-quality problems.

**Decision:** Include deterministic examples of late ingestion, duplicate events, impossible order, future timestamps, and conflicting delivery status.

**Trade-off:** Anomaly injection supports repeatable tests. It intentionally makes some records invalid, so validation warnings must be interpreted in the context of the test dataset.

## 13. Evaluation Limitations

The evaluation uses only eligible records with actual delivery timestamps and valid delay labels.

MAE and RMSE measure ETA error, while precision, recall, and F1 measure delay classification quality.

The starter dataset is small, synthetic, and intended for quick testing. Its metrics are a baseline rather than proof of real-world accuracy. A production evaluation would require representative historical data, time-aware train/test separation where applicable, and comparisons against operational baselines.
