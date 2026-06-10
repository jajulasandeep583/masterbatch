import frappe

def pnl():
    accs = frappe.get_all("Account", filters={"company":"MasterBatch","is_group":0},
                          fields=["name","root_type"])
    rt = {a.name:a.root_type for a in accs}
    gl = frappe.get_all("GL Entry", filters={"company":"MasterBatch","is_cancelled":0},
                        fields=["account","debit","credit"], limit_page_length=0)
    inc=exp=0.0
    for g in gl:
        r = rt.get(g.account)
        if r=="Income": inc += (g.credit-g.debit)
        elif r=="Expense": exp += (g.debit-g.credit)
    print("Income:", round(inc), "Expense:", round(exp), "Net Profit:", round(inc-exp))
    for dt in ["Sales Invoice","Purchase Invoice","Payment Entry","Quotation",
               "Supplier Quotation","Request for Quotation","POS Invoice","Journal Entry"]:
        print(dt, "=", frappe.db.count(dt, {"docstatus":1}))

def breakdown():
    accs = frappe.get_all("Account", filters={"company":"MasterBatch","is_group":0},
                          fields=["name","root_type"])
    rt = {a.name:a.root_type for a in accs}
    gl = frappe.get_all("GL Entry", filters={"company":"MasterBatch","is_cancelled":0},
                        fields=["account","debit","credit"], limit_page_length=0)
    agg={}
    for g in gl:
        if rt.get(g.account)=="Expense":
            agg[g.account]=agg.get(g.account,0)+(g.debit-g.credit)
    for k,v in sorted(agg.items(), key=lambda x:x[1]):
        print(f"{round(v):>12}  {k}")
