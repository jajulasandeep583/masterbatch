import frappe
from frappe.model.document import Document

class LabFormulation(Document):
    def on_submit(self):
        frappe.msgprint(f"Formulation {self.formulation_no} approved and locked.")
