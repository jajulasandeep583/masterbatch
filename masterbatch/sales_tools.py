import frappe
from frappe.utils import today, add_days, flt

from masterbatch.warehouse_utils import get_default_company, get_stores_warehouse


@frappe.whitelist()
def get_item_qty(item_code, warehouse=None):
    """Available (actual) stock for an item — at a warehouse if given, else across all warehouses."""
    if not item_code:
        return 0
    if warehouse:
        return flt(frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty"))
    return flt(frappe.db.sql(
        "SELECT COALESCE(SUM(actual_qty), 0) FROM `tabBin` WHERE item_code = %s", item_code)[0][0])


def _find_formulation(finished_item):
    return frappe.db.get_value("Lab Formulation", {"finished_item": finished_item, "docstatus": 1}, "name") \
        or frappe.db.get_value("Lab Formulation", {"finished_item": finished_item}, "name")


@frappe.whitelist()
def make_raw_material_request(sales_order):
    """Explode each ordered item's recipe into raw materials and raise a DRAFT Purchase
    Material Request the user can review / edit before submitting."""
    so = frappe.get_doc("Sales Order", sales_order)

    agg = {}
    missing = []
    for it in so.items:
        formulation = _find_formulation(it.item_code)
        if not formulation:
            missing.append(it.item_code)
            continue
        lf = frappe.get_doc("Lab Formulation", formulation)
        for r in lf.formulation_items:
            qty = (flt(r.qty_per_100kg) / 100.0) * flt(it.qty)
            agg[r.item_code] = agg.get(r.item_code, 0) + qty

    if not agg:
        frappe.throw("No recipe (Lab Formulation) found for the ordered items, so there are "
                     "no raw materials to request.")

    company = so.company or get_default_company()
    warehouse = get_stores_warehouse(company)
    sched = add_days(today(), 7)

    mr = frappe.new_doc("Material Request")
    mr.material_request_type = "Purchase"
    mr.company = company
    mr.transaction_date = today()
    mr.schedule_date = sched
    for item_code, qty in agg.items():
        mr.append("items", {
            "item_code": item_code,
            "qty": round(qty, 3),
            "schedule_date": sched,
            "warehouse": warehouse,
        })
    mr.insert(ignore_permissions=True)

    if missing:
        frappe.msgprint("No recipe for: " + ", ".join(missing) + " — they were skipped.",
                        indicator="orange", alert=True)
    return mr.name
