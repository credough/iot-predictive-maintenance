import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import test_connection

if __name__ == "__main__":
    test_connection()