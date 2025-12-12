import sqlite3
import pandas as pd
from pathlib import Path

# --- CONFIGURATION ---
# Define data paths
DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "raw" / "orders.csv"
DB_PATH = DATA_DIR / "processed" / "fulfillment.db"

# Ensure the processed directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_db():
    """
    Initializes the SQLite database and loads the raw data
    """
    print(f"Connecting to database at {DB_PATH}...")

    # 1. Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 2. Read the CSV
    print("Loading raw CSV data...")
    df = pd.read_csv(CSV_PATH)

    # 3. Write to SQL
    # if_exists='replace': Drops the table if it exists and creates a new one.
    # index=False: Don't save the Pandas row numbers as a column.
    df.to_sql('orders', conn, if_exists='replace', index=False)
    
    print(f"SUCCESS: Loaded {len(df)} rows into table 'orders'.")

    # 4. Validation
    print("-" * 30)
    cursor.execute("SELECT * FROM orders LIMIT 5")
    rows = cursor.fetchall()
    print(rows)
    print("Sample Data from SQL:")
    sample = pd.read_sql("SELECT * FROM orders LIMIT 5", conn)
    print(sample)
    
    conn.close()

if __name__ == "__main__":
    init_db()