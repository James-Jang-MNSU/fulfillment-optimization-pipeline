import sqlite3
from pathlib import Path

# --- CONFIGURATION ---
DB_PATH = Path("data/processed/fulfillment.db")

def create_clean_view():
    """
    Creates a SQL View that cleans the data
    """

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print("Connecting to database...")

    # For idempotency
    cursor.execute("DROP VIEW IF EXISTS clean_orders")
    
    # 1. Define the Cleaning Logic (The View)
    # Assumption 1: negative weights are sign-entry errors
    #    (e.g. scanner glitch), not returns or calibration errors
    # Assumption 2: NULLs are invalid orders   
    create_view_sql = """
    CREATE VIEW clean_orders AS
    SELECT 
        order_id,
        num_items,
        CASE 
            WHEN total_weight_kg < 0 THEN ABS(total_weight_kg) 
            ELSE total_weight_kg 
        END as total_weight_kg
    FROM orders
    WHERE num_items IS NOT NULL 
    """
    
    # 2. Execute and Save
    cursor.execute(create_view_sql)
    conn.commit() # Commits the schema change to the database file
    
    print("View 'clean_orders' created successfully.")

    # 3. Validation
    # If the view works, should see fewer rows than the original 1000
    count = cursor.execute("SELECT COUNT(*) FROM clean_orders").fetchone()[0]
    
    print(f"Clean rows available: {count}")
    print(f"Dropped {1000 - count} rows due to missing data.")
    
    conn.close()

if __name__ == "__main__":
    create_clean_view()
