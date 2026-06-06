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
    doc.customer_group = "Commercial"
    doc.territory = "India"
    doc.insert(ignore_permissions=True)

def make_supplier(name, group):
    if frappe.db.exists("Supplier", name):
        return
    doc = frappe.new_doc("Supplier")
    doc.supplier_name = name
    doc.supplier_group = "Raw Material"
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


def fix_shades_and_batches():
    import random
    frappe.set_user("Administrator")

    # remove any previously created (hash-named) shade codes
    for nm in frappe.get_all("Shade Code", pluck="name"):
        frappe.delete_doc("Shade Code", nm, force=1, ignore_permissions=True)
    frappe.db.commit()

    shade_map = {
        "SH-W01":  ("White PE Standard",    "White MB",     "RM-PE-NAT"),
        "SH-W02":  ("White PP Standard",    "White MB",     "RM-PP-NAT"),
        "SH-B01":  ("Black PE Standard",    "Black MB",     "RM-PE-NAT"),
        "SH-B02":  ("Black PP Standard",    "Black MB",     "RM-PP-NAT"),
        "SH-R01":  ("Vivid Red PE",         "Colour MB",    "RM-PE-NAT"),
        "SH-R02":  ("Brick Red PP",         "Colour MB",    "RM-PP-NAT"),
        "SH-Y01":  ("Lemon Yellow PE",      "Colour MB",    "RM-PE-NAT"),
        "SH-BL01": ("Royal Blue PE",        "Colour MB",    "RM-PE-NAT"),
        "SH-G01":  ("Forest Green PE",      "Colour MB",    "RM-PE-NAT"),
        "SH-F01":  ("Filler PE 70%",        "Filler MB",    "RM-PE-NAT"),
        "SH-F02":  ("Filler PP 70%",        "Filler MB",    "RM-PP-NAT"),
        "SH-A01":  ("Antioxidant PE",       "Additive MB",  "RM-PE-NAT"),
        "SH-SP01": ("Pearlescent PE",       "Specialty MB", "RM-PE-NAT"),
    }
    for code, (name, ptype, resin) in shade_map.items():
        make_shade(code, name, ptype, resin)
    frappe.db.commit()

    # remove any previously created batches then recreate cleanly
    for nm in frappe.get_all("Batch Production Sheet", pluck="name"):
        d = frappe.get_doc("Batch Production Sheet", nm)
        if d.docstatus == 1:
            d.cancel()
        frappe.delete_doc("Batch Production Sheet", nm, force=1, ignore_permissions=True)
    frappe.db.commit()

    fg_shades = [fg[:2] + (fg[3],) for fg in FINISHED_GOODS]
    batch_counter = 1
    created = 0
    for day_offset in range(30, 0, -1):
        date = add_days(today(), -day_offset)
        for _ in range(random.randint(2, 4)):
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
            try:
                make_batch_production_sheet(
                    batch_no, fg_item, shade_code, planned, actual, date,
                    random.choice(OPERATORS), random.choice(SHIFTS), ingredients, random.choice(QC)
                )
                created += 1
            except Exception as e:
                print(f"  batch skip {batch_no}: {e}")
            batch_counter += 1
    frappe.db.commit()
    print(f"shades recreated ({len(shade_map)}), batches created ({created})")


