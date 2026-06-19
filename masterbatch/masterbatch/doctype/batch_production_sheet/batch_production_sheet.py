import frappe
from frappe.model.document import Document
from frappe.utils import flt

from masterbatch.warehouse_utils import get_default_company, get_stores_warehouse, get_fg_warehouse


def evaluate_qc_status(row):
    """Pass/Fail for a QC row from its result vs the parameter's limits (server-side authority)."""
    result = row.result
    if result is None or str(result).strip() == "":
        return row.status or "Pass"
    et = row.evaluation_type or "Range"
    if et == "Text Match":
        return "Pass" if str(result).strip().lower() == str(row.target_text or "").strip().lower() else "Fail"
    try:
        val = float(str(result).strip())
    except (TypeError, ValueError):
        return "Fail"
    mn = row.min_value or 0
    mx = row.max_value or 0
    if et == "Minimum":
        return "Pass" if val >= mn else "Fail"
    if et == "Maximum":
        return "Pass" if val <= mx else "Fail"
    return "Pass" if (mn <= val <= mx) else "Fail"


class BatchProductionSheet(Document):
    def validate(self):
        if self.actual_output_kg and self.planned_qty:
            total_input = sum(r.qty_consumed or 0 for r in self.consumption_items)
            self.rejection_kg = total_input - self.actual_output_kg if total_input > self.actual_output_kg else 0
        # auto Pass/Fail each QC parameter from its result and the master's limits
        for row in (self.qc_parameters or []):
            row.status = evaluate_qc_status(row)

    def before_submit(self):
        # don't let a batch submit if a raw material isn't actually in stock —
        # replace the short item with an available one (or add stock) first.
        self.check_raw_material_stock()

    def check_raw_material_stock(self):
        wh_src = get_stores_warehouse()
        if not wh_src:
            return  # no stores warehouse configured on this site — let the stock entry surface it
        required, names = {}, {}
        for r in self.consumption_items:
            if r.item_code and r.qty_consumed:
                required[r.item_code] = required.get(r.item_code, 0) + flt(r.qty_consumed)
                names[r.item_code] = r.item_name or r.item_code
        short = []
        for item_code, need in required.items():
            avail = flt(frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": wh_src}, "actual_qty"))
            if avail < need:
                short.append((item_code, names.get(item_code), need, avail))
        if short:
            rows = "".join(
                "<li><b>{n}</b> ({c}): need {need:g} KG, only <b>{avail:g} KG</b> available</li>".format(
                    n=n or c, c=c, need=need, avail=avail)
                for c, n, need, avail in short
            )
            frappe.throw(
                "These raw materials don't have enough stock in <b>{wh}</b>:<ul>{rows}</ul>"
                "Replace the short item(s) in the <b>Raw Material Consumption</b> table with an "
                "available raw material (or add stock), then submit the batch again.".format(wh=wh_src, rows=rows),
                title="Insufficient Raw Material Stock",
            )

    def on_submit(self):
        frappe.msgprint(f"Batch {self.batch_no} submitted. Use 'Create Stock Entry' to post stock "
                        f"(consume raw materials, produce finished goods).")


@frappe.whitelist()
def find_formulation(finished_item):
    """Return the approved Lab Formulation for a finished item (so the batch can auto-load its recipe)."""
    return frappe.db.get_value(
        "Lab Formulation",
        {"finished_item": finished_item, "docstatus": 1},
        "name",
    ) or frappe.db.get_value("Lab Formulation", {"finished_item": finished_item}, "name")


@frappe.whitelist()
def get_formulation_items(formulation, planned_qty=0):
    """Return the recipe rows, scaled to the planned batch quantity, to auto-fill the batch sheet."""
    planned_qty = float(planned_qty or 0)
    lf = frappe.get_doc("Lab Formulation", formulation)
    rows = []
    for it in lf.formulation_items:
        plan = round((it.qty_per_100kg / 100.0) * planned_qty, 3) if planned_qty else it.qty_per_100kg
        rows.append({
            "item_code": it.item_code,
            "item_name": it.item_name or frappe.db.get_value("Item", it.item_code, "item_name"),
            "planned_qty": plan,
            "qty_consumed": plan,
            "uom": "KG",
        })
    return {"finished_item": lf.finished_item, "shade_code": lf.shade_code, "items": rows}


@frappe.whitelist()
def make_stock_entry(batch):
    """Post real stock for a batch: consume raw materials, produce the finished masterbatch."""
    doc = frappe.get_doc("Batch Production Sheet", batch)
    if doc.stock_entry and frappe.db.exists("Stock Entry", doc.stock_entry):
        return doc.stock_entry
    if not doc.consumption_items:
        frappe.throw("No raw-material consumption rows to post.")

    # Finished-goods quality gate: only QC-passed batches enter sellable stock
    if (doc.qc_status or "").strip() != "Passed":
        frappe.throw(
            f"Batch {doc.batch_no}: finished goods can move to sellable stock only after "
            f"QC is <b>Passed</b> (current QC status: {doc.qc_status or 'Pending'})."
        )

    company = get_default_company()
    wh_src = get_stores_warehouse(company)
    wh_fg = get_fg_warehouse(company, doc.finished_item)
    if not wh_src or not wh_fg:
        frappe.throw("Could not determine a source (stores) or finished-goods warehouse for "
                     f"company {company}. Please configure warehouses for this company first.")

    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Manufacture"
    se.company = company
    se.posting_date = doc.production_date
    for r in doc.consumption_items:
        if r.qty_consumed:
            se.append("items", {"item_code": r.item_code, "qty": r.qty_consumed,
                                "s_warehouse": wh_src, "uom": "KG"})
    se.append("items", {"item_code": doc.finished_item, "qty": doc.actual_output_kg,
                        "t_warehouse": wh_fg, "is_finished_item": 1, "uom": "KG"})
    # rejection becomes sellable scrap stock under the chosen rejection item
    if (doc.rejection_kg or 0) > 0 and doc.rejection_item:
        se.append("items", {"item_code": doc.rejection_item, "qty": doc.rejection_kg,
                            "t_warehouse": wh_fg, "type": "Scrap",
                            "allow_zero_valuation_rate": 1, "uom": "KG"})
    se.insert(ignore_permissions=True)
    se.submit()
    doc.db_set("stock_entry", se.name)
    return se.name
