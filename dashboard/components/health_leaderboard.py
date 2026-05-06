import streamlit as st
import pandas as pd


RISK_COLORS = {
    "HIGH":   "#ef4444",
    "MEDIUM": "#f97316",
    "LOW":    "#22c55e",
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
        "Rank", "Machine ID", "Model", "Age",
        "Health Score", "Anomalies",
        "Recent (7d)", "Risk"
    ]

    # Set Rank as index to eliminate the unnamed integer index column
    display_df = display_df.set_index("Rank")

    def color_risk(val):
        color = RISK_COLORS.get(val, "#9ca3af")
        return f"color: {color}; font-weight: 600"

    def color_health(val):
        if val <= 25:
            return "color: #ef4444; font-weight: 600"
        elif val <= 60:
            return "color: #f97316; font-weight: 600"
        else:
            return "color: #22c55e; font-weight: 600"

    styled = (
        display_df.style
        .map(color_risk, subset=["Risk"])
        .map(color_health, subset=["Health Score"])
        .format({"Health Score": "{:.2f}"})
        .set_properties(**{"font-size": "0.8rem"})
    )

    st.dataframe(
        styled,
        use_container_width=True,
        height=380,
        column_config={
            "Rank":         st.column_config.NumberColumn(width="small"),
            "Machine ID":   st.column_config.NumberColumn(width="small"),
            "Model":        st.column_config.TextColumn(width="small"),
            "Age":          st.column_config.NumberColumn(width="small"),
            "Health Score": st.column_config.NumberColumn(width="medium"),
            "Anomalies":    st.column_config.NumberColumn(width="medium"),
            "Recent (7d)":  st.column_config.NumberColumn(width="small"),
            "Risk":         st.column_config.TextColumn(width="small"),
        }
    )