"""
Signify Luminaire SCM - Inventory Optimization & ABC-XYZ Segmentation Engine
Author: GET (Supply Chain Analytics)
Tech Stack: Python, Pandas, NumPy, OpenPyXL, SQLite3
"""

import os
import sqlite3
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "signify_scm.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. Load Data from SQLite
# -----------------------------------------------------------------------------
conn = sqlite3.connect(DB_PATH)

df_suppliers = pd.read_sql_query("SELECT * FROM suppliers", conn)
df_parts = pd.read_sql_query("SELECT * FROM parts_bom", conn)
df_po = pd.read_sql_query("SELECT * FROM purchase_orders", conn)
df_inv = pd.read_sql_query("SELECT * FROM inventory_levels", conn)

conn.close()

# -----------------------------------------------------------------------------
# 2. Calculate Supplier Lead Time & Delivery Statistics
# -----------------------------------------------------------------------------
# Filter delivered orders
df_po_delivered = df_po[df_po["status"] == "Delivered"].copy()
df_po_delivered["order_date"] = pd.to_datetime(df_po_delivered["order_date"])
df_po_delivered["promised_delivery_date"] = pd.to_datetime(df_po_delivered["promised_delivery_date"])
df_po_delivered["actual_delivery_date"] = pd.to_datetime(df_po_delivered["actual_delivery_date"])

# Calculate actual lead time in days
df_po_delivered["actual_lead_time"] = (
    df_po_delivered["actual_delivery_date"] - df_po_delivered["order_date"]
).dt.days

# Calculate delivery delay
df_po_delivered["delay_days"] = (
    df_po_delivered["actual_delivery_date"] - df_po_delivered["promised_delivery_date"]
).dt.days

# OTIF calculation
df_po_delivered["is_on_time"] = df_po_delivered["delay_days"] <= 0
df_po_delivered["is_in_full"] = (df_po_delivered["received_quantity"] / df_po_delivered["order_quantity"]) >= 0.98
df_po_delivered["is_otif"] = df_po_delivered["is_on_time"] & df_po_delivered["is_in_full"]

# Supplier-level scorecard
supplier_scorecard = df_po_delivered.groupby("supplier_id").agg(
    total_orders=("po_id", "count"),
    otif_rate=("is_otif", "mean"),
    on_time_rate=("is_on_time", "mean"),
    in_full_rate=("is_in_full", "mean"),
    avg_actual_lead_time=("actual_lead_time", "mean"),
    std_lead_time=("actual_lead_time", "std"),
    avg_delay_days=("delay_days", "mean"),
    avg_defect_rate=("inspection_defect_rate", "mean")
).reset_index()

supplier_scorecard = supplier_scorecard.merge(df_suppliers, on="supplier_id", how="left")
supplier_scorecard["otif_pct"] = np.round(supplier_scorecard["otif_rate"] * 100, 2)
supplier_scorecard["avg_actual_lead_time"] = np.round(supplier_scorecard["avg_actual_lead_time"], 1)
supplier_scorecard["std_lead_time"] = np.round(supplier_scorecard["std_lead_time"].fillna(2.0), 2)
supplier_scorecard["avg_delay_days"] = np.round(supplier_scorecard["avg_delay_days"], 1)
supplier_scorecard["avg_defect_pct"] = np.round(supplier_scorecard["avg_defect_rate"] * 100, 2)

# Part-level lead time metrics
part_lt_stats = df_po_delivered.groupby("part_id").agg(
    avg_lead_time=("actual_lead_time", "mean"),
    std_lead_time=("actual_lead_time", "std")
).reset_index()
part_lt_stats["avg_lead_time"] = np.round(part_lt_stats["avg_lead_time"], 1)
part_lt_stats["std_lead_time"] = np.round(part_lt_stats["std_lead_time"].fillna(2.0), 2)

# -----------------------------------------------------------------------------
# 3. ABC-XYZ Segmentation Engine
# -----------------------------------------------------------------------------
# Merge parts with inventory snapshot
df_master = df_parts.merge(df_inv, on="part_id", how="left")
df_master = df_master.merge(part_lt_stats, on="part_id", how="left")
df_master["avg_lead_time"] = df_master["avg_lead_time"].fillna(30.0)
df_master["std_lead_time"] = df_master["std_lead_time"].fillna(4.0)

