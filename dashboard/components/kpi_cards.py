import streamlit as st


def render_kpi_cards(summary: dict) -> None:
    col1, col2, col3, col4 = st.columns(4)

    cards = [
        {
            "label": "Machines Monitored",
            "value": f"{summary['total_machines']:,}",
            "subtext": "Active in fleet",
            "col": col1,
        },
        {
            "label": "Anomalies Detected",
            "value": f"{summary['total_anomalies']:,}",
            "subtext": "Across all sensors",
            "col": col2,
        },
        {
            "label": "Failure Events",
            "value": f"{summary['total_failures']:,}",
            "subtext": "Recorded failures",
            "col": col3,
        },
        {
            "label": "Machines with Recent Anomalies",
            "value": f"{summary['machines_active_anomalies']:,}",
            "subtext": f"of {summary['total_machines']} machines in last 7 days",
            "col": col4,
        },
    ]

    for card in cards:
        with card["col"]:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{card['label']}</div>
                    <div class="kpi-value">{card['value']}</div>
                    <div class="kpi-subtext">{card['subtext']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )