from sqlalchemy import text
from db.connection import engine


STAGING_DDL = """
CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.telemetry (
    id              SERIAL PRIMARY KEY,
    datetime        TEXT,
    machineid       TEXT,
    volt            TEXT,
    rotate          TEXT,
    pressure        TEXT,
    vibration       TEXT,
    ingested_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.machines (
    id              SERIAL PRIMARY KEY,
    machineid       TEXT,
    model           TEXT,
    age             TEXT,
    ingested_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.errors (
    id              SERIAL PRIMARY KEY,
    datetime        TEXT,
    machineid       TEXT,
    errorid         TEXT,
    ingested_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.failures (
    id              SERIAL PRIMARY KEY,
    datetime        TEXT,
    machineid       TEXT,
    failure         TEXT,
    ingested_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.maintenance (
    id              SERIAL PRIMARY KEY,
    datetime        TEXT,
    machineid       TEXT,
    comp            TEXT,
    ingested_at     TIMESTAMP DEFAULT NOW()
);
"""


def create_staging_tables() -> None:
    with engine.begin() as conn:
        conn.execute(text(STAGING_DDL))
    print("Staging tables created successfully.")


if __name__ == "__main__":
    create_staging_tables()