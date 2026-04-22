import pandas as pd
from sqlalchemy import text
from db.connection import engine


RISK_WINDOW_DAYS = 7
RISK_THRESHOLD = 5


def compute_machine_health_scores() -> pd.DataFrame:
    query = """
        SELECT
            dm.machine_id,
            dm.model,
            dm.age_years,
            COUNT(fae.anomaly_key) AS total_anomalies
        FROM warehouse.dim_machine dm
        LEFT JOIN warehouse.fact_anomaly_events fae
            ON dm.machine_key = fae.machine_key
        GROUP BY dm.machine_id, dm.model, dm.age_years
        ORDER BY dm.machine_id
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    max_anomalies = df["total_anomalies"].max()

    if max_anomalies == 0:
        df["health_score"] = 100.0
    else:
        df["health_score"] = (
            1 - (df["total_anomalies"] / max_anomalies)
        ) * 100
        df["health_score"] = df["health_score"].round(2)

    return df


def compute_failure_risk(days: int = RISK_WINDOW_DAYS) -> pd.DataFrame:
    query = f"""
        SELECT
            dm.machine_id,
            dm.model,
            COUNT(fae.anomaly_key) AS recent_anomalies
        FROM warehouse.dim_machine dm
        LEFT JOIN warehouse.fact_anomaly_events fae
            ON dm.machine_key = fae.machine_key
            AND fae.detected_at >= (
                SELECT MAX(detected_at) FROM warehouse.fact_anomaly_events
            ) - INTERVAL '{days} days'
        GROUP BY dm.machine_id, dm.model
        ORDER BY recent_anomalies DESC
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    df["failure_risk"] = df["recent_anomalies"].apply(
        lambda x: "HIGH" if x >= RISK_THRESHOLD
        else ("MEDIUM" if x >= 2 else "LOW")
    )

    return df


def get_machines_at_risk(days: int = RISK_WINDOW_DAYS) -> pd.DataFrame:
    df = compute_failure_risk(days)
    return df[df["failure_risk"].isin(["HIGH", "MEDIUM"])].reset_index(drop=True)