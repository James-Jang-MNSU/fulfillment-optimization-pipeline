import sqlite3
import pandas as pd
import os
import visualize_logistics

# --- CONFIGURATION ---
from setup_db import DB_PATH
EXPORT_DIR = "data/bi_exports"
OUTPUT_PATH = os.path.join(EXPORT_DIR, "fulfillment_bi_data.csv")

def export_data():
    """
    Exports clean CSVs for Power BI / Tableau
    Joins the Orders and the Assignments to create a 'Master Table'
    """
    print(f"--- Exporting Data to {EXPORT_DIR} ---")
    
    # 1. Ensure directory exists
    os.makedirs(EXPORT_DIR, exist_ok=True)
    
    # 2. Load Data (Raw Orders)
    conn = sqlite3.connect(DB_PATH)
    orders_df = pd.read_sql_query("SELECT * FROM clean_orders", conn)
    conn.close()
    
    # 3. Load Optimization Results
    results_df = visualize_logistics.load_results()
    
    # 4. Feature Engineering for BI
    results_df['is_safety_violation'] = results_df.apply(
        lambda row: 'Violation' if (row['assigned_worker'] == 'Robot' and row['total_weight_kg'] > 5) else 'Safe', 
        axis=1
    )
    
    # 5. Export to CSV
    results_df.to_csv(OUTPUT_PATH, index=False)

    print(f"Success! Data exported to: {OUTPUT_PATH}")
    print("Columns exported:", list(results_df.columns))

if __name__ == "__main__":
    export_data()