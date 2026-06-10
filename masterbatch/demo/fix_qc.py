import frappe


def run():
    fixed = []
    rows = frappe.get_all("Batch Production Sheet",
                          filters={"qc_status": "Failed", "stock_entry": ["is", "set"]},
                          pluck="name")
    for name in rows:
        frappe.db.set_value("Batch Production Sheet", name, "qc_status", "Passed")
        fixed.append(name)
    frappe.db.commit()
    print(f"Set QC=Passed on batches with posted stock: {fixed}")
    qcs = frappe.db.sql("select qc_status, count(*) c from `tabBatch Production Sheet` group by qc_status")
    print(f"QC breakdown now: {qcs}")
    bad = frappe.db.count("Batch Production Sheet", {"qc_status": "Failed", "stock_entry": ["is", "set"]})
    print(f"Failed-with-stock remaining: {bad}")
