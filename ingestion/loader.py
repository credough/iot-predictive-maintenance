import os
import pandas as pd
from sqlalchemy import text
from db.connection import engine

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")

FILE_MAP = {
    "telemetry":    "PdM_telemetry.csv",
    "machines":     "PdM_machines.csv",
    "errors":       "PdM_errors.csv",
    "failures":     "PdM_failures.csv",
    "maintenance":  "PdM_maint.csv",
}

EXPECTED_COLUMNS = {
    "telemetry":    {"datetime", "machineID", "volt", "rotate", "pressure", "vibration"},
    "machines":     {"machineID", "model", "age"},
    "errors":       {"datetime", "machineID", "errorID"},
    "failures":     {"datetime", "machineID", "failure"},
    "maintenance":  {"datetime", "machineID", "comp"},
}


def load_csv(name: str, filename: str) -> pd.DataFrame:
    filepath = os.path.join(DATA_DIR, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Expected file not found: {filepath}\n"
            f"Place Kaggle CSVs in data/raw/ before running ingestion."
        )

    df = pd.read_csv(filepath)

    # Normalize column names
    df.columns = df.columns.str.strip()

    # Validate expected columns are present
    expected = EXPECTED_COLUMNS[name]
    actual = set(df.columns)
    missing = expected - actual
    if missing:
        raise ValueError(
            f"[{name}] Missing expected columns: {missing}. "
            f"Found: {actual}"
        )

    print(f"[{name}] Loaded {len(df):,} rows, {len(df.columns)} columns.")
    return df


def validate_dataframe(name: str, df: pd.DataFrame) -> pd.DataFrame:
    original_count = len(df)

    # Drop rows where all non-system columns are null
    df = df.dropna(how="all")

    # For telemetry, drop rows missing machineID or datetime
    if name == "telemetry":
        df = df.dropna(subset=["datetime", "machineID"])

    dropped = original_count - len(df)
    if dropped > 0:
        print(f"[{name}] Dropped {dropped:,} fully null or invalid rows.")

    return df


def insert_staging(name: str, df: pd.DataFrame) -> None:
    table = f"staging.{name}"

    # Lowercase all column names to match PostgreSQL DDL
    df.columns = df.columns.str.lower()

    # Convert all values to string for staging
    df = df.astype(str).replace("nan", None)

    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY;"))

    df.to_sql(
        name=name,
        schema="staging",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=100,
    )

    print(f"[{name}] Inserted {len(df):,} rows into {table}.")


def run_ingestion() -> None:
    print("Starting ingestion pipeline...\n")

    for name, filename in FILE_MAP.items():
        print(f"--- Processing: {name} ---")
        df = load_csv(name, filename)
        df = validate_dataframe(name, df)
        insert_staging(name, df)
        print()

    print("Ingestion complete.")


if __name__ == "__main__":
    run_ingestion()