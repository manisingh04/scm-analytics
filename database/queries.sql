-- ====================================================================
-- Signify Luminaire SCM - Advanced SQL Analytics
-- Showcasing: Window Functions, CTEs, Aggregations & Composite KPIs
-- ====================================================================

-- --------------------------------------------------------------------
-- QUERY 1: Supplier On-Time In-Full (OTIF %) & Delivery Reliability Scorecard
-- OTIF is the holy-grail metric in Signify logistics.
-- --------------------------------------------------------------------
WITH DeliveryStats AS (
    SELECT 
        po.supplier_id,
        s.supplier_name,
        s.category,
        s.country_origin,
        COUNT(po.po_id) AS total_orders,
        -- On Time: delivered on or before promised date
        SUM(CASE 
            WHEN julianday(po.actual_delivery_date) <= julianday(po.promised_delivery_date) 
            THEN 1 ELSE 0 
        END) AS on_time_orders,
        -- In Full: received >= 98% of ordered quantity
        SUM(CASE 
            WHEN CAST(po.received_quantity AS FLOAT) / po.order_quantity >= 0.98 
            THEN 1 ELSE 0 
        END) AS in_full_orders,
        -- On-Time AND In-Full
        SUM(CASE 
            WHEN julianday(po.actual_delivery_date) <= julianday(po.promised_delivery_date)
                 AND CAST(po.received_quantity AS FLOAT) / po.order_quantity >= 0.98
            THEN 1 ELSE 0 
        END) AS otif_orders,
        AVG(julianday(po.actual_delivery_date) - julianday(po.promised_delivery_date)) AS avg_delay_days,
        AVG(po.inspection_defect_rate) * 100 AS avg_defect_pct
    FROM purchase_orders po
    JOIN suppliers s ON po.supplier_id = s.supplier_id
    WHERE po.status = 'Delivered'
    GROUP BY po.supplier_id, s.supplier_name, s.category, s.country_origin
)
SELECT 
    supplier_id,
    supplier_name,
    category,
    country_origin,
    total_orders,
    ROUND((CAST(on_time_orders AS FLOAT) / total_orders) * 100, 2) AS on_time_rate_pct,
    ROUND((CAST(in_full_orders AS FLOAT) / total_orders) * 100, 2) AS in_full_rate_pct,
    ROUND((CAST(otif_orders AS FLOAT) / total_orders) * 100, 2) AS otif_score_pct,
    ROUND(avg_delay_days, 1) AS avg_delay_days,
    ROUND(avg_defect_pct, 2) AS avg_defect_pct
FROM DeliveryStats
ORDER BY otif_score_pct ASC;


-- --------------------------------------------------------------------
-- QUERY 2: Window Function - Rolling Lead Time Variability & Moving Average
-- Used to detect supplier delivery deterioration before it causes plant shutdowns.
-- --------------------------------------------------------------------
SELECT 
    po.po_id,
    po.supplier_id,
    s.supplier_name,
    po.part_id,
    b.component_type,
    po.order_date,
    CAST(julianday(po.actual_delivery_date) - julianday(po.order_date) AS INT) AS actual_lead_time_days,
    s.contracted_lead_time_days,
    -- 3-order moving average lead time
    ROUND(AVG(julianday(po.actual_delivery_date) - julianday(po.order_date)) OVER (
        PARTITION BY po.supplier_id, po.part_id 
        ORDER BY po.order_date 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 1) AS rolling_avg_lead_time_3po,
    -- Difference from contract
    ROUND(
        (julianday(po.actual_delivery_date) - julianday(po.order_date)) - s.contracted_lead_time_days, 
        1
    ) AS lead_time_variance_from_contract
FROM purchase_orders po
JOIN suppliers s ON po.supplier_id = s.supplier_id
JOIN parts_bom b ON po.part_id = b.part_id
WHERE po.status = 'Delivered'
ORDER BY po.supplier_id, po.order_date;


-- --------------------------------------------------------------------
-- QUERY 3: Stockout Vulnerability & Days of Coverage (DoC) by Component Type
-- Identifies critical assembly bottlenecks (Die-cast housings vs Drivers).
-- --------------------------------------------------------------------
SELECT 
    b.part_id,
    b.part_description,
    b.luminaire_model,
    b.component_type,
    b.material,
    inv.current_stock_units,
    inv.reserved_production_units,
    (inv.current_stock_units - inv.reserved_production_units) AS net_available_stock,
    inv.monthly_consumption_rate,
    ROUND(CAST(inv.monthly_consumption_rate AS FLOAT) / 30, 2) AS daily_run_rate,
    ROUND(
        CAST(inv.current_stock_units - inv.reserved_production_units AS FLOAT) / 
        (CAST(inv.monthly_consumption_rate AS FLOAT) / 30), 
        1
    ) AS days_of_coverage_doc,
    CASE 
        WHEN (inv.current_stock_units - inv.reserved_production_units) <= 0 THEN 'CRITICAL: Stockout Active'
        WHEN (CAST(inv.current_stock_units - inv.reserved_production_units AS FLOAT) / (CAST(inv.monthly_consumption_rate AS FLOAT) / 30)) < 14 THEN 'HIGH RISK: < 14 Days Cover'
        WHEN (CAST(inv.current_stock_units - inv.reserved_production_units AS FLOAT) / (CAST(inv.monthly_consumption_rate AS FLOAT) / 30)) BETWEEN 14 AND 45 THEN 'HEALTHY: Optimal Buffer'
        ELSE 'OVERSTOCKED: Excess Working Capital'
    END AS inventory_health_status
FROM inventory_levels inv
JOIN parts_bom b ON inv.part_id = b.part_id
ORDER BY days_of_coverage_doc ASC;


-- --------------------------------------------------------------------
-- QUERY 4: Category-Level Cost, CBM (Volume), and Freight Mode Breakdown
-- Highlights why mechanical parts occupy 70%+ of warehouse volume despite moderate unit cost.
-- --------------------------------------------------------------------
SELECT 
    b.component_type,
    COUNT(DISTINCT b.part_id) AS distinct_parts_count,
    ROUND(AVG(b.unit_cost_usd), 2) AS avg_unit_cost,
    ROUND(SUM(b.unit_cost_usd * inv.current_stock_units), 2) AS total_inventory_valuation_usd,
    ROUND(SUM(b.unit_volume_cbm * inv.current_stock_units), 2) AS total_warehouse_volume_cbm,
    ROUND(SUM(b.unit_weight_kg * inv.current_stock_units), 1) AS total_weight_kg,
    ROUND(
        (SUM(b.unit_volume_cbm * inv.current_stock_units) / 
        (SELECT SUM(b2.unit_volume_cbm * inv2.current_stock_units) 
         FROM parts_bom b2 JOIN inventory_levels inv2 ON b2.part_id = inv2.part_id)) * 100, 
        2
    ) AS warehouse_cbm_share_pct
FROM parts_bom b
JOIN inventory_levels inv ON b.part_id = inv.part_id
GROUP BY b.component_type
ORDER BY total_warehouse_volume_cbm DESC;
