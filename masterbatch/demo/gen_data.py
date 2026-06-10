import frappe, random
from frappe.utils import add_days, getdate

COMPANY = "MasterBatch"
random.seed(42)

# 12 months ending Jun 2026
MONTHS = [(2025,7),(2025,8),(2025,9),(2025,10),(2025,11),(2025,12),
          (2026,1),(2026,2),(2026,3),(2026,4),(2026,5),(2026,6)]

def rdate(my):
    y,m = my
    day = random.randint(1,26) if not (y==2026 and m==6) else random.randint(1,8)
    return getdate(f"{y}-{m:02d}-{day:02d}")

def ensure_fiscal_years():
    for name,s,e in [("2025-2026","2025-04-01","2026-03-31")]:
        if not frappe.db.exists("Fiscal Year", name):
            frappe.get_doc({"doctype":"Fiscal Year","year":name,"year_start_date":s,"year_end_date":e}).insert(ignore_permissions=True)
            print("Created FY", name)
    print("FYs:", frappe.get_all("Fiscal Year", pluck="name"))

EXP_ITEMS = [
    ("EXP-RAWMAT","Pigments & Resins (Raw Material)","Cost of Goods Sold - MB"),
    ("EXP-PACK","Packaging Material","Cost of Goods Sold - MB"),
    ("EXP-FREIGHT","Freight & Logistics","Freight and Forwarding Charges - MB"),
    ("EXP-POWER","Power & Fuel","Utility Expenses - MB"),
    ("EXP-CONSUM","Factory Consumables","Miscellaneous Expenses - MB"),
]

def ensure_expense_items():
    grp = frappe.db.get_value("Item Group", {"name":"Services"}, "name") or frappe.get_all("Item Group", filters={"is_group":0}, pluck="name")[0]
    for code,nm,acc in EXP_ITEMS:
        if frappe.db.exists("Item", code):
            it = frappe.get_doc("Item", code)
        else:
            it = frappe.get_doc({"doctype":"Item","item_code":code,"item_name":nm,"item_group":grp,
                "is_stock_item":0,"is_purchase_item":1,"is_sales_item":0,"gst_hsn_code":"39039090"})
            it.insert(ignore_permissions=True)
        if it.item_defaults:
            it.item_defaults[0].company=COMPANY
            it.item_defaults[0].expense_account=acc
        else:
            it.append("item_defaults",{"company":COMPANY,"expense_account":acc})
        it.save(ignore_permissions=True)
    print("Expense items ready")

def party_address(dt, party):
    addrs = frappe.get_all("Dynamic Link", filters={"link_doctype":dt,"link_name":party,"parenttype":"Address"}, pluck="parent")
    return addrs[0] if addrs else None

def party_state_code(party_gstin):
    return party_gstin[:2] if party_gstin else "29"

def add_taxes_from_template(doc, tmpl):
    tdoc = frappe.get_doc(doc.meta.get_field("taxes_and_charges").options, tmpl)
    doc.taxes_and_charges = tmpl
    doc.set("taxes", [])
    for t in tdoc.taxes:
        row = {"charge_type":t.charge_type,"account_head":t.account_head,"description":t.description,
               "rate":t.rate,"cost_center":t.cost_center}
        if t.get("gst_tax_type"): row["gst_tax_type"]=t.get("gst_tax_type")
        doc.append("taxes", row)

def gen_sales_invoices(n=60):
    sales_items = frappe.get_all("Item", filters={"is_sales_item":1,"is_stock_item":1}, fields=["name","valuation_rate"])
    custs = frappe.get_all("Customer", fields=["name","gstin"])
    comp_addr = party_address("Company", COMPANY)
    made=0
    for i in range(n):
        c = random.choice(custs)
        sc = party_state_code(c.gstin)
        tmpl = "Output GST In-state - MB" if sc=="29" else "Output GST Out-state - MB"
        try:
            si = frappe.new_doc("Sales Invoice")
            si.company = COMPANY
            si.customer = c.name
            si.set_posting_time = 1
            si.posting_date = rdate(random.choice(MONTHS))
            si.due_date = add_days(si.posting_date, 30)
            si.customer_address = party_address("Customer", c.name)
            si.company_address = comp_addr
            si.update_stock = 0
            for _ in range(random.randint(1,3)):
                it = random.choice(sales_items)
                rate = round((it.valuation_rate or 100)*random.uniform(1.4,1.8),0)
                si.append("items",{"item_code":it.name,"qty":random.choice([50,100,150,200,250,500]),"rate":rate})
            add_taxes_from_template(si, tmpl)
            si.insert(ignore_permissions=True)
            si.submit()
            made+=1
        except Exception as e:
            print("SI err:", str(e)[:160])
    frappe.db.commit()
    print("Sales Invoices created:", made)

