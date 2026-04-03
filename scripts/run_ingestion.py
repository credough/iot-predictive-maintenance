import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.schema_staging import create_staging_tables
from ingestion.loader import run_ingestion

if __name__ == "__main__":
    create_staging_tables()
    run_ingestion()