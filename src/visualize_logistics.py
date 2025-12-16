import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from setup_db import DB_PATH

# --- CONFIGURATION ---
OUTPUT_PATH = "reports/dashboard.png"

# Set the visual style: White grid, readable fonts (affects every plot to be created)
sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 6) # Default plot size (Width, Height)

print("Libraries loaded and configuration set.")

def load_data():
    """
    Gets data from view
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM clean_orders", conn)
    conn.close()
    return df

def load_results():
    """
    Loads the optimization results directly from the SQL 'assignments' table
    """
    print("--- Loading Assignments from SQL ---")
    conn = sqlite3.connect(DB_PATH)
    try:
        results_df = pd.read_sql_query("SELECT * FROM assignments", conn)
        print(f"Loaded {len(results_df)} assignments.")
    except Exception as e:
        print(f"Error loading results: {e}")
        print("Did you run the optimization step? The 'assignments' table might be missing.")
        results_df = pd.DataFrame() # Return empty if failed
    finally:
        conn.close()
        
    return results_df

# --- 1. MODULAR PLOTTING FUNCTIONS ---

def plot_weight_distribution(df, ax):
    sns.histplot(data=df, x="total_weight_kg", kde=True, ax=ax, color="skyblue")
    ax.set_title("Input: Weight Distribution")
    ax.set_xlabel("Weight (kg)")

def plot_items_distribution(df, ax):
    sns.histplot(data=df, x="num_items", kde=True, ax=ax, color="orange")
    ax.set_title("Input: Items per Order")
    ax.set_xlabel("Number of Items")

def plot_correlation(df, ax):
    sns.scatterplot(data=df, x="num_items", y="total_weight_kg", alpha=0.5, color="purple", ax=ax)
    ax.set_title("Input: Correlation (Items vs Weight)")
    ax.set_xlabel("Items")
    ax.set_ylabel("Weight (kg)")

def plot_worker_volume(results_df, ax):
    worker_order = ["Robot", "Senior", "Junior"]
    sns.countplot(data=results_df, x="assigned_worker", order=worker_order, palette="viridis", ax=ax)
    ax.set_title("Output: Order Volume")
    ax.set_ylabel("Count")

def plot_worker_cost(results_df, ax):
    worker_order = ["Robot", "Senior", "Junior"]
    sns.barplot(data=results_df, x="assigned_worker", y="cost", order=worker_order, estimator=sum, errorbar=None, palette="viridis", ax=ax)
    ax.set_title("Output: Total Cost ($)")
    ax.set_ylabel("Cost ($)")

def draw_summary_text(results_df, ax):
    """
    Fills the empty slot with the ROI calculations
    """
    ax.axis('off') # Turn off the grid/box for this slot
    
    # Calculate stats
    summary = results_df.groupby("assigned_worker").agg(
        count=('order_id', 'count'),
        total_cost=('cost', 'sum')
    )
    summary['avg_cost'] = summary['total_cost'] / summary['count']
    
    # Create the text string
    text_str = "EXECUTIVE SUMMARY\n\n"
    for worker in summary.index:
        row = summary.loc[worker]
        text_str += f"{worker}:\n"
        text_str += f"  Orders: {int(row['count'])}\n"
        text_str += f"  Cost:   ${row['total_cost']:,.2f}\n"
        text_str += f"  Avg:    ${row['avg_cost']:.2f}/order\n\n"
        
    ax.text(0.1, 0.5, text_str, fontsize=12, fontfamily='monospace', va='center')

def plot_safety_audit(results_df, ax=None):
    """
    Visualizes the weight range handled by each worker type.
    """
    if ax is None: fig, ax = plt.subplots()
    
    worker_order = ["Robot", "Senior", "Junior"]
    
    # Box Plot: Shows the Median, Quartiles, and Outliers
    sns.boxplot(
        data=results_df, 
        x="assigned_worker", 
        y="total_weight_kg",   # Note: In run_optimization, we mapped 'total_weight_kg' to 'weight'
        order=worker_order, 
        palette="coolwarm", # distinct colors for contrast
        ax=ax
    )
    
    ax.set_title("Safety Audit: Weight Distribution by Worker")
    ax.set_ylabel("Order Weight (kg)")
    ax.set_xlabel("Assigned Worker")
    
    # Add a red reference line at 5kg (The hypothetical "Safe Limit")
    ax.axhline(y=5, color='red', linestyle='--', linewidth=1.5, label='Robot Limit (5kg)')
    ax.legend(loc='upper right')

# --- 2. THE DASHBOARD BUILDER ---

def save_dashboard(clean_df, results_df):
    """
    Generates the final 6-panel dashboard.
    Updated: Replaced Scatter Plot with Safety Audit Box Plot.
    """
    print("--- Generating 6-Panel Dashboard ---")
    
    # 3 Rows, 2 Columns (Size = 16x18 to fit everything)
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    fig.suptitle("Logistics Optimization Report", fontsize=24, weight='bold')
    
    # Row 1: Inputs
    plot_weight_distribution(clean_df, ax=axes[0, 0])
    plot_items_distribution(clean_df, ax=axes[0, 1])
    
    # Row 2: Audit & Summary
    plot_safety_audit(results_df, ax=axes[1, 0])
    draw_summary_text(results_df, ax=axes[1, 1]) # <--- The "Empty" Slot
    
    # Row 3: Outputs
    plot_worker_volume(results_df, ax=axes[2, 0])
    plot_worker_cost(results_df, ax=axes[2, 1])
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.95)
    
    plt.savefig(OUTPUT_PATH, dpi=300)
    plt.show()
    print(f"Dashboard saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    # 1. Load Inputs(initial data)
    df = load_data()
    
    # 2. Load Outputs (for the "After" charts)
    results_df = load_results()
    
    if not results_df.empty:
        # 3. Generate the Dashboard
        save_dashboard(df, results_df)
        
        # 4. Show the Safety Audit (Pop-up for quick check)
        # plot_safety_audit(results_df)
        # plt.show()
    else:
        print("Skipping visualization because results are missing.")