def build_demo_workspace():
    """Create Number Cards, Dashboard Charts and the Masterbatch workspace."""
    import json
    frappe.set_user("Administrator")

    def h():
        return frappe.generate_hash(length=10)

    # ---- Number Cards ----
    number_cards = [
        {"name": "MB Total Batches", "label": "Total Batches", "document_type": "Batch Production Sheet",
         "function": "Count", "filters_json": json.dumps([["Batch Production Sheet", "docstatus", "=", 1]])},
        {"name": "MB Total Output", "label": "Total Output (KG)", "document_type": "Batch Production Sheet",
         "function": "Sum", "aggregate_function_based_on": "actual_output_kg",
         "filters_json": json.dumps([["Batch Production Sheet", "docstatus", "=", 1]])},
        {"name": "MB Open Sales Orders", "label": "Sales Orders", "document_type": "Sales Order",
         "function": "Count", "filters_json": json.dumps([["Sales Order", "docstatus", "=", 1]])},
        {"name": "MB Open Purchase Orders", "label": "Purchase Orders", "document_type": "Purchase Order",
         "function": "Count", "filters_json": json.dumps([["Purchase Order", "docstatus", "=", 1]])},
    ]
    for nc in number_cards:
        try:
            if frappe.db.exists("Number Card", nc["name"]):
                frappe.delete_doc("Number Card", nc["name"], force=1, ignore_permissions=True)
            doc = frappe.new_doc("Number Card")
            doc.update(nc)
            doc.label = nc["label"]
            doc.name = nc["name"]
            doc.is_public = 1
            doc.show_percentage_stats = 1
            doc.insert(ignore_permissions=True)
        except Exception as e:
            print(f"  number card skip {nc['name']}: {e}")
    frappe.db.commit()

    # ---- Dashboard Charts ----
    charts = [
        {"name": "MB Daily Production", "chart_name": "Daily Production Output",
         "chart_type": "Sum", "document_type": "Batch Production Sheet",
         "based_on": "production_date", "value_based_on": "actual_output_kg",
         "timespan": "Last Month", "time_interval": "Daily", "type": "Line",
         "filters_json": json.dumps([["Batch Production Sheet", "docstatus", "=", 1]])},
        {"name": "MB Shade Output", "chart_name": "Shade-wise Output (KG)",
         "chart_type": "Group By", "document_type": "Batch Production Sheet",
         "group_by_based_on": "shade_code", "group_by_type": "Sum",
         "aggregate_function_based_on": "actual_output_kg", "type": "Bar",
         "filters_json": json.dumps([["Batch Production Sheet", "docstatus", "=", 1]])},
        {"name": "MB QC Status", "chart_name": "Production by QC Status",
         "chart_type": "Group By", "document_type": "Batch Production Sheet",
         "group_by_based_on": "qc_status", "group_by_type": "Count", "type": "Donut",
         "filters_json": json.dumps([["Batch Production Sheet", "docstatus", "=", 1]])},
    ]
    for ch in charts:
        try:
            if frappe.db.exists("Dashboard Chart", ch["name"]):
                frappe.delete_doc("Dashboard Chart", ch["name"], force=1, ignore_permissions=True)
            doc = frappe.new_doc("Dashboard Chart")
            doc.update(ch)
            doc.name = ch["name"]
            doc.is_public = 1
            doc.insert(ignore_permissions=True)
        except Exception as e:
            print(f"  chart skip {ch['name']}: {e}")
    frappe.db.commit()

    # ---- Workspace ----
    if frappe.db.exists("Workspace", "Masterbatch"):
        frappe.delete_doc("Workspace", "Masterbatch", force=1, ignore_permissions=True)
        frappe.db.commit()

    ws = frappe.new_doc("Workspace")
    ws.name = "Masterbatch"
    ws.title = "Masterbatch"
    ws.label = "Masterbatch"
    ws.module = "Masterbatch"
    ws.public = 1
    ws.icon = "manufacturing"
    ws.is_hidden = 0

    shortcuts = [
        ("Batch Production Sheet", "Batch Production Sheet", "DocType", "#7B2D8B"),
        ("Shade Code", "Shade Code", "DocType", "#318AD8"),
        ("Lab Formulation", "Lab Formulation", "DocType", "#29CD42"),
        ("Production Summary", "Production Summary", "Report", "#FFC107"),
        ("RM Consumption", "Raw Material Consumption", "Report", "#FF5858"),
        ("Shade-wise Production", "Shade-wise Production", "Report", "#00BCD4"),
    ]
    for label, link_to, typ, color in shortcuts:
        ws.append("shortcuts", {"label": label, "link_to": link_to, "type": typ, "color": color})

    for nc in number_cards:
        ws.append("number_cards", {"number_card_name": nc["name"], "label": nc["label"]})

    for ch in charts:
        ws.append("charts", {"chart_name": ch["name"], "label": ch["chart_name"]})

    blocks = []
    blocks.append({"id": h(), "type": "header",
                   "data": {"text": "<span><b>Capital Colours — Masterbatch Manufacturing</b></span>", "col": 12}})
    blocks.append({"id": h(), "type": "paragraph",
                   "data": {"text": "Production, Quality, Inventory & Sales — live overview", "col": 12}})
    for nc in number_cards:
        blocks.append({"id": h(), "type": "number_card", "data": {"number_card_name": nc["name"], "col": 3}})
    blocks.append({"id": h(), "type": "chart", "data": {"chart_name": "MB Daily Production", "col": 12}})
    blocks.append({"id": h(), "type": "chart", "data": {"chart_name": "MB Shade Output", "col": 8}})
    blocks.append({"id": h(), "type": "chart", "data": {"chart_name": "MB QC Status", "col": 4}})
    blocks.append({"id": h(), "type": "header", "data": {"text": "<span><b>Quick Links</b></span>", "col": 12}})
    for label, link_to, typ, color in shortcuts:
        blocks.append({"id": h(), "type": "shortcut", "data": {"shortcut_name": label, "col": 4}})

    ws.content = json.dumps(blocks)
    ws.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"workspace built: {len(number_cards)} cards, {len(charts)} charts, {len(shortcuts)} shortcuts")


