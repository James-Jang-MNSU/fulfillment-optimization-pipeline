import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from optimize_logistics import optimize_schedule, WORKERS, DB_PATH

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

def run_optimization(df):
    """
    Gets solution by running optimizer and return results as a clean DataFrame
    """
    print("--- Running Optimization Model ---")

    # 1. Run optimization
    prob, choices, order_ids, worker_names = optimize_schedule(df)
    
    # 2. Extract results: Same logic used in save_results() from optimize_logistics
    results = []
    for i, row in df.iterrows():
        oid = row['order_id']
        assigned_worker = None
        
        for worker in worker_names:
            if choices[oid][worker].varValue > 0.5:
                assigned_worker = worker
                break
        
        # 3. Calculate specific cost for current assignment
        if assigned_worker:
            speed = WORKERS[assigned_worker]["speed"]
            wage  = WORKERS[assigned_worker]["wage"]
            cost  = (row['num_items'] / speed) * wage
            
            results.append({
                "order_id": oid,
                "assigned_worker": assigned_worker,
                "cost": cost,
                "num_items": row['num_items'],
                "total_weight_kg": row['total_weight_kg']
            })
            
    return pd.DataFrame(results)

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

# --- 2. THE DASHBOARD BUILDER ---

def save_dashboard(clean_df, results_df):
    print("--- Generating 6-Panel Dashboard ---")
    
    # 3 Rows, 2 Columns (Size = 16x18 to fit everything)
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    fig.suptitle("Logistics Optimization Report", fontsize=24, weight='bold')
    
    # Row 1: Inputs
    plot_weight_distribution(clean_df, ax=axes[0, 0])
    plot_items_distribution(clean_df, ax=axes[0, 1])
    
    # Row 2: Correlation & Summary
    plot_correlation(clean_df, ax=axes[1, 0])
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
    # 1. Load data
    df = load_data()
    print(f"Raw Data Loaded: {len(df)} records.")
    
    # 2. Run the optimization and catch the results
    results_df = run_optimization(df)
    
    # 3. Output dashboard
    save_dashboard(df, results_df)