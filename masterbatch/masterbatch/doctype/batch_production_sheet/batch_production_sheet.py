import frappe
from frappe.model.document import Document


class BatchProductionSheet(Document):
    def validate(self):
        if self.actual_output_kg and self.planned_qty:
            total_input = sum(r.qty_consumed or 0 for r in self.consumption_items)
            self.rejection_kg = total_input - self.actual_output_kg if total_input > self.actual_output_kg else 0

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

    company = frappe.db.get_single_value("Global Defaults", "default_company")
    abbr = frappe.db.get_value("Company", company, "abbr")
    wh_src = f"Stores - {abbr}"
    wh_fg = f"Finished Goods - {abbr}"

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
    se.insert(ignore_permissions=True)
    se.submit()
    doc.db_set("stock_entry", se.name)
    return se.name
