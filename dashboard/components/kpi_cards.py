import streamlit as st


def render_kpi_cards(summary: dict) -> None:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Machines Monitored",
            value=summary["total_machines"],
        )
    with col2:
        st.metric(
            label="Total Anomalies Detected",
            value=f"{summary['total_anomalies']:,}",
        )
    with col3:
        st.metric(
            label="Total Failure Events",
            value=f"{summary['total_failures']:,}",
        )
    with col4:
        st.metric(
            label="Machines with Recent Anomalies",
            value=summary["machines_active_anomalies"],
            delta=f"{summary['machines_active_anomalies']} of {summary['total_machines']} machines",
            delta_color="inverse",
        )