def gen_purchase_invoices(n=40):
    sups = frappe.get_all("Supplier", fields=["name","gstin"])
    made=0
    for i in range(n):
        s = random.choice(sups)
        sc = party_state_code(s.gstin)
        tmpl = "Input GST In-state - MB" if sc=="29" else "Input GST Out-state - MB"
        try:
            pi = frappe.new_doc("Purchase Invoice")
            pi.company = COMPANY
            pi.supplier = s.name
            pi.set_posting_time = 1
            pi.posting_date = rdate(random.choice(MONTHS))
            pi.bill_no = "SUP-%d" % (1000+i)
            pi.bill_date = pi.posting_date
            pi.supplier_address = party_address("Supplier", s.name)
            pi.update_stock = 0
            for _ in range(random.randint(1,3)):
                code,nm,acc = random.choice(EXP_ITEMS)
                pi.append("items",{"item_code":code,"qty":random.choice([100,200,500,1000]),
                    "rate":round(random.uniform(40,400),0),"expense_account":acc})
            add_taxes_from_template(pi, tmpl)
            try:
                pi.insert(ignore_permissions=True)
                pi.submit()
            except Exception:
                frappe.db.rollback()
                alt = "Input GST Out-state - MB" if tmpl=="Input GST In-state - MB" else "Input GST In-state - MB"
                pi2 = frappe.copy_doc(pi)
                pi2.set("taxes", [])
                add_taxes_from_template(pi2, alt)
                pi2.insert(ignore_permissions=True)
                pi2.submit()
            made+=1
        except Exception as e:
            print("PI err:", str(e)[:160])
    frappe.db.commit()
    print("Purchase Invoices created:", made)

def gen_payments():
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
    made=0
    sis = frappe.get_all("Sales Invoice", filters={"docstatus":1,"outstanding_amount":[">",0]}, pluck="name")
    for nm in random.sample(sis, min(20,len(sis))):
        try:
            pe = get_payment_entry("Sales Invoice", nm)
            pe.paid_to = "SBI - MB"; pe.reference_no="RCPT-"+nm[-5:]; pe.reference_date=frappe.utils.nowdate()
            pe.insert(ignore_permissions=True); pe.submit(); made+=1
        except Exception as e:
            print("PE-SI err:", str(e)[:140])
    pis = frappe.get_all("Purchase Invoice", filters={"docstatus":1,"outstanding_amount":[">",0]}, pluck="name")
    for nm in random.sample(pis, min(12,len(pis))):
        try:
            pe = get_payment_entry("Purchase Invoice", nm)
            pe.paid_from = "SBI - MB"; pe.reference_no="PAY-"+nm[-5:]; pe.reference_date=frappe.utils.nowdate()
            pe.insert(ignore_permissions=True); pe.submit(); made+=1
        except Exception as e:
            print("PE-PI err:", str(e)[:140])
    frappe.db.commit()
    print("Payment Entries created:", made)

def gen_quotations(n=15):
    sales_items = frappe.get_all("Item", filters={"is_sales_item":1,"is_stock_item":1}, fields=["name","valuation_rate"])
    custs = frappe.get_all("Customer", pluck="name")
    made=0
    for i in range(n):
        try:
            q = frappe.new_doc("Quotation")
            q.quotation_to="Customer"; q.party_name=random.choice(custs); q.company=COMPANY
            q.transaction_date = rdate(random.choice(MONTHS))
            for _ in range(random.randint(1,3)):
                it=random.choice(sales_items)
                q.append("items",{"item_code":it.name,"qty":random.choice([100,200,500]),"rate":round((it.valuation_rate or 100)*1.6,0)})
            q.insert(ignore_permissions=True)
            if random.random()<0.7: q.submit()
            made+=1
        except Exception as e:
            print("QTN err:", str(e)[:140])
    frappe.db.commit()
    print("Quotations created:", made)

