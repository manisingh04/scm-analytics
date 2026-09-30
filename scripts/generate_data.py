"""
Signify Luminaire SCM - Synthetic Realistic Data Generator
Generates realistic lighting BOM, supplier performance, purchase orders,
and inventory levels. Creates both SQLite database and CSV files.
"""

import os
import sqlite3
import random
import datetime
import pandas as pd
import numpy as np

# Set seed for reproducible realistic data
random.seed(42)
np.random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(BASE_DIR, "database", "signify_scm.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# -----------------------------------------------------------------------------
# 1. Suppliers Definition
# -----------------------------------------------------------------------------
suppliers_data = [
    # Mechanical (Die-Casting & Sheet Metal)
    ("SUP-MEC-01", "Precision Castings Ltd (Pune)", "Mechanical", "India", "Tier 1", 35, "Net 60", 8.9),
    ("SUP-MEC-02", "Delta Die-Castings (Suzhou)", "Mechanical", "China", "Tier 2", 50, "Net 45", 7.4),
    ("SUP-MEC-03", "Apex Extrusions & Metals (Gujarat)", "Mechanical", "India", "Tier 1", 28, "Net 60", 9.1),
    ("SUP-MEC-04", "Vietnam Alloy Tech (Hai Phong)", "Mechanical", "Vietnam", "Tier 2", 42, "Net 60", 8.2),

    # Electronics (Drivers, LED Boards, Sensors)
    ("SUP-ELE-01", "OptoDrive Semiconductors (Hsinchu)", "Electronic", "Taiwan", "Tier 1", 65, "Net 30", 9.4),
    ("SUP-ELE-02", "EuroPower Driver Systems (Eindhoven)", "Electronic", "Netherlands", "Tier 1", 45, "Net 60", 9.7),
    ("SUP-ELE-03", "Bharat Micro-Electronics (Bangalore)", "Electronic", "India", "Tier 2", 30, "Net 45", 8.0),
    ("SUP-ELE-04", "Shenzhen SolidLED Components", "Electronic", "China", "Tier 3", 60, "Net 30", 6.8),

    # Optics (Lenses, Diffusers, Covers)
    ("SUP-OPT-01", "PolymerOptics Global (Munich)", "Optics", "Germany", "Tier 1", 40, "Net 60", 9.5),
    ("SUP-OPT-02", "ClearVision Optical Molding (Dongguan)", "Optics", "China", "Tier 2", 35, "Net 45", 7.9),
    ("SUP-OPT-03", "IndoOptics PolyPlast (Chennai)", "Optics", "India", "Tier 1", 21, "Net 60", 8.7),

    # Fasteners & Hardware
    ("SUP-FAS-01", "Unifast Hardware & Gaskets (Faridabad)", "Fastener", "India", "Tier 1", 14, "Net 30", 9.2),
]

df_suppliers = pd.DataFrame(suppliers_data, columns=[
    "supplier_id", "supplier_name", "category", "country_origin",
    "reliability_tier", "contracted_lead_time_days", "payment_terms", "esg_compliance_score"
])

# -----------------------------------------------------------------------------
# 2. Parts Bill of Materials (BOM)
# -----------------------------------------------------------------------------
models = [
    "StreetStar LED 150W",
    "CleanSky Troffer 45W",
    "HighBay Pro Industrial 200W",
    "UrbanPark Architectural 60W"
]

parts_data = []

# Generate 50 realistic components across 4 luminaire lines
part_counter = 1

# StreetStar Parts
streetstar_parts = [
    ("Die-Cast ADC12 Luminaire Housing", "Mechanical", "Die-cast ADC12 Al", 24.50, 4.200, 0.0380, "SUP-MEC-01", 200),
    ("Adjustable Mast Tenon Bracket", "Mechanical", "Galvanized Steel", 7.80, 1.850, 0.0095, "SUP-MEC-03", 300),
    ("150W Dimmable Constant Current Driver", "Electronic", "Encapsulated PCB", 18.20, 0.650, 0.0018, "SUP-ELE-02", 500),
    ("IP66 Surge Protection Device 10kV", "Electronic", "Electronic Module", 4.10, 0.120, 0.0004, "SUP-ELE-03", 500),
    ("High-Efficacy LED Array MCPCB (150W)", "Electronic", "Al-backed FR4 PCB", 12.50, 0.280, 0.0008, "SUP-ELE-01", 1000),
    ("Type II Medium Road Optical Lens 48-LED", "Optics", "Optical Grade PMMA", 5.40, 0.310, 0.0022, "SUP-OPT-01", 400),
    ("Silicone Weatherproof Gasket Seal", "Fastener", "EPDM/Silicone", 1.25, 0.045, 0.0002, "SUP-FAS-01", 1500),
    ("Stainless Steel 304 Captive Fasteners Kit", "Fastener", "SS 304", 1.60, 0.110, 0.0003, "SUP-FAS-01", 2000),
    ("4mm Toughened Protective Glass Plate", "Optics", "Tempered Soda-Lime Glass", 3.90, 0.950, 0.0035, "SUP-OPT-03", 250),
    ("NEMA 7-Pin Smart Lighting Receptacle", "Electronic", "PBT / Phosphor Bronze", 3.10, 0.085, 0.0005, "SUP-ELE-04", 500),
]

for desc, c_type, mat, cost, wt, cbm, sup, moq in streetstar_parts:
    parts_data.append((f"PRT-{part_counter:04d}", desc, "StreetStar LED 150W", c_type, mat, cost, wt, cbm, sup, moq, 0.22))
    part_counter += 1

# CleanSky Troffer Parts
troffer_parts = [
    ("2x2 Deep Drawn CRCA Steel Housing", "Mechanical", "Sheet Metal CRCA Steel", 11.20, 3.400, 0.0450, "SUP-MEC-03", 250),
    ("White Powder-Coated Steel Gear Tray", "Mechanical", "Cold Rolled Steel", 5.60, 1.200, 0.0120, "SUP-MEC-03", 300),
    ("45W Isolated High-PF Flicker-Free Driver", "Electronic", "Flyback SMPS PCB", 8.40, 0.380, 0.0012, "SUP-ELE-03", 600),
    ("Linear LED Boards Array 45W 4000K", "Electronic", "FR4 PCB", 6.80, 0.160, 0.0006, "SUP-ELE-01", 800),
    ("Microprismatic Glare-Control Diffuser", "Optics", "Extruded Polycarbonate", 4.30, 0.720, 0.0180, "SUP-OPT-02", 500),
    ("Push-Fit Quick Disconnect Terminal Block", "Electronic", "Nylon 66 / Copper", 0.65, 0.025, 0.0001, "SUP-ELE-03", 2500),
    ("Earth Continuity Grounding Harness", "Fastener", "Copper Braided Wire", 0.45, 0.030, 0.0001, "SUP-FAS-01", 3000),
    ("Safety Suspension Aircraft Wire Clips", "Fastener", "Galvanized Steel Cable", 1.10, 0.060, 0.0002, "SUP-FAS-01", 1500),
]

for desc, c_type, mat, cost, wt, cbm, sup, moq in troffer_parts:
    parts_data.append((f"PRT-{part_counter:04d}", desc, "CleanSky Troffer 45W", c_type, mat, cost, wt, cbm, sup, moq, 0.20))
    part_counter += 1

# HighBay Pro Industrial Parts
highbay_parts = [
    ("Finned Cold-Forged 6063 Aluminum Heatsink", "Mechanical", "Extruded 6063-T6 Al", 32.80, 5.100, 0.0320, "SUP-MEC-03", 150),
    ("Cast Aluminum Driver Enclosure Box", "Mechanical", "Die-cast ADC12 Al", 14.50, 1.650, 0.0085, "SUP-MEC-02", 200),
    ("200W IP65 High-Efficiency DALI Driver", "Electronic", "Potting Resin Filled SMPS", 27.50, 1.100, 0.0032, "SUP-ELE-02", 300),
    ("COB High-Lumen Density LED Chip Array", "Electronic", "Ceramic Substrate LED", 16.90, 0.140, 0.0004, "SUP-ELE-01", 500),
    ("90-Degree Specular Aluminum Reflector", "Optics", "Spun Anodized Aluminum", 8.20, 0.580, 0.0240, "SUP-OPT-03", 250),
    ("Heavy-Duty Cast Forged Eye-Bolt Hanger", "Fastener", "Drop Forged Steel", 2.40, 0.320, 0.0006, "SUP-FAS-01", 1000),
    ("Optical Grade Polycarbonate Protection Lens", "Optics", "Molded Polycarbonate", 4.80, 0.420, 0.0045, "SUP-OPT-02", 400),
    ("Internal Thermal Interface Phase-Change Pad", "Mechanical", "Silicone/Ceramic Composite", 1.15, 0.015, 0.0001, "SUP-MEC-01", 2000),
]

for desc, c_type, mat, cost, wt, cbm, sup, moq in highbay_parts:
    parts_data.append((f"PRT-{part_counter:04d}", desc, "HighBay Pro Industrial 200W", c_type, mat, cost, wt, cbm, sup, moq, 0.22))
    part_counter += 1

# UrbanPark PostTop Parts + Additional components to reach 50 parts
urban_parts = [
    ("Spun Aluminum Decorative Canopy Hood", "Mechanical", "Deep Drawn 5052 Al", 19.40, 2.300, 0.0420, "SUP-MEC-04", 150),
    ("Clear Cylindrical Impact-Resistant Enclosure", "Optics", "PMMA Acrylic Cylinder", 11.50, 1.450, 0.0280, "SUP-OPT-01", 200),
    ("Cast Decorative Pole Base Adapter 76mm", "Mechanical", "Die-cast ADC12 Al", 16.30, 2.800, 0.0190, "SUP-MEC-01", 150),
    ("60W Programmable Midnight-Dimming Driver", "Electronic", "Electronic PCB", 15.20, 0.520, 0.0016, "SUP-ELE-02", 400),
    ("Circular Symmetric Radial Distribution Lens", "Optics", "Molded PMMA", 6.20, 0.290, 0.0028, "SUP-OPT-01", 350),
    ("Circular 60W LED Ring Board 3000K", "Electronic", "Al-MCPCB", 10.40, 0.220, 0.0011, "SUP-ELE-01", 600),
]

for desc, c_type, mat, cost, wt, cbm, sup, moq in urban_parts:
    parts_data.append((f"PRT-{part_counter:04d}", desc, "UrbanPark Architectural 60W", c_type, mat, cost, wt, cbm, sup, moq, 0.22))
    part_counter += 1

# Fill up to 50 parts with specialized accessories and components
extra_specs = [
    ("DALI-2 Light & Motion Sensor Head", "Electronic", "PBT / Microcontroller", 14.80, 0.090, 0.0006, "SUP-ELE-02", 300),
    ("Die-Cast Wall Mounting Swivel Arm", "Mechanical", "Die-cast ADC12 Al", 13.60, 2.100, 0.0150, "SUP-MEC-01", 200),
    ("Photocell Twist-Lock Dusk-to-Dawn Switch", "Electronic", "Polycarbonate Housing", 5.20, 0.110, 0.0007, "SUP-ELE-04", 500),
    ("Pressure Equalization Breather Vent IP68", "Fastener", "ePTFE Membrane", 1.80, 0.020, 0.0001, "SUP-FAS-01", 1500),
    ("Asymmetric Forward-Throw Batwing Lens", "Optics", "Optical PMMA", 6.80, 0.340, 0.0031, "SUP-OPT-01", 300),
    ("Heat-Pipe Thermal Copper Core Insert", "Mechanical", "Oxygen-Free Copper C1020", 9.40, 0.450, 0.0008, "SUP-MEC-03", 400),
    ("Emergency Battery Backup Module 3-Hour", "Electronic", "LiFePO4 Pack", 22.50, 0.850, 0.0024, "SUP-ELE-03", 250),
    ("Extruded Architectural Linear Profile 1.2m", "Mechanical", "Anodized 6063-T5 Al", 15.90, 1.750, 0.0210, "SUP-MEC-03", 200),
    ("Frosted Opal Anti-Glare Extruded Diffuser", "Optics", "Impact Modified Acrylic", 4.90, 0.480, 0.0110, "SUP-OPT-02", 300),
    ("Quick-Mount Louver Spring Retainers", "Fastener", "Spring Steel 65Mn", 0.55, 0.018, 0.0001, "SUP-FAS-01", 4000),
    ("Zaga-Book 18 Compliant Sensor Receptacle", "Electronic", "High-Temp Polymer", 4.10, 0.070, 0.0004, "SUP-ELE-01", 500),
    ("Corrosion-Proof Marine Coating Primer Base", "Mechanical", "Epoxy-Phenolic", 3.20, 0.350, 0.0015, "SUP-MEC-04", 250),
    ("Internal Cable Routing Strain Relief Glands", "Fastener", "Polyamide PA66", 0.85, 0.035, 0.0002, "SUP-FAS-01", 2000),
    ("Elliptical Beam Narrow Distribution Optic", "Optics", "Optical Grade Polycarbonate", 5.90, 0.280, 0.0025, "SUP-OPT-03", 350),
    ("Isolated Step-Down DC-DC Converter 24V", "Electronic", "Compact FR4 Board", 7.60, 0.150, 0.0008, "SUP-ELE-03", 500),
    ("Sheet Metal Reflector Clip Brackets", "Mechanical", "Zinc-Plated Steel", 1.40, 0.095, 0.0005, "SUP-MEC-03", 1000),
    ("High-Temperature Silicone Potting Gel (1kg)", "Fastener", "Two-Part Silicone", 6.50, 1.050, 0.0011, "SUP-FAS-01", 300),
    ("Polycarbonate Clear Protective Dome Cover", "Optics", "UV-Stabilized Makrolon PC", 7.20, 0.620, 0.0090, "SUP-OPT-01", 250),
]

for desc, c_type, mat, cost, wt, cbm, sup, moq in extra_specs:
    if part_counter > 50:
        break
    parts_data.append((f"PRT-{part_counter:04d}", desc, "Multi-Platform Common", c_type, mat, cost, wt, cbm, sup, moq, 0.22))
    part_counter += 1

df_parts = pd.DataFrame(parts_data, columns=[
    "part_id", "part_description", "luminaire_model", "component_type",
    "material", "unit_cost_usd", "unit_weight_kg", "unit_volume_cbm",
    "primary_supplier_id", "minimum_order_qty", "holding_cost_annual_pct"
])

# -----------------------------------------------------------------------------
# 3. Historical Purchase Orders Generator (18 months, ~1,500 POs)
# -----------------------------------------------------------------------------
supplier_dict = df_suppliers.set_index("supplier_id").to_dict("index")
parts_dict = df_parts.set_index("part_id").to_dict("index")

start_date = datetime.date(2025, 1, 1)
end_date = datetime.date(2026, 6, 30)
days_range = (end_date - start_date).days

po_records = []
po_id_num = 10001

for _ in range(1400):
    part_id = random.choice(df_parts["part_id"].tolist())
    p_info = parts_dict[part_id]
    sup_id = p_info["primary_supplier_id"]
    s_info = supplier_dict[sup_id]
    
    # Order date
    order_day_offset = random.randint(0, days_range - 60)
    order_date = start_date + datetime.timedelta(days=order_day_offset)
    
    # Contracted Lead time & variance based on category and country
    base_lead_time = s_info["contracted_lead_time_days"]
    tier = s_info["reliability_tier"]
    category = p_info["component_type"]
    
    # Mechanical & overseas suppliers have higher variance
    if category == "Mechanical":
        variance = np.random.normal(loc=2.5, scale=6.0) # Slight delay tendency due to casting/mold prep
    elif category == "Electronic":
        variance = np.random.normal(loc=4.0, scale=9.0) # Chip supply chain disruptions
    elif category == "Optics":
        variance = np.random.normal(loc=0.5, scale=4.0)
    else:
        variance = np.random.normal(loc=-1.0, scale=2.5) # Fasteners are fast
        
    if tier == "Tier 3":
        variance += 7.0
    elif tier == "Tier 2":
        variance += 2.0
        
    actual_lead_time = max(5, int(base_lead_time + variance))
    promised_lead_time = base_lead_time
    
    promised_date = order_date + datetime.timedelta(days=promised_lead_time)
    actual_delivery_date = order_date + datetime.timedelta(days=actual_lead_time)
    
    # Order Quantity (multiples of MOQ)
    multiplier = random.choice([1, 1.5, 2, 3, 5])
    order_qty = int(p_info["minimum_order_qty"] * multiplier)
    
    # Received Quantity (Fulfillment rate)
    fulfillment_draw = random.random()
    if fulfillment_draw < 0.88:
        received_qty = order_qty # 100% full
    elif fulfillment_draw < 0.96:
        received_qty = int(order_qty * random.uniform(0.92, 0.98)) # Minor short-shipment
    else:
        received_qty = int(order_qty * random.uniform(0.80, 0.90)) # Major short-shipment
        
    # Price slight variation
    unit_price = round(p_info["unit_cost_usd"] * random.uniform(0.96, 1.05), 2)
    
    # Freight Mode
    country = s_info["country_origin"]
    if country in ["India"]:
        freight_mode = "Road Logistics"
    elif actual_lead_time - base_lead_time > 12 and random.random() < 0.35:
        freight_mode = "Air Expedited" # Signify expedited to prevent line stoppage
    else:
        freight_mode = "Ocean Freight"
        
    # Inspection defect rate (Mechanical & Tier 3 have higher initial scrap)
    if tier == "Tier 3":
        defect_rate = round(float(np.random.beta(a=2, b=40)), 4) # ~4-6%
    elif category == "Mechanical":
        defect_rate = round(float(np.random.beta(a=1.5, b=70)), 4) # ~2%
    else:
        defect_rate = round(float(np.random.beta(a=1, b=120)), 4) # <1%
        
    status = "Delivered"
    if actual_delivery_date > datetime.date(2026, 6, 30):
        actual_delivery_date = None
        status = "In Transit"
        
    po_records.append((
        f"PO-{po_id_num}",
        part_id,
        sup_id,
        order_date.isoformat(),
        promised_date.isoformat(),
        actual_delivery_date.isoformat() if actual_delivery_date else None,
        order_qty,
        received_qty if status == "Delivered" else 0,
        unit_price,
        freight_mode,
        defect_rate,
        status
    ))
    po_id_num += 1

df_po = pd.DataFrame(po_records, columns=[
    "po_id", "part_id", "supplier_id", "order_date", "promised_delivery_date",
    "actual_delivery_date", "order_quantity", "received_quantity",
    "unit_purchase_price", "freight_mode", "inspection_defect_rate", "status"
])

# -----------------------------------------------------------------------------
# 4. Current Inventory Levels Snapshot
# -----------------------------------------------------------------------------
inv_records = []
for i, part in enumerate(parts_data):
    p_id = part[0]
    c_type = part[3]
    moq = part[9]
    
    # Monthly consumption based on luminaire demand
    monthly_consumption = int(moq * random.uniform(1.2, 4.5))
    
    # Current stock simulation
    # Deliberately create some stockouts, some healthy, some overstocked
    stock_ratio = random.choice([0.15, 0.45, 0.9, 1.2, 1.8, 3.2])
    current_stock = int(monthly_consumption * stock_ratio)
    reserved_prod = int(current_stock * random.uniform(0.15, 0.55))
    on_order = int(monthly_consumption * random.uniform(0.5, 2.0))
    last_replenish = (datetime.date(2026, 6, 25) - datetime.timedelta(days=random.randint(2, 45))).isoformat()
    
    inv_records.append((
        i + 1,
        p_id,
        current_stock,
        reserved_prod,
        on_order,
        monthly_consumption,
        last_replenish
    ))

df_inv = pd.DataFrame(inv_records, columns=[
    "snapshot_id", "part_id", "current_stock_units", "reserved_production_units",
    "on_order_units", "monthly_consumption_rate", "last_replenishment_date"
])

# -----------------------------------------------------------------------------
# 5. Export to CSV & SQLite DB
# -----------------------------------------------------------------------------
df_suppliers.to_csv(os.path.join(DATA_DIR, "suppliers.csv"), index=False)
df_parts.to_csv(os.path.join(DATA_DIR, "parts_bom.csv"), index=False)
df_po.to_csv(os.path.join(DATA_DIR, "purchase_orders.csv"), index=False)
df_inv.to_csv(os.path.join(DATA_DIR, "inventory_levels.csv"), index=False)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

with open(SCHEMA_PATH, "r") as f:
    cursor.executescript(f.read())

df_suppliers.to_sql("suppliers", conn, if_exists="append", index=False)
df_parts.to_sql("parts_bom", conn, if_exists="append", index=False)
df_po.to_sql("purchase_orders", conn, if_exists="append", index=False)
df_inv.to_sql("inventory_levels", conn, if_exists="append", index=False)

conn.commit()
conn.close()

print(f"Data generation complete.")
print(f"Database created at: {DB_PATH}")
print(f"Suppliers count: {len(df_suppliers)}")
print(f"Parts BOM count: {len(df_parts)}")
print(f"Purchase Orders count: {len(df_po)}")
print(f"Inventory Snapshot count: {len(df_inv)}")
