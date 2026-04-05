import numpy as np
import pandas as pd
from sqlalchemy import text
from db.connection import engine


ROLLING_WINDOW = 24      # 24-hour rolling window (data is hourly)
Z_SCORE_THRESHOLD = 3.0  # Standard deviations beyond which a reading is anomalous


def fetch_sensor_readings() -> pd.DataFrame:
    query = """
        SELECT
            fsr.reading_key,
            fsr.machine_key,
            fsr.sensor_key,
            fsr.reading_timestamp,
            fsr.sensor_value,
            dst.sensor_name
        FROM warehouse.fact_sensor_readings fsr
        JOIN warehouse.dim_sensor_type dst
            ON fsr.sensor_key = dst.sensor_key
        ORDER BY fsr.machine_key, fsr.sensor_key, fsr.reading_timestamp
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    print(f"Fetched {len(df):,} sensor readings.")
    return df


def compute_rolling_zscore(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["machine_key", "sensor_key", "reading_timestamp"]).copy()

    def zscore_group(group: pd.DataFrame) -> pd.DataFrame:
        values = group["sensor_value"]
        rolling_mean = values.rolling(window=ROLLING_WINDOW, min_periods=1).mean()
        rolling_std = values.rolling(window=ROLLING_WINDOW, min_periods=1).std()
        rolling_std = rolling_std.replace(0, np.nan)

        result = group.copy()
        result["rolling_mean"] = rolling_mean
        result["rolling_std"] = rolling_std
        result["z_score"] = (values - rolling_mean) / rolling_std
        return result

    # Compute z-scores on non-grouping columns only
    zscore_cols = df.groupby(
        ["machine_key", "sensor_key"], group_keys=False
    ).apply(zscore_group, include_groups=False).reset_index(drop=True)

    # Re-attach the grouping columns from the sorted original
    df = df.reset_index(drop=True)
    df["rolling_mean"] = zscore_cols["rolling_mean"]
    df["rolling_std"] = zscore_cols["rolling_std"]
    df["z_score"] = zscore_cols["z_score"]

    return df


def flag_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag rows where the absolute z-score exceeds the threshold.
    Returns only the anomalous rows.
    """
    df["z_score"] = df["z_score"].fillna(0)
    anomalies = df[np.abs(df["z_score"]) > Z_SCORE_THRESHOLD].copy()
    print(f"Detected {len(anomalies):,} anomalous readings "
          f"(threshold: z > {Z_SCORE_THRESHOLD}, window: {ROLLING_WINDOW}h).")
    return anomalies


def write_anomaly_events(anomalies: pd.DataFrame) -> None:
    if anomalies.empty:
        print("No anomalies to write.")
        return

    # Reset index after groupby/apply to ensure column access is reliable
    anomalies = anomalies.reset_index(drop=True)

    records = [
        {
            "machine_key":      int(row["machine_key"]),
            "sensor_key":       int(row["sensor_key"]),
            "detected_at":      row["reading_timestamp"],
            "sensor_value":     float(row["sensor_value"]),
            "z_score":          round(float(row["z_score"]), 4),
            "detection_method": "zscore",
        }
        for _, row in anomalies.iterrows()
    ]

    with engine.begin() as conn:
        conn.execute(
            text("TRUNCATE warehouse.fact_anomaly_events RESTART IDENTITY CASCADE;")
        )

    chunk_size = 5000
    total = len(records)
    for i in range(0, total, chunk_size):
        chunk = records[i: i + chunk_size]
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO warehouse.fact_anomaly_events
                        (machine_key, sensor_key, detected_at,
                         sensor_value, z_score, detection_method)
                    VALUES
                        (:machine_key, :sensor_key, :detected_at,
                         :sensor_value, :z_score, :detection_method)
                """),
                chunk,
            )
        print(
            f"[fact_anomaly_events] Inserted "
            f"{min(i + chunk_size, total):,}/{total:,} rows...",
            end="\r"
        )

    print(f"\n[fact_anomaly_events] Wrote {total:,} anomaly events.")


def run_anomaly_detection() -> None:
    print("Starting anomaly detection...\n")

    df = fetch_sensor_readings()
    df = compute_rolling_zscore(df)
    anomalies = flag_anomalies(df)
    write_anomaly_events(anomalies)

    print("\nAnomaly detection complete.")


if __name__ == "__main__":
    run_anomaly_detection()