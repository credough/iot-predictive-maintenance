import pandas as pd
from sqlalchemy import text
from db.connection import engine


# ── Helpers ────────────────────────────────────────────────────────────────

def read_staging(table: str) -> pd.DataFrame:
    with engine.connect() as conn:
        df = pd.read_sql(f"SELECT * FROM staging.{table}", conn)
    return df


def get_machine_key_map() -> dict:
    with engine.connect() as conn:
        df = pd.read_sql(
            "SELECT machine_key, machine_id FROM warehouse.dim_machine", conn
        )
    return dict(zip(df["machine_id"], df["machine_key"]))


def get_sensor_key_map() -> dict:
    with engine.connect() as conn:
        df = pd.read_sql(
            "SELECT sensor_key, sensor_name FROM warehouse.dim_sensor_type", conn
        )
    return dict(zip(df["sensor_name"], df["sensor_key"]))


def get_error_key_map() -> dict:
    with engine.connect() as conn:
        df = pd.read_sql(
            "SELECT error_key, error_code FROM warehouse.dim_error_type", conn
        )
    return dict(zip(df["error_code"], df["error_key"]))


def get_failure_key_map() -> dict:
    with engine.connect() as conn:
        df = pd.read_sql(
            "SELECT failure_key, failure_code FROM warehouse.dim_failure_type", conn
        )
    return dict(zip(df["failure_code"], df["failure_key"]))


# ── Dimension Loaders ───────────────────────────────────────────────────────

def load_dim_machine() -> None:
    df = read_staging("machines")

    df = df.rename(columns={"machineid": "machine_id"})
    df["machine_id"] = pd.to_numeric(df["machine_id"], errors="coerce")
    df["age_years"] = pd.to_numeric(df["age"], errors="coerce")
    df = df.dropna(subset=["machine_id", "age_years"])
    df["machine_id"] = df["machine_id"].astype(int)
    df["age_years"] = df["age_years"].astype(int)
    df["model"] = df["model"].str.strip()

    records = df[["machine_id", "model", "age_years"]].to_dict(orient="records")

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE warehouse.dim_machine RESTART IDENTITY CASCADE;"))
        conn.execute(
            text("""
                INSERT INTO warehouse.dim_machine (machine_id, model, age_years)
                VALUES (:machine_id, :model, :age_years)
            """),
            records,
        )
    print(f"[dim_machine] Loaded {len(records)} machines.")


def load_dim_sensor_type() -> None:
    sensors = [
        {"sensor_name": "volt",      "unit": "V",    "description": "Voltage reading"},
        {"sensor_name": "rotate",    "unit": "RPM",  "description": "Rotation speed"},
        {"sensor_name": "pressure",  "unit": "psi",  "description": "Pressure reading"},
        {"sensor_name": "vibration", "unit": "mm/s", "description": "Vibration level"},
    ]

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE warehouse.dim_sensor_type RESTART IDENTITY CASCADE;"))
        conn.execute(
            text("""
                INSERT INTO warehouse.dim_sensor_type (sensor_name, unit, description)
                VALUES (:sensor_name, :unit, :description)
            """),
            sensors,
        )
    print(f"[dim_sensor_type] Loaded {len(sensors)} sensor types.")


def load_dim_error_type() -> None:
    error_codes = [f"error{i}" for i in range(1, 6)]
    records = [
        {"error_code": code, "description": f"Sensor error code {code}"}
        for code in error_codes
    ]

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE warehouse.dim_error_type RESTART IDENTITY CASCADE;"))
        conn.execute(
            text("""
                INSERT INTO warehouse.dim_error_type (error_code, description)
                VALUES (:error_code, :description)
            """),
            records,
        )
    print(f"[dim_error_type] Loaded {len(records)} error types.")


def load_dim_failure_type() -> None:
    failure_codes = [f"comp{i}" for i in range(1, 5)]
    records = [
        {"failure_code": code, "component": code,
         "description": f"Component {code.replace('comp', '')} failure"}
        for code in failure_codes
    ]

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE warehouse.dim_failure_type RESTART IDENTITY CASCADE;"))
        conn.execute(
            text("""
                INSERT INTO warehouse.dim_failure_type (failure_code, component, description)
                VALUES (:failure_code, :component, :description)
            """),
            records,
        )
    print(f"[dim_failure_type] Loaded {len(records)} failure types.")


# ── Fact Loaders ────────────────────────────────────────────────────────────