def build_demo_workspace2():
    import json
    frappe.set_user("Administrator")

    def h():
        return frappe.generate_hash(length=10)

    f_batch = json.dumps([["Batch Production Sheet", "docstatus", "=", 1]])
    f_so = json.dumps([["Sales Order", "docstatus", "=", 1]])
    f_po = json.dumps([["Purchase Order", "docstatus", "=", 1]])

    # clean any existing objects
    for lbl in ["Total Batches", "Total Output (KG)", "Sales Orders", "Purchase Orders"]:
        for nm in frappe.get_all("Number Card", filters={"label": lbl}, pluck="name"):
            frappe.delete_doc("Number Card", nm, force=1, ignore_permissions=True)
    for cn in ["Daily Production Output", "Shade-wise Output (KG)", "Production by QC Status"]:
        for nm in frappe.get_all("Dashboard Chart", filters={"chart_name": cn}, pluck="name"):
            frappe.delete_doc("Dashboard Chart", nm, force=1, ignore_permissions=True)
    if frappe.db.exists("Workspace", "Masterbatch"):
        frappe.delete_doc("Workspace", "Masterbatch", force=1, ignore_permissions=True)
    frappe.db.commit()

    card_defs = [
        {"label": "Total Batches", "document_type": "Batch Production Sheet", "function": "Count", "filters_json": f_batch},
        {"label": "Total Output (KG)", "document_type": "Batch Production Sheet", "function": "Sum",
         "aggregate_function_based_on": "actual_output_kg", "filters_json": f_batch},
        {"label": "Sales Orders", "document_type": "Sales Order", "function": "Count", "filters_json": f_so},
        {"label": "Purchase Orders", "document_type": "Purchase Order", "function": "Count", "filters_json": f_po},
    ]
    card_names = []
    for c in card_defs:
        try:
            doc = frappe.new_doc("Number Card")
            doc.update(c)
            doc.is_public = 1
            doc.insert(ignore_permissions=True)
            card_names.append(doc.name)
        except Exception as e:
            print(f"  card skip {c['label']}: {e}")

    chart_defs = [
        {"chart_name": "Daily Production Output", "chart_type": "Sum", "document_type": "Batch Production Sheet",
         "based_on": "production_date", "value_based_on": "actual_output_kg", "timespan": "Last Month",
         "time_interval": "Daily", "type": "Line", "filters_json": f_batch},
        {"chart_name": "Shade-wise Output (KG)", "chart_type": "Group By", "document_type": "Batch Production Sheet",
         "group_by_based_on": "shade_code", "group_by_type": "Sum", "aggregate_function_based_on": "actual_output_kg",
         "type": "Bar", "filters_json": f_batch},
        {"chart_name": "Production by QC Status", "chart_type": "Group By", "document_type": "Batch Production Sheet",
         "group_by_based_on": "qc_status", "group_by_type": "Count", "type": "Donut", "filters_json": f_batch},
    ]
    chart_names = []
    for c in chart_defs:
        try:
            doc = frappe.new_doc("Dashboard Chart")
            doc.update(c)
            doc.is_public = 1
            doc.insert(ignore_permissions=True)
            chart_names.append(doc.name)
        except Exception as e:
            print(f"  chart skip {c['chart_name']}: {e}")
    frappe.db.commit()

    ws = frappe.new_doc("Workspace")
    ws.title = "Masterbatch"
    ws.label = "Masterbatch"
    ws.module = "Masterbatch"
    ws.public = 1
    ws.icon = "manufacturing"

    shortcuts = [
        ("Batch Production Sheet", "Batch Production Sheet", "DocType", "#7B2D8B"),
        ("Shade Code", "Shade Code", "DocType", "#318AD8"),
        ("Lab Formulation", "Lab Formulation", "DocType", "#29CD42"),
        ("Production Summary", "Production Summary", "Report", "#FFC107"),
        ("RM Consumption", "Raw Material Consumption", "Report", "#FF5858"),
        ("Shade-wise Production", "Shade-wise Production", "Report", "#00BCD4"),
    ]
    for label, link_to, typ, color in shortcuts:
        ws.append("shortcuts", {"label": label, "link_to": link_to, "type": typ, "color": color})
    for nm in card_names:
        ws.append("number_cards", {"number_card_name": nm, "label": nm})
    for nm in chart_names:
        ws.append("charts", {"chart_name": nm, "label": nm})

    blocks = []
    blocks.append({"id": h(), "type": "header",
                   "data": {"text": "<span><b>Capital Colours — Masterbatch Manufacturing</b></span>", "col": 12}})
    for nm in card_names:
        blocks.append({"id": h(), "type": "number_card", "data": {"number_card_name": nm, "col": 3}})
    if len(chart_names) >= 1:
        blocks.append({"id": h(), "type": "chart", "data": {"chart_name": chart_names[0], "col": 12}})
    if len(chart_names) >= 2:
        blocks.append({"id": h(), "type": "chart", "data": {"chart_name": chart_names[1], "col": 8}})
    if len(chart_names) >= 3:
        blocks.append({"id": h(), "type": "chart", "data": {"chart_name": chart_names[2], "col": 4}})
    blocks.append({"id": h(), "type": "header", "data": {"text": "<span><b>Quick Links</b></span>", "col": 12}})
    for label, link_to, typ, color in shortcuts:
        blocks.append({"id": h(), "type": "shortcut", "data": {"shortcut_name": label, "col": 4}})

    ws.content = json.dumps(blocks)
    ws.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"OK cards={card_names} charts={chart_names}")


