import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.schema_warehouse import create_warehouse_tables
from etl.transform import run_etl

if __name__ == "__main__":
    create_warehouse_tables()
    run_etl()