import frappe
from frappe.model.document import Document

class BatchProductionSheet(Document):
    def validate(self):
        if self.actual_output_kg and self.planned_qty:
            total_input = sum(r.qty_consumed or 0 for r in self.consumption_items)
            self.rejection_kg = total_input - self.actual_output_kg if total_input > self.actual_output_kg else 0

    def on_submit(self):
        frappe.msgprint(f"Batch {self.batch_no} submitted. Create Stock Entry from Work Order in ERPNext.")
