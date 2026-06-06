"""
Capital Colours – Full Demo Data Loader
Run: bench --site colour execute masterbatch.demo.load_demo_data.run
"""

import frappe
from frappe.utils import today, add_days
import random

# ─────────────────────────────────────────────────────────────────────────────
ITEM_GROUPS = [
    {"item_group_name": "Raw Materials - MB",    "parent_item_group": "All Item Groups"},
    {"item_group_name": "Finished Goods - MB",   "parent_item_group": "All Item Groups"},
    {"item_group_name": "Packing Materials - MB","parent_item_group": "All Item Groups"},
]

RAW_MATERIALS = [
    # (item_code, item_name, valuation_rate)
    ("RM-PE-NAT",   "PE Natural Resin (LDPE)",       85),
    ("RM-PP-NAT",   "PP Natural Resin (Homo)",        90),
    ("RM-TIO2",     "Titanium Dioxide (TiO2)",       220),
    ("RM-CARBON",   "Carbon Black N330",             180),
    ("RM-PIG-RED",  "Red Pigment PR254",             650),
    ("RM-PIG-YEL",  "Yellow Pigment PY83",           480),
    ("RM-PIG-BLUE", "Blue Pigment PB15",             520),
    ("RM-PIG-GRN",  "Green Pigment PG7",             540),
    ("RM-CACO3",    "Calcium Carbonate (CaCO3)",       28),
    ("RM-ANTIOXD",  "Antioxidant Irganox 1010",      850),
    ("RM-UVSTAB",   "UV Stabilizer Tinuvin 770",    1200),
    ("RM-LUBRIC",   "Calcium Stearate (Lubricant)",  120),
    ("RM-WAXPE",    "Polyethylene Wax",              160),
]

FINISHED_GOODS = [
    # (item_code, item_name, valuation_rate, shade_code)
    ("MB-WHITE-PE",   "White Masterbatch PE (50% TiO2)",    320, "SH-W01"),
    ("MB-WHITE-PP",   "White Masterbatch PP (50% TiO2)",    340, "SH-W02"),
    ("MB-BLACK-PE",   "Black Masterbatch PE (40% CB)",      260, "SH-B01"),
    ("MB-BLACK-PP",   "Black Masterbatch PP (40% CB)",      275, "SH-B02"),
    ("MB-RED-001",    "Red Masterbatch PE (Vivid Red)",     680, "SH-R01"),
    ("MB-RED-002",    "Red Masterbatch PP (Brick Red)",     720, "SH-R02"),
    ("MB-YELLOW-001", "Yellow Masterbatch PE",              620, "SH-Y01"),
    ("MB-BLUE-001",   "Blue Masterbatch PE",                660, "SH-BL01"),
    ("MB-GREEN-001",  "Green Masterbatch PE",               640, "SH-G01"),
    ("MB-FILLER-PE",  "Filler Masterbatch PE (70% CaCO3)",  95, "SH-F01"),
    ("MB-FILLER-PP",  "Filler Masterbatch PP (70% CaCO3)", 100, "SH-F02"),
    ("MB-ADDTV-AO",   "Antioxidant Masterbatch PE",        450, "SH-A01"),
    ("MB-PEARL-01",   "Pearlescent Masterbatch PE",        890, "SH-SP01"),
]

PACKING = [
    ("PKG-BAG-25",  "HDPE Bag 25 KG",   12),
    ("PKG-LABEL",   "Product Label",     0.5),
]

CUSTOMERS = [
    ("Vivid Plastics",    "FMCG Packaging",        "Hyderabad"),
    ("Aluva Plastics",    "Furniture & Household",  "Kochi"),
    ("Supreme Polymers",  "Industrial Packaging",   "Mumbai"),
    ("Raj Films",         "Film & Packaging",       "Delhi"),
    ("Ganga Packaging",   "Woven Sacks",            "Ahmedabad"),
]

SUPPLIERS = [
    ("Reliance Industries", "PE/PP Resin Supplier"),
    ("Cabot Corporation",   "Carbon Black Supplier"),
    ("BASF India",          "Additives Supplier"),
    ("Clariant India",      "Pigment Supplier"),
    ("Omya India",          "CaCO3 Supplier"),
]