# Annual Demand & Valuation
df_master["annual_demand"] = df_master["monthly_consumption_rate"] * 12
df_master["daily_demand"] = df_master["monthly_consumption_rate"] / 30.0
# Estimate daily demand standard deviation (CV assumption based on component type)
# Mechanical parts have moderate CV, electronics high CV, fasteners low CV
type_cv_map = {"Mechanical": 0.45, "Electronic": 0.85, "Optics": 0.50, "Fastener": 0.25}
df_master["demand_cv"] = df_master["component_type"].map(type_cv_map)
df_master["std_daily_demand"] = df_master["daily_demand"] * df_master["demand_cv"]

df_master["annual_spend_usd"] = df_master["annual_demand"] * df_master["unit_cost_usd"]

# Step 3A: ABC Classification (by Annual Spend)
df_master = df_master.sort_values(by="annual_spend_usd", ascending=False).reset_index(drop=True)
df_master["cum_spend"] = df_master["annual_spend_usd"].cumsum()
total_annual_spend = df_master["annual_spend_usd"].sum()
df_master["cum_spend_pct"] = (df_master["cum_spend"] / total_annual_spend) * 100

def assign_abc(cum_pct):
    if cum_pct <= 80.0:
        return "A"
    elif cum_pct <= 95.0:
        return "B"
    else:
        return "C"

df_master["abc_class"] = df_master["cum_spend_pct"].apply(assign_abc)

# Step 3B: XYZ Classification (by Demand Volatility / CV)
def assign_xyz(cv):
    if cv < 0.40:
        return "X"
    elif cv < 0.70:
        return "Y"
    else:
        return "Z"

df_master["xyz_class"] = df_master["demand_cv"].apply(assign_xyz)
df_master["abc_xyz"] = df_master["abc_class"] + df_master["xyz_class"]

# -----------------------------------------------------------------------------
# 4. Statistical Dynamic Safety Stock & Reorder Point (ROP)
# -----------------------------------------------------------------------------
# Z-Score for target service levels:
# 90% -> 1.28 | 95% -> 1.645 | 98% -> 2.05 | 99% -> 2.33
# We calculate for 95% (Standard) and 98% (High-Reliability for Signify)
Z_95 = 1.645
Z_98 = 2.055

# Dual variability formula: SS = Z * sqrt( L * sigma_d^2 + d^2 * sigma_L^2 )
d = df_master["daily_demand"].values
sig_d = df_master["std_daily_demand"].values
L = df_master["avg_lead_time"].values
sig_L = df_master["std_lead_time"].values

combined_variance = (L * (sig_d ** 2)) + ((d ** 2) * (sig_L ** 2))
df_master["safety_stock_95"] = np.ceil(Z_95 * np.sqrt(combined_variance)).astype(int)
df_master["safety_stock_98"] = np.ceil(Z_98 * np.sqrt(combined_variance)).astype(int)

# Reorder Point (ROP) = (Avg Daily Demand * Avg Lead Time) + Safety Stock
df_master["reorder_point_rop"] = np.ceil((d * L) + df_master["safety_stock_95"]).astype(int)

# Economic Order Quantity (EOQ)
# EOQ = sqrt( (2 * Annual_Demand * Ordering_Cost) / (Holding_Cost_Pct * Unit_Cost) )
ORDERING_COST_S = 120.0 # Standard Signify PO processing cost ($120/order)
holding_cost_annual_per_unit = df_master["unit_cost_usd"] * df_master["holding_cost_annual_pct"]
df_master["eoq_units"] = np.ceil(
    np.sqrt((2 * df_master["annual_demand"] * ORDERING_COST_S) / holding_cost_annual_per_unit)
).astype(int)

# Practical EOQ adjusted for MOQ
df_master["recommended_order_qty"] = np.maximum(df_master["eoq_units"], df_master["minimum_order_qty"])

# -----------------------------------------------------------------------------
# 5. Working Capital & Inventory Health Diagnostics
# -----------------------------------------------------------------------------
df_master["current_stock_value_usd"] = df_master["current_stock_units"] * df_master["unit_cost_usd"]
df_master["current_stock_cbm"] = df_master["current_stock_units"] * df_master["unit_volume_cbm"]

# Optimal cycle stock = EOQ / 2
df_master["target_avg_stock_units"] = df_master["safety_stock_95"] + (df_master["recommended_order_qty"] / 2.0)
df_master["target_stock_value_usd"] = df_master["target_avg_stock_units"] * df_master["unit_cost_usd"]
df_master["working_capital_delta_usd"] = df_master["current_stock_value_usd"] - df_master["target_stock_value_usd"]

