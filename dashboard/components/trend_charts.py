import plotly.graph_objects as go
import streamlit as st
import pandas as pd


SENSOR_COLORS = {
    "volt":      "#4C9BE8",
    "rotate":    "#56C9A0",
    "pressure":  "#E8834C",
    "vibration": "#B56CE8",
}


def render_sensor_trends(df: pd.DataFrame, machine_id: int) -> None:
    if df.empty:
        st.warning(f"No sensor data available for Machine {machine_id}.")
        return

    sensors = df["sensor_name"].unique()

    for sensor in sensors:
        sensor_df = df[df["sensor_name"] == sensor].copy()
        color = SENSOR_COLORS.get(sensor, "#FFFFFF")

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=sensor_df["reading_date"],
            y=sensor_df["avg_value"],
            mode="lines",
            name="Daily Average",
            line=dict(color=color, width=2),
        ))

        fig.add_trace(go.Scatter(
            x=pd.concat([sensor_df["reading_date"], sensor_df["reading_date"].iloc[::-1]]),
            y=pd.concat([sensor_df["max_value"], sensor_df["min_value"].iloc[::-1]]),
            fill="toself",
            fillcolor=color.replace(")", ", 0.15)").replace("rgb", "rgba"),
            line=dict(color="rgba(255,255,255,0)"),
            name="Min/Max Range",
            showlegend=True,
        ))

        fig.update_layout(
            title=f"Machine {machine_id} — {sensor.capitalize()} Trend",
            xaxis_title="Date",
            yaxis_title=sensor.capitalize(),
            template="plotly_dark",
            height=300,
            margin=dict(l=40, r=40, t=50, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )

        st.plotly_chart(fig, use_container_width=True)