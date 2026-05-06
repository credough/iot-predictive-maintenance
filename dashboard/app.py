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

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 2.5rem;
            padding-right: 2.5rem;
        }

        h1 {
            font-size: 1.6rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-bottom: 0.25rem;
        }

        .section-label {
            font-size: 0.7rem;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.75rem;
            margin-top: 1.5rem;
        }

        .kpi-card {
            background-color: #161622;
            border: 1px solid #2a2a3d;
            border-radius: 10px;
            padding: 1.2rem 1.4rem;
            height: 100%;
        }

        .kpi-label {
            font-size: 0.72rem;
            font-weight: 500;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.4rem;
        }

        .kpi-value {
            font-size: 2rem;
            font-weight: 700;
            color: #f0f0f5;
            line-height: 1.1;
        }

        .kpi-subtext {
            font-size: 0.72rem;
            color: #4b5563;
            margin-top: 0.35rem;
        }

        .alert-high {
            background-color: #2a0f0f;
            border: 1px solid #7f1d1d;
            border-left: 3px solid #c0392b;
            border-radius: 6px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            font-size: 0.82rem;
            color: #fca5a5;
            line-height: 1.5;
        }

        .alert-medium {
            background-color: #1f1a0e;
            border: 1px solid #78350f;
            border-left: 3px solid #e67e22;
            border-radius: 6px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            font-size: 0.82rem;
            color: #fcd34d;
            line-height: 1.5;
        }

        .alert-success {
            background-color: #0f1f14;
            border: 1px solid #14532d;
            border-left: 3px solid #27ae60;
            border-radius: 6px;
            padding: 0.75rem 1rem;
            font-size: 0.82rem;
            color: #86efac;
        }

        div[data-testid="stSelectbox"] label {
            font-size: 0.78rem;
            font-weight: 500;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: 0.07em;
        }

        div[data-testid="stRadio"] label {
            font-size: 0.82rem;
        }

        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
        }

        hr {
            border-color: #1f1f2e;
            margin: 1.25rem 0;
        }
    </style>
""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### IoT Predictive Maintenance")
    st.markdown(
        "<span style='font-size:0.78rem; color:#6b7280;'>"
        "Industrial sensor analytics and machine health monitoring."
        "</span>",
        unsafe_allow_html=True,
    )
    st.divider()

    page = st.radio(
        "Navigation",
        ["Fleet Overview", "Machine Deep Dive", "Anomaly Heatmap"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown(
        "<span style='font-size:0.72rem; color:#4b5563;'>"
        "Source: Microsoft Azure IoT Predictive Maintenance<br><br>"
        "Detection: Rolling Z-Score<br>"
        "Window: 24h — Threshold: 3.0"
        "</span>",
        unsafe_allow_html=True,
    )


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
    st.markdown("<h1>Fleet Overview</h1>", unsafe_allow_html=True)
    st.markdown(
        "<span style='font-size:0.8rem; color:#6b7280;'>"
        "Real-time health and anomaly summary across all monitored machines."
        "</span>",
        unsafe_allow_html=True,
    )
    st.divider()

    summary = load_fleet_summary()
    render_kpi_cards(summary)

    st.divider()

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown(
            '<p class="section-label">Machine Health Leaderboard</p>',
            unsafe_allow_html=True,
        )
        leaderboard = load_leaderboard()
        render_health_leaderboard(leaderboard)

    with col_right:
        st.markdown(
            '<p class="section-label">Active Alerts</p>',
            unsafe_allow_html=True,
        )
        at_risk = load_at_risk()
        render_alert_summary(at_risk)


elif page == "Machine Deep Dive":
    st.markdown("<h1>Machine Deep Dive</h1>", unsafe_allow_html=True)
    st.markdown(
        "<span style='font-size:0.8rem; color:#6b7280;'>"
        "Sensor trends and health metrics for an individual machine."
        "</span>",
        unsafe_allow_html=True,
    )
    st.divider()

    leaderboard = load_leaderboard()
    machine_ids = sorted(leaderboard["machine_id"].tolist())

    col_select, _ = st.columns([2, 3])
    with col_select:
        selected_machine = st.selectbox(
            "MACHINE",
            options=machine_ids,
            format_func=lambda x: f"Machine {x}",
        )

    if selected_machine:
        machine_row = leaderboard[
            leaderboard["machine_id"] == selected_machine
        ].iloc[0]

        st.markdown(
            '<p class="section-label">Machine Summary</p>',
            unsafe_allow_html=True,
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Model", machine_row["model"])
        col2.metric("Age", f"{machine_row['age_years']} years")
        col3.metric("Health Score", f"{machine_row['health_score']:.2f}")
        col4.metric("Failure Risk", machine_row["failure_risk"])

        st.divider()

        st.markdown(
            '<p class="section-label">Sensor Trends</p>',
            unsafe_allow_html=True,
        )

        trend_data = load_sensor_trends(selected_machine)
        render_sensor_trends(trend_data, selected_machine)


elif page == "Anomaly Heatmap":
    st.markdown("<h1>Anomaly Heatmap</h1>", unsafe_allow_html=True)
    st.markdown(
        "<span style='font-size:0.8rem; color:#6b7280;'>"
        "Anomaly frequency per machine per month. "
        "Brighter cells indicate higher anomaly concentration."
        "</span>",
        unsafe_allow_html=True,
    )
    st.divider()

    heatmap_data = load_heatmap_data()
    render_anomaly_heatmap(heatmap_data)