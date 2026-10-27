
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS carriers (
    carrier_id TEXT PRIMARY KEY,
    carrier_name TEXT NOT NULL,
    service_level TEXT NOT NULL
        CHECK (service_level IN ('standard', 'express')),
    active INTEGER NOT NULL CHECK (active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS facilities (
    facility_id TEXT PRIMARY KEY,
    facility_name TEXT NOT NULL,
    city TEXT NOT NULL,
    facility_type TEXT NOT NULL,
    timezone TEXT NOT NULL,
    operating_start_hour INTEGER NOT NULL
        CHECK (operating_start_hour BETWEEN 0 AND 23),
    operating_end_hour INTEGER NOT NULL
        CHECK (operating_end_hour BETWEEN 0 AND 23)
);

CREATE TABLE IF NOT EXISTS service_levels (
    service_level_id TEXT PRIMARY KEY,
    service_name TEXT NOT NULL UNIQUE
        CHECK (service_name IN ('standard', 'express')),
    max_transit_hours INTEGER NOT NULL CHECK (max_transit_hours > 0),
    delay_threshold_minutes INTEGER NOT NULL
        CHECK (delay_threshold_minutes >= 0)
);

CREATE TABLE IF NOT EXISTS routes (
    route_id TEXT PRIMARY KEY,
    origin_facility_id TEXT NOT NULL,
    destination_facility_id TEXT NOT NULL,
    distance_km REAL NOT NULL CHECK (distance_km > 0),
    planned_duration_hours REAL NOT NULL
        CHECK (planned_duration_hours > 0),
    active INTEGER NOT NULL CHECK (active IN (0, 1)),
    FOREIGN KEY (origin_facility_id) REFERENCES facilities(facility_id),
    FOREIGN KEY (destination_facility_id) REFERENCES facilities(facility_id)
);

CREATE TABLE IF NOT EXISTS shipments (
    shipment_id TEXT PRIMARY KEY,
    carrier_id TEXT NOT NULL,
    origin_facility_id TEXT NOT NULL,
    destination_facility_id TEXT NOT NULL,
    service_level_id TEXT NOT NULL,
    planned_departure_time TEXT NOT NULL,
    planned_eta TEXT NOT NULL,
    actual_delivery_time TEXT,
    status TEXT NOT NULL CHECK (
        status IN ('created', 'in_transit', 'delivered', 'cancelled')
    ),
    distance_km REAL NOT NULL CHECK (distance_km > 0),
    FOREIGN KEY (carrier_id) REFERENCES carriers(carrier_id),
    FOREIGN KEY (origin_facility_id) REFERENCES facilities(facility_id),
    FOREIGN KEY (destination_facility_id) REFERENCES facilities(facility_id),
    FOREIGN KEY (service_level_id) REFERENCES service_levels(service_level_id)
);

CREATE TABLE IF NOT EXISTS shipment_legs (
    leg_id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL,
    leg_number INTEGER NOT NULL CHECK (leg_number > 0),
    route_id TEXT NOT NULL,
    carrier_id TEXT NOT NULL,
    origin_facility_id TEXT NOT NULL,
    destination_facility_id TEXT NOT NULL,
    planned_departure_time TEXT NOT NULL,
    planned_arrival_time TEXT NOT NULL,
    UNIQUE (shipment_id, leg_number),
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
    FOREIGN KEY (route_id) REFERENCES routes(route_id),
    FOREIGN KEY (carrier_id) REFERENCES carriers(carrier_id),
    FOREIGN KEY (origin_facility_id) REFERENCES facilities(facility_id),
    FOREIGN KEY (destination_facility_id) REFERENCES facilities(facility_id)
);

CREATE TABLE IF NOT EXISTS tracking_events (
    event_id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_time TEXT NOT NULL,
    ingestion_time TEXT NOT NULL,
    facility_id TEXT NOT NULL,
    source TEXT NOT NULL,
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
    FOREIGN KEY (facility_id) REFERENCES facilities(facility_id)
);

CREATE TABLE IF NOT EXISTS facility_queues (
    queue_id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    queue_length INTEGER NOT NULL CHECK (queue_length >= 0),
    estimated_wait_minutes INTEGER NOT NULL
        CHECK (estimated_wait_minutes >= 0),
    observed_at TEXT NOT NULL,
    valid_until TEXT NOT NULL,
    FOREIGN KEY (facility_id) REFERENCES facilities(facility_id)
);

CREATE TABLE IF NOT EXISTS weather_events (
    weather_event_id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    condition TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('moderate', 'high')),
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    FOREIGN KEY (facility_id) REFERENCES facilities(facility_id)
);

CREATE TABLE IF NOT EXISTS eta_estimates (
    eta_id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL,
    prediction_time TEXT NOT NULL,
    predicted_eta TEXT NOT NULL,
    predicted_delay INTEGER NOT NULL CHECK (predicted_delay IN (0, 1)),
    model_version TEXT NOT NULL,
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
);

CREATE TABLE IF NOT EXISTS delay_reasons (
    delay_id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    delay_minutes INTEGER NOT NULL CHECK (delay_minutes > 0),
    rule TEXT NOT NULL,
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
);

-- Indexes for common shipment and timeline queries.
CREATE INDEX IF NOT EXISTS idx_events_shipment_time
    ON tracking_events(shipment_id, event_time);

CREATE INDEX IF NOT EXISTS idx_eta_shipment_prediction
    ON eta_estimates(shipment_id, prediction_time);

CREATE INDEX IF NOT EXISTS idx_legs_shipment
    ON shipment_legs(shipment_id);

CREATE INDEX IF NOT EXISTS idx_delays_shipment
    ON delay_reasons(shipment_id);
