import streamlit as st
import pandas as pd


RISK_COLORS = {
    "HIGH":   "#c0392b",
    "MEDIUM": "#e67e22",
    "LOW":    "#27ae60",
}


def render_health_leaderboard(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("No health score data available.")
        return

    display_df = df[[
        "rank", "machine_id", "model", "age_years",
        "health_score", "total_anomalies",
        "recent_anomalies", "failure_risk"
    ]].copy()

    display_df.columns = [
        "Rank", "Machine ID", "Model", "Age (Years)",
        "Health Score", "Total Anomalies",
        "Recent Anomalies (7d)", "Failure Risk"
    ]

    def color_risk(val):
        color = RISK_COLORS.get(val, "#ffffff")
        return f"color: {color}; font-weight: bold"

    def color_health(val):
        if val <= 25:
            return "color: #c0392b"
        elif val <= 60:
            return "color: #e67e22"
        else:
            return "color: #27ae60"

    styled = display_df.style\
        .applymap(color_risk, subset=["Failure Risk"])\
        .applymap(color_health, subset=["Health Score"])\
        .format({"Health Score": "{:.2f}"})\
        .hide(axis="index")

    st.dataframe(styled, use_container_width=True, height=400)