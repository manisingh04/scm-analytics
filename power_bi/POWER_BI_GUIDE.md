# Power BI Dashboard Setup & Visual Guide

Follow this guide to build the **Signify SCM Control Tower** in Power BI Desktop using the generated data.

---

### 1. Data Ingestion (Import Mode)
1. Open **Power BI Desktop**.
2. Click **Get Data** -> **Text/CSV**.
3. Load the following files from your project directory:
   * `output/dim_parts_optimized.csv` (Primary Dimension Table)
   * `data/purchase_orders.csv` (Fact Table 1: Deliveries & Orders)
   * `output/fact_supplier_scorecard.csv` (Dimension / Aggregated Scorecard)
   * `output/fact_inventory_scenarios.csv` (Sensitivity Fact Table)

---

### 2. Star Schema Relationship Modeling
In the **Model View**, establish the following 1-to-Many (`1:*`) relationships:
* `dim_parts_optimized[part_id]` ──(1:*)──► `purchase_orders[part_id]`
* `fact_supplier_scorecard[supplier_id]` ──(1:*)──► `purchase_orders[supplier_id]`
* `fact_supplier_scorecard[supplier_id]` ──(1:*)──► `dim_parts_optimized[primary_supplier_id]`

*(Ensure cross-filter direction is set to **Single**).*

---

### 3. Recommended 3-Page Dashboard Layout

#### 📄 Page 1: Supply Chain Control Tower (Executive Overview)
* **Top KPI Ribbon:**
  * Card 1: `OTIF %` (Conditional formatting: Green >= 90%, Orange >= 80%, Red < 80%)
  * Card 2: `Current Inventory Valuation` (e.g. \$540.7K)
  * Card 3: `Inventory Turnover Ratio`
  * Card 4: `Stockout Critical SKUs`
  * Card 5: `Total Warehouse CBM`
* **Visual 1 (Donut Chart):** Inventory Valuation by Component Type (Mechanical vs Electronic vs Optics vs Fastener).
* **Visual 2 (Clustered Column Chart):** Top 10 SKUs by Annual Spend vs. Current Stock Units.
* **Visual 3 (Table with Status Badges):** High-risk parts needing immediate replenishment (Filtered where `inventory_health_status != "OPTIMAL_HEALTHY"`).

#### 📄 Page 2: ABC-XYZ Inventory Rationalization Matrix
* **Visual 1 (Matrix Visual):**
  * Rows: `abc_class` (A, B, C)
  * Columns: `xyz_class` (X, Y, Z)
  * Values: `Total Current Stock Value`, `Part Count`
* **Visual 2 (Scatter Plot - Rationalization Opportunity):**
  * X-axis: `Annual Spend ($)`
  * Y-axis: `Days of Coverage (DoC)`
  * Legend: `abc_xyz` class
  * Tooltips: `part_description`, `luminaire_model`
* **Slicers:** Slicer for `luminaire_model` (e.g., StreetStar, CleanSky, HighBay) and `component_type`.

#### 📄 Page 3: Supplier Lead Time & Risk Scorecard
* **Visual 1 (Scatter Plot):**
  * X-axis: `avg_delay_days`
  * Y-axis: `otif_pct`
  * Bubble Size: `total_orders`
  * Legend: `reliability_tier`
* **Visual 2 (Horizontal Bar Chart):** Average Actual Lead Time by Supplier compared to Contracted Lead Time.
* **Visual 3 (Table):** Supplier Master details including `country_origin`, `esg_compliance_score`, `avg_defect_pct`, and `payment_terms`.
