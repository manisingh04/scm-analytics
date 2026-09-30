-- ====================================================================
-- Signify Luminaire Supply Chain Management (SCM) Database Schema
-- Focus: Multi-Component BOM, Supplier Risk & Inventory Optimization
-- ====================================================================

DROP TABLE IF EXISTS purchase_orders;
DROP TABLE IF EXISTS inventory_levels;
DROP TABLE IF EXISTS parts_bom;
DROP TABLE IF EXISTS suppliers;

-- 1. Suppliers Master Table
CREATE TABLE suppliers (
    supplier_id VARCHAR(20) PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'Mechanical (Die-Cast/Extrusion)', 'Electronics (Drivers/ICs)', 'Optics (Lenses)', 'Fasteners/Hardware'
    country_origin VARCHAR(50) NOT NULL,
    reliability_tier VARCHAR(10) NOT NULL, -- 'Tier 1', 'Tier 2', 'Tier 3'
    contracted_lead_time_days INT NOT NULL,
    payment_terms VARCHAR(20) DEFAULT 'Net 60',
    esg_compliance_score DECIMAL(4, 2) NOT NULL -- Scale 0.00 to 10.00 (Signify Sustainability Standard)
);

-- 2. Parts Bill of Materials (BOM) & Specifications Master
CREATE TABLE parts_bom (
    part_id VARCHAR(20) PRIMARY KEY,
    part_description VARCHAR(150) NOT NULL,
    luminaire_model VARCHAR(50) NOT NULL, -- e.g., 'StreetStar LED 150W', 'Cleanroom Troffer 60W', 'UrbanPark PostTop 40W'
    component_type VARCHAR(50) NOT NULL, -- 'Mechanical', 'Electronic', 'Optics', 'Fastener'
    material VARCHAR(80) NOT NULL, -- 'Die-cast ADC12 Al', 'Extruded 6063-T6', 'FR4 PCB', 'Optical PMMA', 'Stainless Steel 304'
    unit_cost_usd DECIMAL(10, 2) NOT NULL,
    unit_weight_kg DECIMAL(8, 3) NOT NULL,
    unit_volume_cbm DECIMAL(8, 5) NOT NULL, -- Cubic meters (Crucial for freight & warehouse capacity)
    primary_supplier_id VARCHAR(20) NOT NULL,
    minimum_order_qty INT NOT NULL,
    holding_cost_annual_pct DECIMAL(4, 2) DEFAULT 0.22, -- 22% annual inventory carrying cost rate
    FOREIGN KEY (primary_supplier_id) REFERENCES suppliers(supplier_id)
);

-- 3. Historical Purchase Orders & Delivery Performance
CREATE TABLE purchase_orders (
    po_id VARCHAR(25) PRIMARY KEY,
    part_id VARCHAR(20) NOT NULL,
    supplier_id VARCHAR(20) NOT NULL,
    order_date DATE NOT NULL,
    promised_delivery_date DATE NOT NULL,
    actual_delivery_date DATE,
    order_quantity INT NOT NULL,
    received_quantity INT NOT NULL,
    unit_purchase_price DECIMAL(10, 2) NOT NULL,
    freight_mode VARCHAR(20) NOT NULL, -- 'Ocean Freight', 'Road Logistics', 'Air Expedited'
    inspection_defect_rate DECIMAL(5, 4) DEFAULT 0.0000, -- e.g. 0.0125 = 1.25% defective parts
    status VARCHAR(20) NOT NULL, -- 'Delivered', 'Cancelled', 'In Transit', 'Delayed'
    FOREIGN KEY (part_id) REFERENCES parts_bom(part_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- 4. Current Inventory Snapshot & Stock Status
CREATE TABLE inventory_levels (
    snapshot_id INT PRIMARY KEY,
    part_id VARCHAR(20) NOT NULL,
    current_stock_units INT NOT NULL,
    reserved_production_units INT NOT NULL,
    on_order_units INT NOT NULL,
    monthly_consumption_rate INT NOT NULL,
    last_replenishment_date DATE,
    FOREIGN KEY (part_id) REFERENCES parts_bom(part_id)
);

CREATE INDEX idx_po_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_po_part ON purchase_orders(part_id);
CREATE INDEX idx_bom_type ON parts_bom(component_type);
