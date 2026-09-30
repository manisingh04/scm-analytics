# Signify SCM Power BI DAX Measures Reference

This document provides production-ready DAX measures formatted for Power BI Desktop. Import the CSV files from `output/` and `data/` and paste these measures into a dedicated `_Measures` table.

---

### 1. Delivery & Supplier Performance Measures (Table: `purchase_orders`)

```dax
Total Orders = COUNTROWS(purchase_orders)
```

```dax
Delivered Orders = 
CALCULATE(
    COUNTROWS(purchase_orders),
    purchase_orders[status] = "Delivered"
)
```

```dax
On Time Orders = 
CALCULATE(
    COUNTROWS(purchase_orders),
    purchase_orders[status] = "Delivered",
    purchase_orders[actual_delivery_date] <= purchase_orders[promised_delivery_date]
)
```

```dax
In Full Orders = 
CALCULATE(
    COUNTROWS(purchase_orders),
    purchase_orders[status] = "Delivered",
    DIVIDE(purchase_orders[received_quantity], purchase_orders[order_quantity]) >= 0.98
)
```

```dax
OTIF Orders = 
CALCULATE(
    COUNTROWS(purchase_orders),
    purchase_orders[status] = "Delivered",
    purchase_orders[actual_delivery_date] <= purchase_orders[promised_delivery_date],
    DIVIDE(purchase_orders[received_quantity], purchase_orders[order_quantity]) >= 0.98
)
```

```dax
OTIF % = 
DIVIDE([OTIF Orders], [Delivered Orders], 0) * 100
```

```dax
Average Lead Time (Days) = 
AVERAGEX(
    FILTER(purchase_orders, purchase_orders[status] = "Delivered"),
    DATEDIFF(purchase_orders[order_date], purchase_orders[actual_delivery_date], DAY)
)
```

```dax
Average Delivery Delay (Days) = 
AVERAGEX(
    FILTER(purchase_orders, purchase_orders[status] = "Delivered"),
    DATEDIFF(purchase_orders[promised_delivery_date], purchase_orders[actual_delivery_date], DAY)
)
```

```dax
Average Defect Rate % = 
AVERAGE(purchase_orders[inspection_defect_rate]) * 100
```

---

### 2. Inventory Health & Working Capital Measures (Table: `dim_parts_optimized`)

```dax
Current Inventory Valuation = 
SUMX(dim_parts_optimized, dim_parts_optimized[current_stock_units] * dim_parts_optimized[unit_cost_usd])
```

```dax
Target Safety Stock Valuation (95% SL) = 
SUMX(dim_parts_optimized, dim_parts_optimized[safety_stock_95] * dim_parts_optimized[unit_cost_usd])
```

```dax
Target Inventory Valuation = 
SUMX(dim_parts_optimized, dim_parts_optimized[target_stock_value_usd])
```

```dax
Working Capital Capital Trap = 
SUMX(
    FILTER(dim_parts_optimized, dim_parts_optimized[working_capital_delta_usd] > 0),
    dim_parts_optimized[working_capital_delta_usd]
)
```

```dax
Total Warehouse CBM Occupied = 
SUM(dim_parts_optimized[current_stock_cbm])
```

```dax
Stockout Critical SKUs = 
CALCULATE(
    DISTINCTCOUNT(dim_parts_optimized[part_id]),
    dim_parts_optimized[inventory_health_status] = "CRITICAL_STOCKOUT"
)
```

```dax
High Risk Understocked SKUs = 
CALCULATE(
    DISTINCTCOUNT(dim_parts_optimized[part_id]),
    dim_parts_optimized[inventory_health_status] = "HIGH_RISK_UNDERSTOCK"
)
```

```dax
Overstocked SKUs = 
CALCULATE(
    DISTINCTCOUNT(dim_parts_optimized[part_id]),
    dim_parts_optimized[inventory_health_status] = "OVERSTOCKED_CAPITAL_TRAP"
)
```

```dax
Annual Spend Total = 
SUM(dim_parts_optimized[annual_spend_usd])
```

```dax
Inventory Turnover Ratio = 
DIVIDE([Annual Spend Total], [Current Inventory Valuation], 0)
```

---

### 3. Conditional Color Formatting Measures

```dax
OTIF Status Color = 
SWITCH(
    TRUE(),
    [OTIF %] >= 90, "#2ca02c", -- Green
    [OTIF %] >= 80, "#ff7f0e", -- Orange / Warning
    "#d62728"                  -- Red / Critical
)
```

```dax
Inventory Health Color = 
SELECTEDVALUE(
    dim_parts_optimized[inventory_health_status],
    "#7f7f7f"
)
```