# BOM recipes: (finished_item, [(rm_item, qty_per_100kg)])
BOMS = {
    "MB-WHITE-PE": [
        ("RM-PE-NAT",  47.0),
        ("RM-TIO2",    50.0),
        ("RM-UVSTAB",   1.5),
        ("RM-LUBRIC",   1.0),
        ("RM-ANTIOXD",  0.5),
    ],
    "MB-WHITE-PP": [
        ("RM-PP-NAT",  47.0),
        ("RM-TIO2",    50.0),
        ("RM-UVSTAB",   1.5),
        ("RM-LUBRIC",   1.0),
        ("RM-ANTIOXD",  0.5),
    ],
    "MB-BLACK-PE": [
        ("RM-PE-NAT",  58.0),
        ("RM-CARBON",  40.0),
        ("RM-WAXPE",    1.0),
        ("RM-ANTIOXD",  0.5),
        ("RM-LUBRIC",   0.5),
    ],
    "MB-BLACK-PP": [
        ("RM-PP-NAT",  58.0),
        ("RM-CARBON",  40.0),
        ("RM-WAXPE",    1.0),
        ("RM-ANTIOXD",  0.5),
        ("RM-LUBRIC",   0.5),
    ],
    "MB-RED-001": [
        ("RM-PE-NAT",   55.0),
        ("RM-PIG-RED",  40.0),
        ("RM-WAXPE",     3.0),
        ("RM-ANTIOXD",   1.0),
        ("RM-LUBRIC",    1.0),
    ],
    "MB-RED-002": [
        ("RM-PP-NAT",   55.0),
        ("RM-PIG-RED",  40.0),
        ("RM-WAXPE",     3.0),
        ("RM-ANTIOXD",   1.0),
        ("RM-LUBRIC",    1.0),
    ],
    "MB-YELLOW-001": [
        ("RM-PE-NAT",    55.0),
        ("RM-PIG-YEL",   40.0),
        ("RM-WAXPE",      3.0),
        ("RM-ANTIOXD",    1.0),
        ("RM-LUBRIC",     1.0),
    ],
    "MB-BLUE-001": [
        ("RM-PE-NAT",    55.0),
        ("RM-PIG-BLUE",  40.0),
        ("RM-WAXPE",      3.0),
        ("RM-ANTIOXD",    1.0),
        ("RM-LUBRIC",     1.0),
    ],
    "MB-GREEN-001": [
        ("RM-PE-NAT",    55.0),
        ("RM-PIG-GRN",   40.0),
        ("RM-WAXPE",      3.0),
        ("RM-ANTIOXD",    1.0),
        ("RM-LUBRIC",     1.0),
    ],
    "MB-FILLER-PE": [
        ("RM-PE-NAT",  28.0),
        ("RM-CACO3",   70.0),
        ("RM-LUBRIC",   1.5),
        ("RM-ANTIOXD",  0.5),
    ],
    "MB-FILLER-PP": [
        ("RM-PP-NAT",  28.0),
        ("RM-CACO3",   70.0),
        ("RM-LUBRIC",   1.5),
        ("RM-ANTIOXD",  0.5),
    ],
    "MB-ADDTV-AO": [
        ("RM-PE-NAT",   75.0),
        ("RM-ANTIOXD",  20.0),
        ("RM-UVSTAB",    4.0),
        ("RM-LUBRIC",    1.0),
    ],
    "MB-PEARL-01": [
        ("RM-PE-NAT",   60.0),
        ("RM-PIG-YEL",  15.0),
        ("RM-TIO2",     20.0),
        ("RM-ANTIOXD",   2.0),
        ("RM-LUBRIC",    2.0),
        ("RM-WAXPE",     1.0),
    ],
}

OPERATORS = ["Ravi Kumar", "Suresh Babu", "Mahesh Rao", "Kishan Singh", "Naresh Reddy"]
SHIFTS = ["Morning", "Afternoon", "Night"]
QC = ["Passed", "Passed", "Passed", "Passed", "Failed"]  # weighted

# ─────────────────────────────────────────────────────────────────────────────

