import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from analytics.queries import (
    get_fleet_summary,
    get_sensor_trends,
    get_anomaly_heatmap_data,
    get_health_leaderboard,
)
from analytics.health_scores import get_machines_at_risk

from dashboard.components.kpi_cards import render_kpi_cards
from dashboard.components.trend_charts import render_sensor_trends
from dashboard.components.anomaly_heatmap import render_anomaly_heatmap
from dashboard.components.health_leaderboard import render_health_leaderboard
from dashboard.components.alert_summary import render_alert_summary


st.set_page_config(
    page_title="IoT Predictive Maintenance",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global Styles ────────────────────────────────────────────────────────────
st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; }
        .stMetric { background-color: #1e1e2e; border-radius: 8px; padding: 12px; }
        div[data-testid="stMetricValue"] { font-size: 2rem; font-weight: 700; }
        .section-header {
            font-size: 1.1rem;
            font-weight: 600;
            color: #a0a0b0;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("IoT Predictive Maintenance")
    st.caption("Industrial sensor analytics and machine health monitoring.")
    st.divider()

    page = st.radio(
        "Navigation",
        ["Fleet Overview", "Machine Deep Dive", "Anomaly Heatmap"],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("Data source: Microsoft Azure IoT Predictive Maintenance")
    st.caption("Detection method: Rolling Z-Score (window=24h, threshold=3.0)")


# ── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_fleet_summary():
    return get_fleet_summary()


@st.cache_data(ttl=300)
def load_heatmap_data():
    return get_anomaly_heatmap_data()


@st.cache_data(ttl=300)
def load_leaderboard():
    return get_health_leaderboard()


@st.cache_data(ttl=300)
def load_at_risk():
    return get_machines_at_risk()


@st.cache_data(ttl=300)
def load_sensor_trends(machine_id: int):
    return get_sensor_trends(machine_id)


# ── Pages ─────────────────────────────────────────────────────────────────────
if page == "Fleet Overview":
    st.title("Fleet Overview")

    summary = load_fleet_summary()
    render_kpi_cards(summary)

    st.divider()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown('<p class="section-header">Machine Health Leaderboard</p>',
                    unsafe_allow_html=True)
        leaderboard = load_leaderboard()
        render_health_leaderboard(leaderboard)

    with col_right:
        st.markdown('<p class="section-header">Active Alerts</p>',
                    unsafe_allow_html=True)
        at_risk = load_at_risk()
        render_alert_summary(at_risk)


elif page == "Machine Deep Dive":
    st.title("Machine Deep Dive")

    leaderboard = load_leaderboard()
    machine_ids = sorted(leaderboard["machine_id"].tolist())

    selected_machine = st.selectbox(
        "Select Machine",
        options=machine_ids,
        format_func=lambda x: f"Machine {x}",
    )

    if selected_machine:
        machine_row = leaderboard[
            leaderboard["machine_id"] == selected_machine
        ].iloc[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("Model", machine_row["model"])
        col2.metric("Health Score", f"{machine_row['health_score']:.2f}")
        col3.metric("Failure Risk", machine_row["failure_risk"])

        st.divider()
        st.markdown('<p class="section-header">Sensor Trends</p>',
                    unsafe_allow_html=True)

        trend_data = load_sensor_trends(selected_machine)
        render_sensor_trends(trend_data, selected_machine)


elif page == "Anomaly Heatmap":
    st.title("Anomaly Heatmap")
    st.caption(
        "Anomaly frequency per machine per month. "
        "Darker cells indicate higher anomaly concentration."
    )

    heatmap_data = load_heatmap_data()
    render_anomaly_heatmap(heatmap_data)