import pandas as pd
from sqlalchemy import text
from db.connection import engine


def get_sensor_trends(machine_id: int) -> pd.DataFrame:
    """
    Returns daily average sensor readings for a specific machine.
    Aggregates hourly fact_sensor_readings to daily granularity
    to reduce query volume for dashboard rendering.
    """
    query = """
        SELECT
            DATE(fsr.reading_timestamp)     AS reading_date,
            dst.sensor_name,
            AVG(fsr.sensor_value)           AS avg_value,
            MIN(fsr.sensor_value)           AS min_value,
            MAX(fsr.sensor_value)           AS max_value,
            STDDEV(fsr.sensor_value)        AS stddev_value
        FROM warehouse.fact_sensor_readings fsr
        JOIN warehouse.dim_machine dm
            ON fsr.machine_key = dm.machine_key
        JOIN warehouse.dim_sensor_type dst
            ON fsr.sensor_key = dst.sensor_key
        WHERE dm.machine_id = :machine_id
        GROUP BY DATE(fsr.reading_timestamp), dst.sensor_name
        ORDER BY reading_date, dst.sensor_name
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn, params={"machine_id": machine_id})
    return df


def get_anomaly_frequency(machine_id: int = None) -> pd.DataFrame:
    """
    Returns anomaly counts grouped by machine and sensor type.
    If machine_id is provided, filters to that machine only.
    """
    base_query = """
        SELECT
            dm.machine_id,
            dm.model,
            dst.sensor_name,
            COUNT(fae.anomaly_key)          AS anomaly_count,
            MIN(fae.detected_at)            AS first_detected,
            MAX(fae.detected_at)            AS last_detected
        FROM warehouse.fact_anomaly_events fae
        JOIN warehouse.dim_machine dm
            ON fae.machine_key = dm.machine_key
        JOIN warehouse.dim_sensor_type dst
            ON fae.sensor_key = dst.sensor_key
        {where_clause}
        GROUP BY dm.machine_id, dm.model, dst.sensor_name
        ORDER BY dm.machine_id, anomaly_count DESC
    """

    if machine_id is not None:
        query = base_query.format(where_clause="WHERE dm.machine_id = :machine_id")
        with engine.connect() as conn:
            df = pd.read_sql(
                text(query), conn, params={"machine_id": machine_id}
            )
    else:
        query = base_query.format(where_clause="")
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)

    return df


def get_anomaly_heatmap_data() -> pd.DataFrame:
    """
    Returns anomaly counts grouped by machine and month.
    Used to render the anomaly heatmap in the dashboard.
    """
    query = """
        SELECT
            dm.machine_id,
            TO_CHAR(fae.detected_at, 'YYYY-MM') AS year_month,
            COUNT(fae.anomaly_key)              AS anomaly_count
        FROM warehouse.fact_anomaly_events fae
        JOIN warehouse.dim_machine dm
            ON fae.machine_key = dm.machine_key
        GROUP BY dm.machine_id, TO_CHAR(fae.detected_at, 'YYYY-MM')
        ORDER BY dm.machine_id, year_month
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df


def get_fleet_summary() -> dict:
    """
    Returns top-level KPI counts for the dashboard summary cards.
    """
    query = """
        SELECT
            (SELECT COUNT(*) FROM warehouse.dim_machine)            AS total_machines,
            (SELECT COUNT(*) FROM warehouse.fact_anomaly_events)    AS total_anomalies,
            (SELECT COUNT(*) FROM warehouse.fact_failures)          AS total_failures,
            (SELECT COUNT(DISTINCT machine_key)
             FROM warehouse.fact_anomaly_events
             WHERE detected_at >= (
                 SELECT MAX(detected_at) FROM warehouse.fact_anomaly_events
             ) - INTERVAL '7 days')                                 AS machines_active_anomalies
    """
    with engine.connect() as conn:
        result = conn.execute(text(query)).fetchone()

    return {
        "total_machines":           result[0],
        "total_anomalies":          result[1],
        "total_failures":           result[2],
        "machines_active_anomalies": result[3],
    }


def get_health_leaderboard() -> pd.DataFrame:
    """
    Returns all machines ranked by health score ascending
    (lowest health score first — most at-risk machines at the top).
    """
    from analytics.health_scores import compute_machine_health_scores, compute_failure_risk

    health_df = compute_machine_health_scores()
    risk_df = compute_failure_risk()

    df = health_df.merge(
        risk_df[["machine_id", "recent_anomalies", "failure_risk"]],
        on="machine_id",
        how="left",
    )

    df = df.sort_values("health_score", ascending=True).reset_index(drop=True)
    df["rank"] = df.index + 1

    return df