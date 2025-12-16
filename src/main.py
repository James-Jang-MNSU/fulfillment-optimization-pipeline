import logging
import sys
import subprocess
import pandas as pd

import optimize_logistics
import visualize_logistics
import export_for_bi

# --- CONFIGURATION ---
# Configure a "Logger" to format the console output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"), # Saves logs to a file
        logging.StreamHandler(sys.stdout)    # Prints to console
    ]
)
logger = logging.getLogger()

def run_script(script_name):
    """
    Helper function to run standalone scripts using the terminal command 'python script_name'
    """
    logger.info(f"Running Script: {script_name}...")
    try:
        # This runs the command "python src/script_name.py"
        subprocess.run([sys.executable, f"src/{script_name}.py"], check=True)
        logger.info(f"{script_name} completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"{script_name} FAILED. Stopping pipeline.")
        sys.exit(1) # Stop the program immediately

def main():
    logger.info("==========================================")
    logger.info("   AUTOMATED FULFILLMENT CENTER PIPELINE  ")
    logger.info("==========================================")

    # --- PHASE 1: INFRASTRUCTURE & INPUT ---
    # We use run_script for these because they are likely standalone scripts
    # that perform actions (create tables, insert data) rather than returning values.
    
    run_script("generate_data") 
    run_script("setup_db")
    run_script("analyze_corruption")

    # --- PHASE 2: PROCESSING (ETL & OPTIMIZATION) ---
    
    run_script("clean_data") # Creates the clean_orders view
    
    # For Optimization, we use the nice modular functions we built!
    logger.info("Starting Optimization Engine...")
    
    # 1. Load Data
    conn = visualize_logistics.sqlite3.connect(visualize_logistics.DB_PATH)
    clean_df = pd.read_sql_query("SELECT * FROM clean_orders", conn)
    conn.close()
    
    # 2. Run Solver
    prob, choices, orders, workers = optimize_logistics.solve_model(clean_df)
    
    # 3. Save Results (The Persistence)
    optimize_logistics.save_results(clean_df, choices, workers)
    logger.info("✅ Optimization complete.")

    # --- PHASE 3: OUTPUT (VISUALIZATION & BI) ---
    
    logger.info("Generating Reports...")
    
    # Generate Dashboard
    results_df = visualize_logistics.load_results()
    visualize_logistics.save_dashboard(clean_df, results_df)
    
    # Export for BI
    export_for_bi.export_data()
    
    logger.info("==========================================")
    logger.info("         PIPELINE FINISHED SUCCESS        ")
    logger.info("==========================================")

if __name__ == "__main__":
    main()