# Days of Coverage (DoC)
df_master["net_available_units"] = df_master["current_stock_units"] - df_master["reserved_production_units"]
df_master["days_of_coverage"] = np.round(df_master["net_available_units"] / df_master["daily_demand"], 1)

def assign_health(row):
    if row["net_available_units"] <= 0:
        return "CRITICAL_STOCKOUT"
    elif row["days_of_coverage"] < (row["avg_lead_time"] * 0.4):
        return "HIGH_RISK_UNDERSTOCK"
    elif row["days_of_coverage"] > (row["avg_lead_time"] * 2.5):
        return "OVERSTOCKED_CAPITAL_TRAP"
    else:
        return "OPTIMAL_HEALTHY"

df_master["inventory_health_status"] = df_master.apply(assign_health, axis=1)

# -----------------------------------------------------------------------------
# 6. Service Level Sensitivity Scenarios (90% vs 95% vs 98% vs 99%)
# -----------------------------------------------------------------------------
scenarios = []
z_dict = {"90% SL (Low)": 1.282, "95% SL (Standard)": 1.645, "98% SL (Signify Benchmark)": 2.054, "99% SL (Mission Critical)": 2.326}

for label, z_val in z_dict.items():
    ss_scenario = np.ceil(z_val * np.sqrt(combined_variance))
    val_scenario = (ss_scenario * df_master["unit_cost_usd"]).sum()
    cbm_scenario = (ss_scenario * df_master["unit_volume_cbm"]).sum()
    scenarios.append({
        "Service_Level_Scenario": label,
        "Z_Score": z_val,
        "Total_Safety_Stock_Valuation_USD": round(val_scenario, 2),
        "Total_Safety_Stock_CBM": round(cbm_scenario, 2),
        "Delta_vs_95_Base_USD": round(val_scenario - (df_master["safety_stock_95"] * df_master["unit_cost_usd"]).sum(), 2)
    })

df_scenarios = pd.DataFrame(scenarios)

# -----------------------------------------------------------------------------
# 7. ABC-XYZ Summary Matrix
# -----------------------------------------------------------------------------
abc_xyz_summary = df_master.groupby("abc_xyz").agg(
    part_count=("part_id", "count"),
    total_annual_spend=("annual_spend_usd", "sum"),
    avg_annual_spend=("annual_spend_usd", "mean"),
    total_current_stock_value=("current_stock_value_usd", "sum")
).reset_index()
abc_xyz_summary["spend_share_pct"] = np.round((abc_xyz_summary["total_annual_spend"] / total_annual_spend) * 100, 2)

# -----------------------------------------------------------------------------
# 8. Export to Multi-Tab Excel Workbook & CSVs
# -----------------------------------------------------------------------------
excel_path = os.path.join(OUTPUT_DIR, "Signify_Inventory_Optimization_Model.xlsx")

with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    df_master.to_excel(writer, sheet_name="Master_Optimization", index=False)
    abc_xyz_summary.to_excel(writer, sheet_name="ABC_XYZ_Matrix", index=False)
    supplier_scorecard.to_excel(writer, sheet_name="Supplier_Scorecard", index=False)
    df_scenarios.to_excel(writer, sheet_name="SL_Sensitivity_Scenarios", index=False)

# Export clean CSVs for Power BI ingestion
df_master.to_csv(os.path.join(OUTPUT_DIR, "dim_parts_optimized.csv"), index=False)
supplier_scorecard.to_csv(os.path.join(OUTPUT_DIR, "fact_supplier_scorecard.csv"), index=False)
df_scenarios.to_csv(os.path.join(OUTPUT_DIR, "fact_inventory_scenarios.csv"), index=False)

print(f"Inventory Optimization Engine run completed.")
print(f"Excel Model generated at: {excel_path}")
print(f"Total Portfolio Annual Spend: ${total_annual_spend:,.2f}")
print(f"Current Inventory Valuation: ${df_master['current_stock_value_usd'].sum():,.2f}")
print(f"Target Safety Stock Valuation (95% SL): ${(df_master['safety_stock_95'] * df_master['unit_cost_usd']).sum():,.2f}")
print(f"Stockout risk parts identified: {(df_master['inventory_health_status'] == 'CRITICAL_STOCKOUT').sum()}")
print(f"Overstocked parts identified: {(df_master['inventory_health_status'] == 'OVERSTOCKED_CAPITAL_TRAP').sum()}")