def make_item_group(g):
    if frappe.db.exists("Item Group", g["item_group_name"]):
        return
    doc = frappe.new_doc("Item Group")
    doc.item_group_name = g["item_group_name"]
    doc.parent_item_group = g["parent_item_group"]
    doc.insert(ignore_permissions=True)

def make_item(code, name, group, rate, is_purchase=0, is_sales=0, is_stock=1):
    if frappe.db.exists("Item", code):
        return
    doc = frappe.new_doc("Item")
    doc.item_code = code
    doc.item_name = name
    doc.item_group = group
    doc.stock_uom = "KG"
    doc.is_purchase_item = is_purchase
    doc.is_sales_item = is_sales
    doc.is_stock_item = is_stock
    doc.valuation_rate = rate
    doc.insert(ignore_permissions=True)

def make_customer(name, group, city):
    if frappe.db.exists("Customer", name):
        return
    doc = frappe.new_doc("Customer")
    doc.customer_name = name
    doc.customer_group = "All Customer Groups"
    doc.territory = "India"
    doc.insert(ignore_permissions=True)

def make_supplier(name, group):
    if frappe.db.exists("Supplier", name):
        return
    doc = frappe.new_doc("Supplier")
    doc.supplier_name = name
    doc.supplier_group = "All Supplier Groups"
    doc.insert(ignore_permissions=True)

def make_shade(code, name, product_type, resin=None):
    if frappe.db.exists("Shade Code", code):
        return
    doc = frappe.new_doc("Shade Code")
    doc.shade_code = code
    doc.shade_name = name
    doc.product_type = product_type
    if resin:
        doc.base_resin = resin
    doc.insert(ignore_permissions=True)

def make_bom(item_code, ingredients, qty=500):
    if frappe.db.exists("BOM", {"item": item_code, "is_active": 1}):
        return
    doc = frappe.new_doc("BOM")
    doc.item = item_code
    doc.quantity = qty
    doc.uom = "KG"
    for rm, pct in ingredients:
        child = doc.append("items", {})
        child.item_code = rm
        child.qty = round((pct / 100) * qty, 3)
        child.uom = "KG"
    doc.insert(ignore_permissions=True)
    doc.submit()

def make_stock_entry_receipt(item_code, qty, warehouse, rate):
    """Opening stock receipt"""
    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Material Receipt"
    se.posting_date = add_days(today(), -60)
    row = se.append("items", {})
    row.item_code = item_code
    row.qty = qty
    row.basic_rate = rate
    row.t_warehouse = warehouse
    se.insert(ignore_permissions=True)
    se.submit()

def make_batch_production_sheet(batch_no, fg_item, shade_code, planned, actual, date, operator, shift, ingredients, qc):
    if frappe.db.exists("Batch Production Sheet", batch_no):
        return
    doc = frappe.new_doc("Batch Production Sheet")
    doc.batch_no = batch_no
    doc.production_date = date
    doc.finished_item = fg_item
    doc.shade_code = shade_code
    doc.planned_qty = planned
    doc.actual_output_kg = actual
    doc.rejection_kg = round(sum(i[1] for i in ingredients) - actual, 2)
    doc.operator = operator
    doc.shift = shift
    doc.qc_status = qc
    for item_code, consumed, plan_qty in ingredients:
        row = doc.append("consumption_items", {})
        row.item_code = item_code
        row.item_name = frappe.db.get_value("Item", item_code, "item_name") or item_code
        row.planned_qty = plan_qty
        row.qty_consumed = consumed
    doc.insert(ignore_permissions=True)
    doc.submit()

def make_purchase_order(supplier, items_list, date):
    po = frappe.new_doc("Purchase Order")
    po.supplier = supplier
    po.transaction_date = date
    po.schedule_date = add_days(date, 7)
    for ic, qty, rate in items_list:
        row = po.append("items", {})
        row.item_code = ic
        row.qty = qty
        row.rate = rate
        row.schedule_date = add_days(date, 7)
        row.uom = "KG"
    po.insert(ignore_permissions=True)
    po.submit()

def make_sales_order(customer, items_list, date):
    so = frappe.new_doc("Sales Order")
    so.customer = customer
    so.transaction_date = date
    so.delivery_date = add_days(date, 10)
    for ic, qty, rate in items_list:
        row = so.append("items", {})
        row.item_code = ic
        row.qty = qty
        row.rate = rate
        row.uom = "KG"
        row.delivery_date = add_days(date, 10)
    so.insert(ignore_permissions=True)
    so.submit()