def gen_rfq_and_sq(num_rfq=3):
    sups = frappe.get_all("Supplier", pluck="name")
    for s in sups:
        if not frappe.db.get_value("Supplier", s, "email_id"):
            frappe.db.set_value("Supplier", s, "email_id", frappe.scrub(s)+"@example.com")
    made_rfq=made_sq=0
    for r in range(num_rfq):
        chosen_sups = random.sample(sups, 3)
        items = random.sample([x for x,_,_ in EXP_ITEMS],2)
        try:
            rfq=frappe.new_doc("Request for Quotation")
            rfq.company=COMPANY; rfq.transaction_date=rdate((2026,5))
            for s in chosen_sups:
                rfq.append("suppliers",{"supplier":s})
            for it in items:
                rfq.append("items",{"item_code":it,"qty":random.choice([500,1000]),"schedule_date":add_days(rfq.transaction_date,15),"warehouse":"Stores - MB","uom":"Nos","conversion_factor":1})
            rfq.insert(ignore_permissions=True); rfq.submit(); made_rfq+=1
            for s in chosen_sups:
                try:
                    sq=frappe.new_doc("Supplier Quotation")
                    sq.supplier=s; sq.company=COMPANY; sq.transaction_date=add_days(rfq.transaction_date,3)
                    for it in rfq.items:
                        sq.append("items",{"item_code":it.item_code,"qty":it.qty,
                            "rate":round(random.uniform(50,350),0),"request_for_quotation":rfq.name,
                            "schedule_date":it.schedule_date,"warehouse":"Stores - MB","uom":"Nos","conversion_factor":1})
                    sq.insert(ignore_permissions=True); sq.submit(); made_sq+=1
                except Exception as e:
                    print("SQ err:", str(e)[:160])
        except Exception as e:
            print("RFQ err:", str(e)[:160])
    frappe.db.commit()
    print("RFQ created:", made_rfq, "Supplier Quotations:", made_sq)

def _equity_opening_account():
    name = "Opening Stock Reserve - MB"
    if frappe.db.exists("Account", name):
        return name
    parent = (frappe.db.get_value("Account", {"company":COMPANY,"account_name":["like","%Reserves%"],"is_group":1}, "name")
              or frappe.db.get_value("Account", {"company":COMPANY,"account_name":["like","%Capital%"],"is_group":1}, "name")
              or frappe.db.get_value("Account", {"company":COMPANY,"root_type":"Liability","is_group":1,"parent_account":["in",["",None]]}, "name"))
    acc = frappe.get_doc({"doctype":"Account","account_name":"Opening Stock Reserve","company":COMPANY,
        "parent_account":parent,"root_type":"Liability","is_group":0}).insert(ignore_permissions=True)
    return acc.name

def fix_opening_stock_pnl():
    # reclassify net credit sitting in Stock Adjustment (from opening Material Receipts) out of P&L into equity
    sa = "Stock Adjustment - MB"
    rows = frappe.get_all("GL Entry", filters={"company":COMPANY,"account":sa,"is_cancelled":0},
                          fields=["debit","credit"], limit_page_length=0)
    net = sum(r.debit - r.credit for r in rows)  # negative => net credit
    if net >= 0:
        print("Stock Adjustment already non-negative:", round(net)); return
    amt = round(-net, 2)
    eq = _equity_opening_account()
    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"; je.company = COMPANY
    je.posting_date = getdate("2025-04-01")
    je.user_remark = "Reclassify opening stock value to equity (demo P&L cleanup)"
    je.append("accounts", {"account": sa, "debit_in_account_currency": amt})
    je.append("accounts", {"account": eq, "credit_in_account_currency": amt})
    je.insert(ignore_permissions=True); je.submit()
    frappe.db.commit()
    print(f"Reclassified {amt} from Stock Adjustment to {eq}")