def debug_render_cc():
    import frappe, traceback
    frappe.set_user("Administrator")
    from werkzeug.test import EnvironBuilder
    from werkzeug.wrappers import Request
    frappe.local.request = Request(EnvironBuilder(path="/capital-colours", method="GET").get_environ())
    frappe.local.form_dict = frappe._dict()
    try:
        from frappe.website.page_renderers.template_page import TemplatePage
        tp = TemplatePage(path="capital-colours", http_status_code=200)
        print("can_render:", tp.can_render())
        resp = tp.render()
        print("rendered OK, status", getattr(resp, "status_code", "?"))
    except Exception:
        traceback.print_exc()


def create_lab_formulations():
    """Create approved Lab Formulations from the BOM recipes and link every batch."""
    frappe.set_user("Administrator")
    fg_shade = {fg[0]: fg[3] for fg in FINISHED_GOODS}
    fg_name = {fg[0]: fg[1] for fg in FINISHED_GOODS}

    created = 0
    for fg_item, recipe in BOMS.items():
        fno = "LF-" + fg_item
        if frappe.db.exists("Lab Formulation", fno):
            continue
        doc = frappe.new_doc("Lab Formulation")
        doc.formulation_no = fno
        doc.shade_code = fg_shade.get(fg_item)
        doc.finished_item = fg_item
        doc.date = add_days(today(), -45)
        doc.batch_size_kg = 100
        doc.approved_by = "Administrator"
        doc.remarks = f"Approved lab recipe for {fg_name.get(fg_item, fg_item)}"
        for rm, pct in recipe:
            doc.append("formulation_items", {"item_code": rm, "qty_per_100kg": pct, "uom": "KG"})
        doc.insert(ignore_permissions=True)
        doc.submit()
        created += 1
    frappe.db.commit()

    linked = 0
    for b in frappe.get_all("Batch Production Sheet", fields=["name", "finished_item"]):
        fno = "LF-" + (b.finished_item or "")
        if frappe.db.exists("Lab Formulation", fno):
            frappe.db.set_value("Batch Production Sheet", b.name, "formulation_no", fno, update_modified=False)
            linked += 1
    frappe.db.commit()
    print(f"formulations created={created}, batches linked={linked}")


