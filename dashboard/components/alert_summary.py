import streamlit as st
import pandas as pd


def render_alert_summary(at_risk: pd.DataFrame) -> None:
    if at_risk.empty:
        st.markdown(
            '<div class="alert-success">'
            "No machines are currently at elevated risk."
            "</div>",
            unsafe_allow_html=True,
        )
        return

    high_risk = at_risk[at_risk["failure_risk"] == "HIGH"]
    medium_risk = at_risk[at_risk["failure_risk"] == "MEDIUM"]

    if not high_risk.empty:
        for _, row in high_risk.iterrows():
            st.markdown(
                f'<div class="alert-high">'
                f"<strong>Machine {row['machine_id']} ({row['model']})</strong>"
                f" — HIGH RISK<br>"
                f"{row['recent_anomalies']} anomalies in the last 7 days. "
                f"Immediate inspection recommended."
                f"</div>",
                unsafe_allow_html=True,
            )

    if not medium_risk.empty:
        for _, row in medium_risk.iterrows():
            st.markdown(
                f'<div class="alert-medium">'
                f"<strong>Machine {row['machine_id']} ({row['model']})</strong>"
                f" — MEDIUM RISK<br>"
                f"{row['recent_anomalies']} anomalies in the last 7 days. "
                f"Schedule preventive maintenance."
                f"</div>",
                unsafe_allow_html=True,
            )