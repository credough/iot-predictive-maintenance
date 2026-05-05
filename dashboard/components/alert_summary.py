import streamlit as st
import pandas as pd


def render_alert_summary(at_risk: pd.DataFrame) -> None:
    st.subheader("Active Alerts")

    if at_risk.empty:
        st.success("No machines are currently at elevated risk.")
        return

    high_risk = at_risk[at_risk["failure_risk"] == "HIGH"]
    medium_risk = at_risk[at_risk["failure_risk"] == "MEDIUM"]

    if not high_risk.empty:
        for _, row in high_risk.iterrows():
            st.error(
                f"Machine {row['machine_id']} ({row['model']}) — HIGH RISK: "
                f"{row['recent_anomalies']} anomalies detected in the last 7 days. "
                f"Immediate inspection recommended."
            )

    if not medium_risk.empty:
        for _, row in medium_risk.iterrows():
            st.warning(
                f"Machine {row['machine_id']} ({row['model']}) — MEDIUM RISK: "
                f"{row['recent_anomalies']} anomalies detected in the last 7 days. "
                f"Schedule preventive maintenance."
            )