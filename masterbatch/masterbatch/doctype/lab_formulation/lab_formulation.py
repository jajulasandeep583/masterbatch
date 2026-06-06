import frappe
from frappe.model.document import Document


class LabFormulation(Document):
    def on_submit(self):
        self.db_set("status", "Approved")
        frappe.msgprint(f"Formulation {self.formulation_no} approved and locked.")

    def on_cancel(self):
        self.db_set("status", "Draft")


@frappe.whitelist()
def make_bom(formulation):
    """Create (or link) an ERPNext Production BOM from an approved Lab Formulation."""
    doc = frappe.get_doc("Lab Formulation", formulation)

    if doc.bom and frappe.db.exists("BOM", doc.bom):
        return doc.bom

    # reuse an existing active BOM for this item if one already exists
    existing = frappe.db.get_value("BOM", {"item": doc.finished_item, "is_active": 1}, "name")
    if existing:
        doc.db_set("bom", existing)
        return existing

    size = doc.batch_size_kg or 100
    bom = frappe.new_doc("BOM")
    bom.item = doc.finished_item
    bom.quantity = size
    bom.uom = "KG"
    for it in doc.formulation_items:
        bom.append("items", {
            "item_code": it.item_code,
            "qty": round((it.qty_per_100kg / 100.0) * size, 3),
            "uom": "KG",
        })
    bom.insert(ignore_permissions=True)
    bom.submit()
    doc.db_set("bom", bom.name)
    return bom.name