def add_formcost_shortcut():
    import json
    frappe.set_user("Administrator")
    ws = frappe.get_doc("Workspace", "Masterbatch")
    if not any((s.link_to == "Formulation Cost") for s in ws.shortcuts):
        ws.append("shortcuts", {"label": "Formulation Cost", "link_to": "Formulation Cost",
                                "type": "Report", "color": "#9C27B0"})
        content = json.loads(ws.content or "[]")
        content.append({"id": frappe.generate_hash(length=10), "type": "shortcut",
                        "data": {"shortcut_name": "Formulation Cost", "col": 4}})
        ws.content = json.dumps(content)
        ws.save(ignore_permissions=True)
        frappe.db.commit()
    print("workspace shortcut added")


def create_flow_examples():
    """Create real example transactions so stock actually moves: PR in, Manufacture, Delivery out."""
    from frappe.utils import today, add_days
    frappe.set_user("Administrator")
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    abbr = frappe.db.get_value("Company", company, "abbr")
    wh_src = f"Stores - {abbr}"
    wh_fg = f"Finished Goods - {abbr}"
    out = {}

    # 1) Purchase Receipt from first submitted PO  (raw material INWARD)
    try:
        po = frappe.get_all("Purchase Order", filters={"docstatus": 1}, limit=1, pluck="name")
        if po and not frappe.get_all("Purchase Receipt", filters={"docstatus": 1}, limit=1):
            from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
            pr = make_purchase_receipt(po[0])
            pr.set_posting_time = 1
            pr.posting_date = add_days(today(), -8)
            for it in pr.items:
                it.warehouse = wh_src
            pr.insert(ignore_permissions=True)
            pr.submit()
            out["purchase_receipt"] = pr.name
    except Exception as e:
        out["pr_error"] = str(e)
    frappe.db.commit()

    # 2) Manufacture Stock Entries for recent batches (RM CONSUMED, FG PRODUCED)
    from masterbatch.masterbatch.doctype.batch_production_sheet.batch_production_sheet import make_stock_entry
    made = []
    batches = frappe.get_all("Batch Production Sheet",
                             filters={"docstatus": 1, "stock_entry": ["is", "not set"]},
                             fields=["name", "finished_item"], order_by="production_date desc", limit=10)
    for b in batches:
        try:
            se = make_stock_entry(b.name)
            made.append((b.finished_item, se))
        except Exception as e:
            out.setdefault("mfg_errors", []).append(f"{b.name}: {e}")
    out["manufacture_entries"] = len(made)
    frappe.db.commit()

    # 3) Delivery Note for a produced item (finished goods OUTWARD)
    try:
        if not frappe.get_all("Delivery Note", filters={"docstatus": 1}, limit=1):
            deliver = None
            for fi, se in made:
                qty = frappe.db.get_value("Bin", {"item_code": fi, "warehouse": wh_fg}, "actual_qty") or 0
                if qty and qty > 60:
                    deliver = (fi, qty)
                    break
            if deliver:
                dn = frappe.new_doc("Delivery Note")
                dn.customer = "Vivid Plastics"
                dn.company = company
                dn.set_posting_time = 1
                dn.posting_date = add_days(today(), -2)
                dn.append("items", {"item_code": deliver[0], "qty": 50, "warehouse": wh_fg, "uom": "KG"})
                dn.insert(ignore_permissions=True)
                dn.submit()
                out["delivery_note"] = dn.name
    except Exception as e:
        out["dn_error"] = str(e)
    frappe.db.commit()
    print(out)


def create_delivery_example():
    from frappe.utils import today
    frappe.set_user("Administrator")
    if frappe.get_all("Delivery Note", filters={"docstatus": 1}, limit=1):
        print("delivery already exists")
        return
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    abbr = frappe.db.get_value("Company", company, "abbr")
    wh_fg = f"Finished Goods - {abbr}"
    bins = frappe.db.sql(
        "SELECT item_code, actual_qty FROM `tabBin` WHERE warehouse=%s AND actual_qty>60 ORDER BY actual_qty DESC LIMIT 1",
        wh_fg, as_dict=True)
    if not bins:
        print("no FG stock available")
        return
    item = bins[0].item_code
    dn = frappe.new_doc("Delivery Note")
    dn.customer = "Vivid Plastics"
    dn.company = company
    dn.posting_date = today()
    dn.append("items", {"item_code": item, "qty": 50, "warehouse": wh_fg, "uom": "KG"})
    dn.insert(ignore_permissions=True)
    dn.submit()
    frappe.db.commit()
    print("delivery_note", dn.name, "item", item)
