import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.anomaly_detection import run_anomaly_detection

if __name__ == "__main__":
    run_anomaly_detection()