# ─────────────────────────────────────────────────────────────────────────────

def run():
    frappe.set_user("Administrator")
    company = frappe.db.get_single_value("Global Defaults", "default_company") or "colour"
    abbr = frappe.db.get_value("Company", company, "abbr") or "CC"
    wh_stores = f"Stores - {abbr}"
    wh_fg = f"Finished Goods - {abbr}"
    wh_wip = f"Work In Progress - {abbr}"

    print("→ Creating Item Groups...")
    for g in ITEM_GROUPS:
        make_item_group(g)
    frappe.db.commit()

    print("→ Creating Raw Materials...")
    for code, name, rate in RAW_MATERIALS:
        make_item(code, name, "Raw Materials - MB", rate, is_purchase=1)
    frappe.db.commit()

    print("→ Creating Finished Goods...")
    for code, name, rate, shade in FINISHED_GOODS:
        make_item(code, name, "Finished Goods - MB", rate, is_sales=1)
    frappe.db.commit()

    print("→ Creating Packing Materials...")
    for code, name, rate in PACKING:
        make_item(code, name, "Packing Materials - MB", rate, is_purchase=1)
    frappe.db.commit()

    print("→ Creating Customers...")
    for name, grp, city in CUSTOMERS:
        make_customer(name, grp, city)
    frappe.db.commit()

    print("→ Creating Suppliers...")
    for name, grp in SUPPLIERS:
        make_supplier(name, grp)
    frappe.db.commit()

    print("→ Creating Shade Codes...")
    shade_map = {
        "SH-W01":  ("White PE Standard",    "White MB",   "RM-PE-NAT"),
        "SH-W02":  ("White PP Standard",    "White MB",   "RM-PP-NAT"),
        "SH-B01":  ("Black PE Standard",    "Black MB",   "RM-PE-NAT"),
        "SH-B02":  ("Black PP Standard",    "Black MB",   "RM-PP-NAT"),
        "SH-R01":  ("Vivid Red PE",         "Colour MB",  "RM-PE-NAT"),
        "SH-R02":  ("Brick Red PP",         "Colour MB",  "RM-PP-NAT"),
        "SH-Y01":  ("Lemon Yellow PE",      "Colour MB",  "RM-PE-NAT"),
        "SH-BL01": ("Royal Blue PE",        "Colour MB",  "RM-PE-NAT"),
        "SH-G01":  ("Forest Green PE",      "Colour MB",  "RM-PE-NAT"),
        "SH-F01":  ("Filler PE 70%",        "Filler MB",  "RM-PE-NAT"),
        "SH-F02":  ("Filler PP 70%",        "Filler MB",  "RM-PP-NAT"),
        "SH-A01":  ("Antioxidant PE",       "Additive MB","RM-PE-NAT"),
        "SH-SP01": ("Pearlescent PE",       "Specialty MB","RM-PE-NAT"),
    }
    for code, (name, ptype, resin) in shade_map.items():
        make_shade(code, name, ptype, resin)
    frappe.db.commit()

    print("→ Creating BOMs...")
    for fg_item, ingredients in BOMS.items():
        try:
            make_bom(fg_item, ingredients, qty=500)
        except Exception as e:
            print(f"  BOM skip {fg_item}: {e}")
    frappe.db.commit()

    print("→ Adding opening stock for Raw Materials...")
    opening_stocks = [
        ("RM-PE-NAT",  15000, wh_stores, 85),
        ("RM-PP-NAT",   8000, wh_stores, 90),
        ("RM-TIO2",     5000, wh_stores, 220),
        ("RM-CARBON",   3000, wh_stores, 180),
        ("RM-PIG-RED",   800, wh_stores, 650),
        ("RM-PIG-YEL",   600, wh_stores, 480),
        ("RM-PIG-BLUE",  700, wh_stores, 520),
        ("RM-PIG-GRN",   500, wh_stores, 540),
        ("RM-CACO3",   20000, wh_stores, 28),
        ("RM-ANTIOXD",   400, wh_stores, 850),
        ("RM-UVSTAB",    300, wh_stores, 1200),
        ("RM-LUBRIC",   1500, wh_stores, 120),
        ("RM-WAXPE",    1000, wh_stores, 160),
    ]
    for ic, qty, wh, rate in opening_stocks:
        try:
            make_stock_entry_receipt(ic, qty, wh, rate)
        except Exception as e:
            print(f"  Stock skip {ic}: {e}")
    frappe.db.commit()

    print("→ Creating Batch Production Sheets (30 batches)...")
    fg_shades = [fg[:2] + (fg[3],) for fg in FINISHED_GOODS]  # (code, name, shade_code)
    batch_counter = 1
    for day_offset in range(30, 0, -1):
        date = add_days(today(), -day_offset)
        batches_today = random.randint(2, 4)
        for _ in range(batches_today):
            fg_item, _, shade_code = random.choice(fg_shades)
            recipe = BOMS.get(fg_item, [])
            if not recipe:
                continue
            planned = random.choice([250, 500, 750, 1000])
            actual = round(planned * random.uniform(0.97, 0.995), 1)
            ingredients = []
            for rm, pct in recipe:
                plan_qty = round((pct / 100) * planned, 2)
                actual_qty = round(plan_qty * random.uniform(0.98, 1.02), 2)
                ingredients.append((rm, actual_qty, plan_qty))
            batch_no = f"BTCH-{str(batch_counter).zfill(4)}"
            operator = random.choice(OPERATORS)
            shift = random.choice(SHIFTS)
            qc = random.choice(QC)
            try:
                make_batch_production_sheet(
                    batch_no, fg_item, shade_code, planned, actual, date,
                    operator, shift, ingredients, qc
                )
            except Exception as e:
                print(f"  Batch skip {batch_no}: {e}")
            batch_counter += 1
    frappe.db.commit()

    print("→ Creating Purchase Orders...")
    po_data = [
        ("Reliance Industries", [("RM-PE-NAT", 10000, 85), ("RM-PP-NAT", 5000, 90)], add_days(today(), -45)),
        ("Cabot Corporation",   [("RM-CARBON",  2000, 180)],                          add_days(today(), -30)),
        ("Clariant India",      [("RM-PIG-RED",  500, 650), ("RM-PIG-YEL", 400, 480)],add_days(today(), -20)),
        ("BASF India",          [("RM-ANTIOXD",  300, 850), ("RM-UVSTAB",  200, 1200)],add_days(today(), -15)),
        ("Omya India",          [("RM-CACO3",  15000, 28)],                            add_days(today(), -10)),
    ]
    for sup, items, date in po_data:
        try:
            make_purchase_order(sup, items, date)
        except Exception as e:
            print(f"  PO skip {sup}: {e}")
    frappe.db.commit()

    print("→ Creating Sales Orders...")
    so_data = [
        ("Vivid Plastics",   [("MB-WHITE-PE", 2000, 320), ("MB-RED-001", 500, 680)],   add_days(today(), -25)),
        ("Aluva Plastics",   [("MB-BLACK-PE", 1500, 260), ("MB-YELLOW-001", 300, 620)],add_days(today(), -18)),
        ("Supreme Polymers", [("MB-FILLER-PE", 3000, 95), ("MB-WHITE-PP", 1000, 340)], add_days(today(), -12)),
        ("Raj Films",        [("MB-BLACK-PP", 800, 275),  ("MB-BLUE-001", 400, 660)],  add_days(today(), -8)),
        ("Ganga Packaging",  [("MB-FILLER-PP", 2500, 100),("MB-ADDTV-AO", 200, 450)],  add_days(today(), -5)),
    ]
    for cust, items, date in so_data:
        try:
            make_sales_order(cust, items, date)
        except Exception as e:
            print(f"  SO skip {cust}: {e}")
    frappe.db.commit()

    print("\n✅ Capital Colours demo data loaded successfully!")
    print("   → Items, BOMs, Customers, Suppliers, Purchase Orders, Sales Orders")
    print("   → 30+ Batch Production Sheets with realistic data")
    print("   → Shade Codes, Lab Formulations structure ready")
    print("   → Reports: Production Summary, RM Consumption, Shade-wise Production")
