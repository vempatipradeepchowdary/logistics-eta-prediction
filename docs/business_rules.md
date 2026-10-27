
# Business Rules

## 1. Reproducible Data Generation

- The default random seed is `20261022`.
- The same configuration and seed should produce the same generated datasets.
- Identifiers are generated deterministically from the configured data-generation process.
- Starter and full configurations use separate output directories.

## 2. Shipment Lifecycle

A shipment can have tracking events such as:

1. `shipment_created`
2. `picked_up`
3. `arrived_at_hub`
4. `departed_hub`
5. `out_for_delivery`
6. `delivered`

Additional `in_transit` events may occur in the synthetic data. Injected anomalies can intentionally violate normal lifecycle expectations.

The shipment record and its tracking events are separate data sources. Their statuses may disagree in deliberately injected anomaly cases.

## 3. Timestamp Rules

- Timestamps are represented in UTC using ISO 8601 format.
- `event_time` represents when a tracking event occurred.
- `ingestion_time` represents when the system received the event.
- An event can be used for prediction only if both timestamps are at or before the prediction time.
- Events received late must not be treated as information that was available earlier.
- Events with impossible chronological order are treated as data-quality anomalies.

## 4. Prediction Time

The initial prediction time is:

`planned_eta - prediction_horizon`

The default prediction horizon is 24 hours.

If the calculated prediction time is earlier than the planned departure, the current implementation uses the planned departure as the prediction time.

This rule means the actual prediction horizon can be shorter than 24 hours for some shipments.

## 5. ETA Prediction Rules

The rule-based ETA engine starts with the shipment's planned ETA.

It adds estimated disruption time using eligible destination weather events and a valid destination facility-queue observation.

### Weather disruption

A weather event is considered when its facility matches the shipment destination and its time window overlaps the period from prediction time through planned ETA.

The baseline delay adjustments are:

| Severity | Added delay |
|---|---:|
| Severe, high, or extreme | 180 minutes |
| Moderate or medium | 60 minutes |
| Low or minor | 15 minutes |
| Other or unknown | 0 minutes |

The implementation applies the adjustment for each qualifying weather record. Multiple qualifying records can therefore add multiple delay adjustments.

These values are synthetic business assumptions, not measurements of actual weather impact.

### Facility queue

The engine selects the latest destination queue observation that:

- Was observed at or before prediction time.
- Remains valid at prediction time.

The non-negative estimated queue wait is added to the predicted delay.

### Final ETA

The baseline calculation is:

`Predicted ETA = Planned ETA + Estimated disruption minutes`

The current implementation does not use a trained machine-learning model.

## 6. Delay Classification

A prediction is marked as delayed when:

`Predicted ETA > Planned ETA + 60 minutes`

Otherwise, it is marked as not delayed.

The current implementation uses a fixed 60-minute threshold. Although service-level records exist in the data model, this threshold is not currently selected dynamically from each shipment's service level.

## 7. Ground Truth and Evaluation

- Ground truth is stored separately from operational prediction inputs.
- Predictions are compared with eligible ground-truth delivery records.
- Records without an actual delivery timestamp or a valid delay label are excluded.
- Anomaly-only ground-truth records are not treated as ordinary delivery outcomes.
- ETA error is measured in minutes.
- Delay detection is evaluated using precision, recall, F1 score, and confusion-matrix counts.

## 8. Injected Anomalies

The generator injects examples of:

- Late event ingestion
- Duplicate tracking events
- Impossible tracking-event order
- Future-dated tracking events
- A delivered shipment whose tracking feed reports `in_transit`

These cases help test data-quality controls and anomaly detection. They are synthetic test cases and should not be interpreted as evidence of real carrier incidents.
