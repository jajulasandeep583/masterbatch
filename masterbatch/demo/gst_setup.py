import frappe

CODE_POINT = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def check_digit(gstin14):
    factor, total, mod = 1, 0, len(CODE_POINT)
    for ch in gstin14:
        d = factor * CODE_POINT.index(ch)
        d = (d // mod) + (d % mod)
        total += d
        factor = 2 if factor == 1 else 1
    return CODE_POINT[(mod - (total % mod)) % mod]

def build_gstin(state_code, idx):
    pan = "AAACM" + f"{1000+idx:04d}" + "C"   # 5 letters + 4 digits + 1 letter
    base = f"{state_code}{pan}1Z"
    return base + check_digit(base)

STATES = {"29": "Karnataka", "27": "Maharashtra", "33": "Tamil Nadu", "36": "Telangana", "07": "Delhi"}
PIN = {"29": "560001", "27": "400001", "33": "600001", "36": "500001", "07": "110001"}

def ensure_hsn(code, desc):
    if not frappe.db.exists("GST HSN Code", code):
        try:
            frappe.get_doc({"doctype": "GST HSN Code", "hsn_code": code, "description": desc}).insert(ignore_permissions=True)
        except Exception as e:
            print("hsn err", code, e)

def upsert_address(title, party_dt, party, state_code, line1="Plot 1, Industrial Area"):
    state = STATES[state_code]
    gstin = build_gstin(state_code, abs(hash(party)) % 9000)
    name = title + "-Billing-" + state
    existing = frappe.get_all("Address", filters=[["Dynamic Link","link_name","=",party]], pluck="name")
    if existing:
        addr = frappe.get_doc("Address", existing[0])
    else:
        addr = frappe.new_doc("Address")
        addr.append("links", {"link_doctype": party_dt, "link_name": party})
    addr.address_title = title
    addr.address_line1 = line1
    addr.city = state
    addr.state = state
    addr.country = "India"
    addr.pincode = PIN[state_code]
    addr.gstin = gstin
    addr.gst_category = "Registered Regular"
    addr.address_type = "Billing"
    addr.save(ignore_permissions=True)
    return gstin

def setup_gst():
    # 1. Company
    comp = frappe.get_doc("Company", "MasterBatch")
    comp_gstin = build_gstin("29", 1)
    comp.gstin = comp_gstin
    comp.gst_category = "Registered Regular"
    comp.save(ignore_permissions=True)
    print("Company GSTIN set:", comp_gstin)
    # company address
    upsert_address("MasterBatch HO", "Company", "MasterBatch", "29")
    # 2. GST settings keep sandbox; relax HSN validation to avoid blocking demo
    gs = frappe.get_doc("GST Settings")
    gs.sandbox_mode = 1
    gs.enable_api = 1
    gs.validate_hsn_code = 0
    gs.save(ignore_permissions=True)
    print("GST Settings: sandbox=1, enable_api=1, validate_hsn=0")
    # 3. HSN + items
    ensure_hsn("32041790", "Synthetic organic colouring matter")
    ensure_hsn("39039090", "Polymers of styrene / masterbatch")
    for it in frappe.get_all("Item", pluck="name"):
        doc = frappe.get_doc("Item", it)
        if not doc.get("gst_hsn_code"):
            doc.gst_hsn_code = "39039090"
            doc.save(ignore_permissions=True)
    print("HSN set on items")
    # 4. Customers: assign GSTIN + address; alternate in-state/out-state
    custs = frappe.get_all("Customer", pluck="name")
    for i, c in enumerate(custs):
        sc = "29" if i % 2 == 0 else "27"
        g = upsert_address(c, "Customer", c, sc)
        cd = frappe.get_doc("Customer", c)
        cd.gstin = g
        cd.gst_category = "Registered Regular"
        cd.save(ignore_permissions=True)
    print(f"Configured {len(custs)} customers (alt in/out state)")
    # 5. Suppliers
    sups = frappe.get_all("Supplier", pluck="name")
    for i, s in enumerate(sups):
        sc = "29" if i % 2 == 0 else "33"
        g = upsert_address(s, "Supplier", s, sc)
        sd = frappe.get_doc("Supplier", s)
        sd.gstin = g
        sd.gst_category = "Registered Regular"
        sd.save(ignore_permissions=True)
    print(f"Configured {len(sups)} suppliers")
    frappe.db.commit()
    print("DONE setup_gst")

def inspect2():
    print("FISCAL YEARS:", frappe.get_all("Fiscal Year", fields=["name","year_start_date","year_end_date"]))
    print("DEFAULT PRICE LISTS:", frappe.get_all("Price List", filters={"enabled":1}, pluck="name"))
    print("CASH/BANK ACCOUNTS:", frappe.get_all("Account", filters={"company":"MasterBatch","account_type":["in",["Cash","Bank"]],"is_group":0}, pluck="name"))
    print("INCOME ACC:", frappe.get_all("Account", filters={"company":"MasterBatch","root_type":"Income","is_group":0}, pluck="name")[:10])
    print("EXPENSE ACC:", frappe.get_all("Account", filters={"company":"MasterBatch","root_type":"Expense","is_group":0}, pluck="name")[:30])
    items = frappe.get_all("Item", fields=["name","item_name","is_stock_item","is_sales_item","is_purchase_item","standard_rate","valuation_rate"], limit=8)
    for it in items: print("ITEM:", it)
    print("DEFAULT WAREHOUSE:", frappe.get_all("Warehouse", filters={"company":"MasterBatch","is_group":0}, pluck="name")[:10])
    print("SI EXISTING:", frappe.get_all("Sales Invoice", fields=["name","customer","grand_total","posting_date","docstatus"]))
