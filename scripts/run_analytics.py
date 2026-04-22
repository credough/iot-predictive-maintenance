import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.health_scores import (
    compute_machine_health_scores,
    compute_failure_risk,
    get_machines_at_risk,
)
from analytics.queries import get_fleet_summary, get_health_leaderboard


def main():
    print("=== Fleet Summary ===")
    summary = get_fleet_summary()
    for k, v in summary.items():
        print(f"  {k}: {v}")

    print("\n=== Machine Health Scores (Bottom 10) ===")
    health_df = compute_machine_health_scores()
    print(
        health_df.sort_values("health_score")
        .head(10)
        .to_string(index=False)
    )

    print("\n=== Machines at Risk ===")
    at_risk = get_machines_at_risk()
    if at_risk.empty:
        print("  No machines currently at elevated risk.")
    else:
        print(at_risk.to_string(index=False))

    print("\n=== Health Leaderboard (Top 10 at Risk) ===")
    leaderboard = get_health_leaderboard()
    print(leaderboard.head(10).to_string(index=False))


if __name__ == "__main__":
    main()