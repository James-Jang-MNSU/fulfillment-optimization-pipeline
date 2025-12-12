import sqlite3
import pandas as pd
from pathlib import Path

# --- CONFIGURATION ---
# We point to the processed database, not the raw CSV
DB_PATH = Path("data/processed/fulfillment.db")

def run_query(query, db_path=DB_PATH):
    """
    Runs SQL queries and return a Pandas DataFrame
    Handles the repeated process of connection and closing
    """
    # 'with' statement to open/close automatically
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql(query, conn)

def analyze_corruption():
    """
    Runs SQL queries to quantify data quality issues
    """
    print("--- DATA QUALITY REPORT ---\n")
    
    # QUERY 1: Find Missing Data
    # We count how many rows have no item count
    query_nulls = """
    SELECT COUNT(*) as missing_count
    FROM orders
    WHERE num_items IS NULL
    """
    
    df_nulls = run_query(query_nulls)
    print("1. Checking for Missing Item Counts (NULLs):")
    print(df_nulls)
    print("\n")

    # QUERY 2: Find Logic Errors
    # We look for rows where the weight is less than 0
    query_negatives = """
    SELECT COUNT(*) as negative_count
    FROM orders
    WHERE total_weight_kg < 0
    """
    
    df_negs = run_query(query_negatives)  
    print("2. Checking for Negative Weights:")
    print(df_negs)

if __name__ == "__main__":
    analyze_corruption()