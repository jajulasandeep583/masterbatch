import frappe

def go():
    gs = frappe.get_doc("GST Settings")
    print("GST sandbox_mode:", gs.sandbox_mode, "enable_api:", gs.enable_api)
    print("Company GSTIN:", frappe.db.get_value("Company","MasterBatch","gstin"))
    for dt in ["Sales Invoice","Purchase Invoice","Payment Entry","Quotation",
               "Supplier Quotation","Request for Quotation","Journal Entry","Customer","Supplier"]:
        print(" ", dt, "=", frappe.db.count(dt, {"docstatus":1}) if dt not in ("Customer","Supplier") else frappe.db.count(dt))
    print("Default SI print format:", frappe.db.get_value("Property Setter","Sales Invoice-main-default_print_format","value"))
    print("Default PI print format:", frappe.db.get_value("Property Setter","Purchase Invoice-main-default_print_format","value"))
    print("Masterbatch workspace public/icon:", frappe.db.get_value("Workspace","Masterbatch",["public","icon"]))
    print("Apps installed:", frappe.get_installed_apps())