def gen_expense_journals():
    plan = [("Salary - MB",250000,300000),("Office Rent - MB",90000,120000),
            ("Marketing Expenses - MB",30000,80000),("Telephone Expenses - MB",8000,15000),
            ("Travel Expenses - MB",20000,60000)]
    made=0
    for my in MONTHS:
        d = rdate(my)
        for acc,lo,hi in plan:
            amt = round(random.uniform(lo,hi),0)
            try:
                je = frappe.new_doc("Journal Entry")
                je.voucher_type="Journal Entry"; je.company=COMPANY
                je.set_posting_time=1; je.posting_date=d
                je.user_remark=f"{acc.split(' - ')[0]} for {my[0]}-{my[1]:02d}"
                je.append("accounts",{"account":acc,"debit_in_account_currency":amt})
                je.append("accounts",{"account":"SBI - MB","credit_in_account_currency":amt})
                je.insert(ignore_permissions=True); je.submit(); made+=1
            except Exception as e:
                print("JE err:", str(e)[:140])
    frappe.db.commit()
    print(f"Expense Journal Entries created: {made}")

def _ensure_pos_profile():
    name = "MasterBatch Retail POS"
    # set Cash mode account for company
    mop = frappe.get_doc("Mode of Payment", "Cash")
    if not any(a.company==COMPANY for a in mop.accounts):
        mop.append("accounts", {"company":COMPANY,"default_account":"Cash - MB"})
        mop.save(ignore_permissions=True)
    if frappe.db.exists("POS Profile", name):
        return name
    pp = frappe.new_doc("POS Profile")
    pp.name = name; pp.naming_series = "PP-"
    pp.company = COMPANY
    pp.warehouse = "Finished Goods - MB"
    pp.update_stock = 0
    pp.write_off_account = "Write Off - MB"
    pp.write_off_cost_center = frappe.db.get_value("Company", COMPANY, "cost_center")
    pp.append("payments", {"mode_of_payment":"Cash","default":1})
    pp.insert(ignore_permissions=True)
    return name

def _ensure_pos_opening(pp):
    today = frappe.utils.nowdate()
    for nm in frappe.get_all("POS Opening Entry", filters={"pos_profile":pp,"status":"Open","docstatus":1}, pluck="name"):
        d = frappe.get_doc("POS Opening Entry", nm)
        if str(d.period_start_date)[:10] == today:
            return nm
        d.cancel()
    poe = frappe.new_doc("POS Opening Entry")
    poe.posting_date = today
    poe.period_start_date = frappe.utils.now()
    poe.company = COMPANY
    poe.pos_profile = pp
    poe.user = frappe.session.user
    poe.append("balance_details", {"mode_of_payment":"Cash","opening_amount":0})
    poe.insert(ignore_permissions=True); poe.submit()
    return poe.name

def gen_pos(n=10):
    pp = _ensure_pos_profile()
    sales_items = frappe.get_all("Item", filters={"is_sales_item":1,"is_stock_item":1}, fields=["name","valuation_rate"])
    custs = [c for c in frappe.get_all("Customer", fields=["name","gstin"]) if (c.gstin or "29").startswith("29")]
    comp_addr = party_address("Company", COMPANY)
    made=0
    for i in range(n):
        c = random.choice(custs)
        try:
            si = frappe.new_doc("Sales Invoice")
            si.company=COMPANY; si.customer=c.name; si.is_pos=1; si.pos_profile=pp
            si.set_posting_time=1; si.posting_date=rdate(random.choice(MONTHS[-4:]))
            si.update_stock=0
            si.customer_address = party_address("Customer", c.name)
            si.company_address = comp_addr
            for _ in range(random.randint(1,2)):
                it=random.choice(sales_items)
                si.append("items",{"item_code":it.name,"qty":random.choice([10,20,50,100]),
                    "rate":round((it.valuation_rate or 100)*random.uniform(1.4,1.7),0)})
            add_taxes_from_template(si, "Output GST In-state - MB")
            si.append("payments",{"mode_of_payment":"Cash","amount":0})
            si.insert(ignore_permissions=True)
            si.payments[0].amount = si.grand_total
            si.paid_amount = si.grand_total
            si.save(ignore_permissions=True)
            si.submit(); made+=1
        except Exception as e:
            print("POS err:", str(e)[:160])
    frappe.db.commit()
    print(f"POS Invoices created: {made}")

def run_all():
    ensure_fiscal_years()
    ensure_expense_items()
    gen_sales_invoices(60)
    gen_purchase_invoices(40)
    gen_payments()
    gen_quotations(15)
    gen_rfq_and_sq(3)
    print("=== run_all done ===")
