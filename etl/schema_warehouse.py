from sqlalchemy import text
from db.connection import engine


WAREHOUSE_DDL = """
CREATE SCHEMA IF NOT EXISTS warehouse;

-- Dimension: machines
CREATE TABLE IF NOT EXISTS warehouse.dim_machine (
    machine_key     SERIAL PRIMARY KEY,
    machine_id      INTEGER NOT NULL UNIQUE,
    model           VARCHAR(50) NOT NULL,
    age_years       INTEGER NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Dimension: sensor types
CREATE TABLE IF NOT EXISTS warehouse.dim_sensor_type (
    sensor_key      SERIAL PRIMARY KEY,
    sensor_name     VARCHAR(50) NOT NULL UNIQUE,
    unit            VARCHAR(20),
    description     TEXT
);

-- Dimension: error types
CREATE TABLE IF NOT EXISTS warehouse.dim_error_type (
    error_key       SERIAL PRIMARY KEY,
    error_code      VARCHAR(50) NOT NULL UNIQUE,
    description     TEXT
);

-- Dimension: failure types
CREATE TABLE IF NOT EXISTS warehouse.dim_failure_type (
    failure_key     SERIAL PRIMARY KEY,
    failure_code    VARCHAR(50) NOT NULL UNIQUE,
    component       VARCHAR(50),
    description     TEXT
);

-- Fact: sensor readings (one row per machine per hour per sensor)
CREATE TABLE IF NOT EXISTS warehouse.fact_sensor_readings (
    reading_key         SERIAL PRIMARY KEY,
    machine_key         INTEGER NOT NULL REFERENCES warehouse.dim_machine(machine_key),
    sensor_key          INTEGER NOT NULL REFERENCES warehouse.dim_sensor_type(sensor_key),
    reading_timestamp   TIMESTAMP NOT NULL,
    sensor_value        NUMERIC(12, 6) NOT NULL,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- Fact: error events
CREATE TABLE IF NOT EXISTS warehouse.fact_errors (
    error_event_key     SERIAL PRIMARY KEY,
    machine_key         INTEGER NOT NULL REFERENCES warehouse.dim_machine(machine_key),
    error_key           INTEGER NOT NULL REFERENCES warehouse.dim_error_type(error_key),
    event_timestamp     TIMESTAMP NOT NULL,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- Fact: failure events
CREATE TABLE IF NOT EXISTS warehouse.fact_failures (
    failure_event_key   SERIAL PRIMARY KEY,
    machine_key         INTEGER NOT NULL REFERENCES warehouse.dim_machine(machine_key),
    failure_key         INTEGER NOT NULL REFERENCES warehouse.dim_failure_type(failure_key),
    event_timestamp     TIMESTAMP NOT NULL,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- Fact: maintenance records
CREATE TABLE IF NOT EXISTS warehouse.fact_maintenance (
    maintenance_key     SERIAL PRIMARY KEY,
    machine_key         INTEGER NOT NULL REFERENCES warehouse.dim_machine(machine_key),
    failure_key         INTEGER NOT NULL REFERENCES warehouse.dim_failure_type(failure_key),
    event_timestamp     TIMESTAMP NOT NULL,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- Fact: anomaly events (populated by anomaly detection module in Step 5)
CREATE TABLE IF NOT EXISTS warehouse.fact_anomaly_events (
    anomaly_key         SERIAL PRIMARY KEY,
    machine_key         INTEGER NOT NULL REFERENCES warehouse.dim_machine(machine_key),
    sensor_key          INTEGER NOT NULL REFERENCES warehouse.dim_sensor_type(sensor_key),
    detected_at         TIMESTAMP NOT NULL,
    sensor_value        NUMERIC(12, 6) NOT NULL,
    z_score             NUMERIC(8, 4),
    detection_method    VARCHAR(20) NOT NULL DEFAULT 'zscore',
    created_at          TIMESTAMP DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_sensor_readings_machine
    ON warehouse.fact_sensor_readings(machine_key);

CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp
    ON warehouse.fact_sensor_readings(reading_timestamp);

CREATE INDEX IF NOT EXISTS idx_anomaly_machine
    ON warehouse.fact_anomaly_events(machine_key);

CREATE INDEX IF NOT EXISTS idx_anomaly_timestamp
    ON warehouse.fact_anomaly_events(detected_at);
"""


def create_warehouse_tables() -> None:
    with engine.begin() as conn:
        conn.execute(text(WAREHOUSE_DDL))
    print("Warehouse tables created successfully.")


if __name__ == "__main__":
    create_warehouse_tables()