def load_fact_sensor_readings() -> None:
    df = read_staging("telemetry")
    machine_map = get_machine_key_map()
    sensor_map = get_sensor_key_map()

    df["machineid"] = pd.to_numeric(df["machineid"], errors="coerce").astype("Int64")
    df["reading_timestamp"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["machineid", "reading_timestamp"])

    # Unpivot sensor columns into rows — one row per reading per sensor
    sensor_cols = ["volt", "rotate", "pressure", "vibration"]
    df_melted = df.melt(
        id_vars=["machineid", "reading_timestamp"],
        value_vars=sensor_cols,
        var_name="sensor_name",
        value_name="sensor_value",
    )

    df_melted["sensor_value"] = pd.to_numeric(
        df_melted["sensor_value"], errors="coerce"
    )
    df_melted = df_melted.dropna(subset=["sensor_value"])

    df_melted["machine_key"] = df_melted["machineid"].map(machine_map)
    df_melted["sensor_key"] = df_melted["sensor_name"].map(sensor_map)
    df_melted = df_melted.dropna(subset=["machine_key", "sensor_key"])

    df_melted["machine_key"] = df_melted["machine_key"].astype(int)
    df_melted["sensor_key"] = df_melted["sensor_key"].astype(int)

    records = df_melted[
        ["machine_key", "sensor_key", "reading_timestamp", "sensor_value"]
    ].to_dict(orient="records")

    with engine.begin() as conn:
        conn.execute(
            text("TRUNCATE warehouse.fact_sensor_readings RESTART IDENTITY CASCADE;")
        )

    # Insert in chunks to manage memory
    chunk_size = 10000
    total = len(records)
    for i in range(0, total, chunk_size):
        chunk = records[i: i + chunk_size]
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO warehouse.fact_sensor_readings
                        (machine_key, sensor_key, reading_timestamp, sensor_value)
                    VALUES (:machine_key, :sensor_key, :reading_timestamp, :sensor_value)
                """),
                chunk,
            )
        print(f"[fact_sensor_readings] Inserted {min(i + chunk_size, total):,}/{total:,} rows...", end="\r")

    print(f"\n[fact_sensor_readings] Loaded {total:,} rows.")


def load_fact_errors() -> None:
    df = read_staging("errors")
    machine_map = get_machine_key_map()
    error_map = get_error_key_map()

    df["machineid"] = pd.to_numeric(df["machineid"], errors="coerce").astype("Int64")
    df["event_timestamp"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["machineid", "event_timestamp"])

    df["machine_key"] = df["machineid"].map(machine_map)
    df["error_key"] = df["errorid"].map(error_map)
    df = df.dropna(subset=["machine_key", "error_key"])

    records = df[["machine_key", "error_key", "event_timestamp"]].to_dict(orient="records")

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE warehouse.fact_errors RESTART IDENTITY CASCADE;"))
        conn.execute(
            text("""
                INSERT INTO warehouse.fact_errors
                    (machine_key, error_key, event_timestamp)
                VALUES (:machine_key, :error_key, :event_timestamp)
            """),
            records,
        )
    print(f"[fact_errors] Loaded {len(records)} rows.")


def load_fact_failures() -> None:
    df = read_staging("failures")
    machine_map = get_machine_key_map()
    failure_map = get_failure_key_map()

    df["machineid"] = pd.to_numeric(df["machineid"], errors="coerce").astype("Int64")
    df["event_timestamp"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["machineid", "event_timestamp"])

    df["machine_key"] = df["machineid"].map(machine_map)
    df["failure_key"] = df["failure"].map(failure_map)
    df = df.dropna(subset=["machine_key", "failure_key"])

    records = df[["machine_key", "failure_key", "event_timestamp"]].to_dict(orient="records")

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE warehouse.fact_failures RESTART IDENTITY CASCADE;"))
        conn.execute(
            text("""
                INSERT INTO warehouse.fact_failures
                    (machine_key, failure_key, event_timestamp)
                VALUES (:machine_key, :failure_key, :event_timestamp)
            """),
            records,
        )
    print(f"[fact_failures] Loaded {len(records)} rows.")


def load_fact_maintenance() -> None:
    df = read_staging("maintenance")
    machine_map = get_machine_key_map()
    failure_map = get_failure_key_map()

    df["machineid"] = pd.to_numeric(df["machineid"], errors="coerce").astype("Int64")
    df["event_timestamp"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["machineid", "event_timestamp"])

    df["machine_key"] = df["machineid"].map(machine_map)
    df["failure_key"] = df["comp"].map(failure_map)
    df = df.dropna(subset=["machine_key", "failure_key"])

    records = df[["machine_key", "failure_key", "event_timestamp"]].to_dict(orient="records")

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE warehouse.fact_maintenance RESTART IDENTITY CASCADE;"))
        conn.execute(
            text("""
                INSERT INTO warehouse.fact_maintenance
                    (machine_key, failure_key, event_timestamp)
                VALUES (:machine_key, :failure_key, :event_timestamp)
            """),
            records,
        )
    print(f"[fact_maintenance] Loaded {len(records)} rows.")


# ── Pipeline Entry Point ────────────────────────────────────────────────────

def run_etl() -> None:
    print("Starting ETL pipeline...\n")

    print("-- Loading dimensions --")
    load_dim_machine()
    load_dim_sensor_type()
    load_dim_error_type()
    load_dim_failure_type()

    print("\n-- Loading facts --")
    load_fact_sensor_readings()
    load_fact_errors()
    load_fact_failures()
    load_fact_maintenance()

    print("\nETL complete.")


if __name__ == "__main__":
    run_etl()