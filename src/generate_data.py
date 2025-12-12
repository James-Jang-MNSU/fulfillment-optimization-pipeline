import pandas as pd
import numpy as np
import os
from pathlib import Path

# --- CONFIGURATION ---
# Set seed for reproducibilitiy
np.random.seed(42) 

# Magic Numbers
NUM_ORDERS = 1000
PROB_DIRTY_DATA = 0.05  # 5% chance of data corruption
OUTPUT_PATH = Path("data/raw")

# Creates folder if it doesn't exist yet
os.makedirs(OUTPUT_PATH, exist_ok=True)


def generate_orders(n=NUM_ORDERS):
    """
    Generates synthetic, clean order data.
    """
    print(f"Generating {n} orders...")
    
    # Keys are column names and values are arrays of data
    data = {
        # Create IDs
        'order_id': np.arange(1, n + 1),
        
        # Using Poisson distribution: Mean = 3
        'num_items': np.random.poisson(lam=3, size=n), 
        
        # Using Normal distribution: Mean = 5kg, StdDev = 2kg
        'total_weight_kg': np.random.normal(loc=5, scale=2, size=n)
    }
    
    df = pd.DataFrame(data)
    
    # A Normal distribution can give negative numbers. We "clip" them to be at least 0.1.
    df['total_weight_kg'] = df['total_weight_kg'].clip(lower=0.1)
    df['num_items'] = df['num_items'].clip(lower=1)
    
    return df

def corrupt_data(df, corruption_rate=PROB_DIRTY_DATA):
    """
    Injects specific data quality issues:
    1. NULL values in 'num_items' (simulating sensor miss)
    2. Negative values in 'total_weight_kg' (simulating calculation error)
    """
    # Copy data 
    dirty_df = df.copy()
    
    n_rows = len(dirty_df)
    n_corrupt = int(n_rows * corruption_rate)
    
    print(f"Injecting chaos into {n_corrupt} rows...")
    
    # 1. Create NULLs
    # Randomly pick 'n_corrupt' row indices
    nan_indices = np.random.choice(dirty_df.index, size=n_corrupt, replace=False)
    # Go to those rows, and the 'num_items' column, and set them to Not-A-Number (NaN)
    dirty_df.loc[nan_indices, 'num_items'] = np.nan
    
    # 2. Create Negatives
    # Pick a DIFFERENT set of random rows
    neg_indices = np.random.choice(dirty_df.index, size=n_corrupt, replace=False)
    # Multiply weight by -1 to flip the sign
    dirty_df.loc[neg_indices, 'total_weight_kg'] *= -1
    
    return dirty_df

if __name__ == "__main__":
    # 1. Generate clean data
    orders_df = generate_orders(NUM_ORDERS)
    
    # 2. Corrupt generated data
    dirty_orders = corrupt_data(orders_df)
    
    # 3. Save data
    # Join paths
    save_path = OUTPUT_PATH / "orders.csv"
    dirty_orders.to_csv(save_path, index=False)
    
    # 4. Validation
    print(f"SUCCESS: Generated dirty data at {save_path}")
    print("First 5 rows:")
    print(orders_df.head())
    print("-" * 30)
    print("\nMissing Values Count:")
    print(dirty_orders.isnull().sum())
    print("-" * 30)
    print("Negative Weights Count:")
    print((dirty_orders['total_weight_kg'] < 0).sum()) # Create a boolean mask (True for negatives) and sum it up
    print("-" * 30)