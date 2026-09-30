"""
Signify Luminaire SCM - Exploratory Data Analysis & Visualizations Engine
Author: GET (Supply Chain Analytics)
Tech Stack: Python, Seaborn, Matplotlib, Pandas, NumPy
Generates publication-quality charts for executive reporting and interview presentations.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set visual style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.size"] = 10
plt.rcParams["figure.dpi"] = 300

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FIGURES_DIR = os.path.join(BASE_DIR, "reports", "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

# Load data
df_parts_opt = pd.read_csv(os.path.join(OUTPUT_DIR, "dim_parts_optimized.csv"))
df_po = pd.read_csv(os.path.join(DATA_DIR, "purchase_orders.csv"))
df_suppliers = pd.read_csv(os.path.join(OUTPUT_DIR, "fact_supplier_scorecard.csv"))
df_scenarios = pd.read_csv(os.path.join(OUTPUT_DIR, "fact_inventory_scenarios.csv"))

# Compute PO actual lead times
df_po_delivered = df_po[df_po["status"] == "Delivered"].copy()
df_po_delivered["order_date"] = pd.to_datetime(df_po_delivered["order_date"])
df_po_delivered["actual_delivery_date"] = pd.to_datetime(df_po_delivered["actual_delivery_date"])
df_po_delivered["promised_delivery_date"] = pd.to_datetime(df_po_delivered["promised_delivery_date"])
df_po_delivered["actual_lead_time"] = (df_po_delivered["actual_delivery_date"] - df_po_delivered["order_date"]).dt.days
df_po_delivered["delay_days"] = (df_po_delivered["actual_delivery_date"] - df_po_delivered["promised_delivery_date"]).dt.days

# Merge with part category
df_po_delivered = df_po_delivered.merge(df_parts_opt[["part_id", "component_type"]], on="part_id", how="left")

# -----------------------------------------------------------------------------
# CHART 1: Lead Time Distribution by Component Type (KDE / Histogram)
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5.5))
palette = {"Mechanical": "#2b5c8f", "Electronic": "#d95f02", "Optics": "#7570b3", "Fastener": "#1b9e77"}

for c_type, color in palette.items():
    subset = df_po_delivered[df_po_delivered["component_type"] == c_type]
    sns.kdeplot(
        data=subset["actual_lead_time"],
        label=f"{c_type} (Mean: {subset['actual_lead_time'].mean():.1f}d)",
        color=color,
        linewidth=2.2,
        fill=True,
        alpha=0.18,
        ax=ax
    )

ax.set_title("Figure 1: Supplier Lead Time Volatility by Luminaire Component Group", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Actual Lead Time (Days)", fontsize=11, fontweight="semibold")
ax.set_ylabel("Probability Density", fontsize=11, fontweight="semibold")
ax.legend(title="Component Category", frameon=True, facecolor="white", loc="upper right")
ax.grid(True, linestyle="--", alpha=0.5)

# Annotation for interview context
ax.annotate(
    "Long Right-Tail in Electronics\n(Chip shortages & import lead-time spikes)",
    xy=(75, 0.015), xytext=(85, 0.035),
    arrowprops=dict(facecolor="#d95f02", shrink=0.05, width=1.5, headwidth=7),
    fontsize=9, fontweight="bold", color="#d95f02",
    bbox=dict(boxstyle="round,pad=0.4", fc="#fff2e6", ec="#d95f02")
)

plt.tight_layout()
chart1_path = os.path.join(FIGURES_DIR, "fig1_lead_time_distribution.png")
plt.savefig(chart1_path, dpi=300)
plt.close()
print(f"Saved: {chart1_path}")

# -----------------------------------------------------------------------------
# CHART 2: ABC-XYZ 9-Box Matrix Spend Heatmap
# -----------------------------------------------------------------------------
pivot_spend = df_parts_opt.pivot_table(
    index="abc_class",
    columns="xyz_class",
    values="annual_spend_usd",
    aggfunc="sum",
    fill_value=0
) / 1000.0  # in Thousands USD

# Ensure complete 3x3 index
for r in ["A", "B", "C"]:
    if r not in pivot_spend.index:
        pivot_spend.loc[r] = 0
for c in ["X", "Y", "Z"]:
    if c not in pivot_spend.columns:
        pivot_spend[c] = 0
pivot_spend = pivot_spend.loc[["A", "B", "C"], ["X", "Y", "Z"]]

# Part counts for annotations
pivot_counts = df_parts_opt.pivot_table(
    index="abc_class",
    columns="xyz_class",
    values="part_id",
    aggfunc="count",
    fill_value=0
).loc[["A", "B", "C"], ["X", "Y", "Z"]]

annot_labels = np.empty(pivot_spend.shape, dtype=object)
for i in range(3):
    for j in range(3):
        spend_val = pivot_spend.iloc[i, j]
        count_val = pivot_counts.iloc[i, j]
        annot_labels[i, j] = f"${spend_val:,.0f}k\n({count_val} SKUs)"

fig, ax = plt.subplots(figsize=(8.5, 6))
sns.heatmap(
    pivot_spend,
    annot=annot_labels,
    fmt="",
    cmap="YlGnBu",
    cbar_kws={'label': 'Annual Spend ($ in Thousands)'},
    linewidths=1.5,
    linecolor="white",
    ax=ax
)

ax.set_title("Figure 2: Signify Luminaire ABC-XYZ Segmentation Matrix", fontsize=13, fontweight="bold", pad=14)
ax.set_xlabel("XYZ Class (Demand Volatility: X=Stable, Y=Variable, Z=Erratic)", fontsize=11, fontweight="semibold")
ax.set_ylabel("ABC Class (Spend Impact: A=80%, B=15%, C=5%)", fontsize=11, fontweight="semibold")

plt.tight_layout()
chart2_path = os.path.join(FIGURES_DIR, "fig2_abc_xyz_matrix.png")
plt.savefig(chart2_path, dpi=300)
plt.close()
print(f"Saved: {chart2_path}")

# -----------------------------------------------------------------------------
# CHART 3: Supplier Risk Scorecard (OTIF % vs. Average Delay)
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6))

tier_palette = {"Tier 1": "#2ca02c", "Tier 2": "#1f77b4", "Tier 3": "#d62728"}

scatter = sns.scatterplot(
    data=df_suppliers,
    x="avg_delay_days",
    y="otif_pct",
    hue="reliability_tier",
    size="total_orders",
    sizes=(80, 450),
    palette=tier_palette,
    alpha=0.85,
    edgecolor="black",
    linewidth=1.2,
    ax=ax
)

# Reference benchmark lines
ax.axhline(90, color="gray", linestyle="--", linewidth=1.2, label="Signify Target OTIF (90%)")
ax.axvline(0, color="red", linestyle=":", linewidth=1.2, label="Zero Delay Threshold")

# Annotate suppliers
for _, row in df_suppliers.iterrows():
    ax.text(
        row["avg_delay_days"] + 0.15,
        row["otif_pct"] - 0.4,
        row["supplier_name"].split(" ")[0] + f" ({row['category'][:3]})",
        fontsize=8.5,
        fontweight="semibold"
    )

ax.set_title("Figure 3: Supplier Reliability Matrix — On-Time In-Full (OTIF %) vs Delivery Delay", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Average Delivery Delay (Days)", fontsize=11, fontweight="semibold")
ax.set_ylabel("OTIF % (On-Time In-Full)", fontsize=11, fontweight="semibold")
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0)
ax.grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
chart3_path = os.path.join(FIGURES_DIR, "fig3_supplier_otif_risk.png")
plt.savefig(chart3_path, dpi=300)
plt.close()
print(f"Saved: {chart3_path}")

# -----------------------------------------------------------------------------
# CHART 4: Mechanical vs Electronics — Capital Value vs. Physical CBM Share
# -----------------------------------------------------------------------------
cat_agg = df_parts_opt.groupby("component_type").agg(
    total_val=("current_stock_value_usd", "sum"),
    total_cbm=("current_stock_cbm", "sum")
).reset_index()

cat_agg["val_share"] = (cat_agg["total_val"] / cat_agg["total_val"].sum()) * 100
cat_agg["cbm_share"] = (cat_agg["total_cbm"] / cat_agg["total_cbm"].sum()) * 100

x = np.arange(len(cat_agg))
width = 0.35

fig, ax = plt.subplots(figsize=(9, 5.5))
bar1 = ax.bar(x - width/2, cat_agg["val_share"], width, label="Dollar Valuation Share (%)", color="#1f77b4")
bar2 = ax.bar(x + width/2, cat_agg["cbm_share"], width, label="Physical Warehouse Volume Share (CBM %)", color="#ff7f0e")

ax.set_title("Figure 4: The Mechanical Paradox — Inventory Dollar Value vs. Physical Warehouse Volume (CBM)", fontsize=12, fontweight="bold", pad=12)
ax.set_xticks(x)
ax.set_xticklabels(cat_agg["component_type"], fontweight="semibold")
ax.set_ylabel("Share of Total (%)", fontsize=11, fontweight="semibold")
ax.legend(frameon=True, facecolor="white")
ax.grid(True, axis="y", linestyle="--", alpha=0.5)

# Add values above bars
for bar in bar1:
    h = bar.get_height()
    ax.annotate(f"{h:.1f}%", (bar.get_x() + bar.get_width()/2, h), textcoords="offset points", xytext=(0, 3), ha="center", fontsize=8.5, fontweight="bold")
for bar in bar2:
    h = bar.get_height()
    ax.annotate(f"{h:.1f}%", (bar.get_x() + bar.get_width()/2, h), textcoords="offset points", xytext=(0, 3), ha="center", fontsize=8.5, fontweight="bold", color="#d95f02")

plt.tight_layout()
chart4_path = os.path.join(FIGURES_DIR, "fig4_cbm_vs_value_share.png")
plt.savefig(chart4_path, dpi=300)
plt.close()
print(f"Saved: {chart4_path}")

# -----------------------------------------------------------------------------
# CHART 5: Service Level Sensitivity Curve (Hockey-stick inventory carrying cost)
# -----------------------------------------------------------------------------
fig, ax1 = plt.subplots(figsize=(8.5, 5))

sl_labels = ["90%", "95%", "98%", "99%"]
y_vals = df_scenarios["Total_Safety_Stock_Valuation_USD"] / 1000.0 # $k

ax1.plot(sl_labels, y_vals, marker="o", markersize=8, color="#2b5c8f", linewidth=2.5, label="Required Safety Stock ($k)")
ax1.set_title("Figure 5: Service Level Sensitivity — Diminishing Returns on Working Capital", fontsize=12, fontweight="bold", pad=12)
ax1.set_xlabel("Target Customer Service Level Target (%)", fontsize=11, fontweight="semibold")
ax1.set_ylabel("Safety Stock Capital Required ($ in Thousands)", fontsize=11, fontweight="semibold", color="#2b5c8f")
ax1.grid(True, linestyle="--", alpha=0.5)

for i, txt in enumerate(y_vals):
    ax1.annotate(f"${txt:,.1f}k", (sl_labels[i], txt + 4), ha="center", fontweight="bold", fontsize=9.5)

plt.tight_layout()
chart5_path = os.path.join(FIGURES_DIR, "fig5_service_level_sensitivity.png")
plt.savefig(chart5_path, dpi=300)
plt.close()
print(f"Saved: {chart5_path}")

print("All Seaborn exploratory charts successfully generated in reports/figures/.")
