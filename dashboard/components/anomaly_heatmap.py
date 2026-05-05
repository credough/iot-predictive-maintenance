import plotly.graph_objects as go
import streamlit as st
import pandas as pd


def render_anomaly_heatmap(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("No anomaly data available for heatmap.")
        return

    pivot = df.pivot_table(
        index="machine_id",
        columns="year_month",
        values="anomaly_count",
        fill_value=0,
    )

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=[f"Machine {m}" for m in pivot.index.tolist()],
        colorscale=[
            [0.0,  "#1a1a2e"],
            [0.25, "#16213e"],
            [0.5,  "#E8834C"],
            [0.75, "#e05c2a"],
            [1.0,  "#c0392b"],
        ],
        hoverongaps=False,
        colorbar=dict(title="Anomalies"),
    ))

    fig.update_layout(
        title="Anomaly Frequency by Machine and Month",
        xaxis_title="Month",
        yaxis_title="Machine",
        template="plotly_dark",
        height=600,
        margin=dict(l=100, r=40, t=60, b=60),
    )

    st.plotly_chart(fig, use_container_width=True)