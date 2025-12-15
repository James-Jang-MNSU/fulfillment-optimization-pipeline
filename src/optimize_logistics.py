import sqlite3
import pandas as pd
import pulp
from pathlib import Path

# --- CONFIGURATION ---
DB_PATH = Path("data/processed/fulfillment.db")

# Time Horizon: 1 Day (8 Hour Shift)
# Speed = Items per Hour
# Wage = Dollars per Hour
# Max Hours = Hours per Shift 

WORKERS = {
    # Junior worker: Slow and expensive per item, but infinite availability
    "Junior": {
        "speed": 25,
        "wage": 16.0,
        "max_hours": 9999 # Effectively Infinite (Can hire temp agencies)
    },
    
    # Senior worker: Good value, but limited bodies (2 Seniors on shift)
    "Senior": {
        "speed": 65,
        "wage": 28.0,
        "max_hours": 16 # 2 seniors * 8 hours
    },
    
    # Robot: Cheap to run, super fast, but strict limit (1 Robot)
    # Only OpEx (Electricity), not CapEx (Purchase price is sunk cost)
    "Robot": {
        "speed": 140,
        "wage": 5.0,   # Just electricity/maintenence
        "max_hours": 8 # 1 Robot * 8 hours
    }
}

def get_order_data():
    """
    Fetches the clean orders and calculates the total workload.
    """
    with sqlite3.connect(DB_PATH) as conn:
        # Read from the view
        df = pd.read_sql("SELECT * FROM clean_orders", conn)
    
    total_orders = len(df)
    total_items = df['num_items'].sum()
    
    print(f"Orders to Process: {total_orders}")
    print(f"Total Items:       {total_items}")
    
    return df

def optimize_schedule(df):
    print("\n--- OPTIMIZING ---")

    # 1. Initialize model: Use LpMinimize
    prob = pulp.LpProblem("Fulfillment_Cost_Minimization", pulp.LpMinimize)
    
    # 2. Create decision variables: Use classmethod .dicts() to create decision variables in 2 dimension
    order_ids = df['order_id'].tolist()
    worker_names = list(WORKERS.keys())
    choices = pulp.LpVariable.dicts("Assign", (order_ids, worker_names), 0, 1, cat=pulp.LpBinary)

    print(f"Created {len(order_ids) * len(worker_names)} decision variables.")
    
    # 3. Define the objective variable: Cost = (Num Items / Speed) * Wage
    costs = []

    # Nested loop to calculate costs for each combination of order x worker
    for i, row in df.iterrows():
        oid = row['order_id']
        items = row['num_items']
        
        for worker in worker_names:
            # Time = Items / Speed
            speed = WORKERS[worker]["speed"]
            wage  = WORKERS[worker]["wage"]
            hours_needed = items / speed
            cost_to_pack = hours_needed * wage

            variable = choices[oid][worker]
            costs.append(cost_to_pack * variable)
    # Objective Variable
    total_costs = pulp.lpSum(costs)
            
    # Add the objective variable to the problem
    prob += total_costs
    
    print("Objective Function (Cost Minimization) added.")

    # 4. Add Constraints
    
    # Constraint 1: Every order must be assigned to ONE worker
    for oid in order_ids:
        worker_switches = [choices[oid][w] for w in worker_names]

        # Number of workers of each order = sum of worker switches
        prob += pulp.lpSum(worker_switches) == 1, f"Single_Ownership_Order{oid}"
        
    print("Constraint added: Each order assigned to exactly one worker.")
    
    # Constraint 2: Daily Capacity Limits
    for worker in worker_names:
        limit = WORKERS[worker]["max_hours"]
        speed = WORKERS[worker]["speed"]
        
        # Calculate total hours assigned to current worker
        worked_hours = []   # List of worked hours by worker
        for i, row in df.iterrows():
            oid = row['order_id']
            items = row['num_items']
            variable = choices[oid][worker]
            worked_hours.append((items / speed) * variable)
        
        total_worked_hours = pulp.lpSum(worked_hours)
        prob += total_worked_hours <= limit, f"Max_Capacity_{worker}"
        
    print("Constraint added: Shift capacity limits active.")

    # 5. Solve the Problem
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    # Results
    # "Optimal" means it found the absolute best solution
    # "Infeasible" means the problem is impossible
    print(f"Status: {pulp.LpStatus[prob.status]}")
    
    return prob, choices, order_ids, worker_names

def save_results(df, choices, workers):
    print("\n--- RESULTS ---")
    results = []
    
    # Loop through every order
    for i, row in df.iterrows():
        oid = row['order_id']
        
        # Check which worker was assigned
        assigned_worker = None
        for worker in workers:
            if choices[oid][worker].varValue > 0.5:
                assigned_worker = worker
                break
        
        # Calculate the final stats for this assignment
        items = row['num_items']
        speed = WORKERS[assigned_worker]["speed"]
        wage  = WORKERS[assigned_worker]["wage"]
        cost  = (items / speed) * wage

        results.append({
            "order_id": oid,
            "assigned_worker": assigned_worker,
            "cost": cost
        })

    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Print the summary
    print("Workforce Distribution:")
    print(results_df['assigned_worker'].value_counts())
    
    print(f"\nTotal Cost of Operation: ${results_df['cost'].sum():,.2f}")
    
    return results_df
    
if __name__ == "__main__":
    orders_df = get_order_data()
    prob, choices, orders, workers = optimize_schedule(orders_df)
    
    # Only save results when solution exists
    if pulp.LpStatus[prob.status] == "Optimal":
        results_df = save_results(orders_df, choices, workers)
    