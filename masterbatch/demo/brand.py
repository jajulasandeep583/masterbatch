import frappe

def brand_workspace():
    w = frappe.get_doc("Workspace", "Masterbatch")
    w.public = 1
    w.is_hidden = 0
    w.icon = "manufacturing"
    if w.meta.get_field("indicator_color"):
        w.indicator_color = "purple"
    w.sequence_id = 1
    w.app = "masterbatch"
    w.save(ignore_permissions=True)
    frappe.db.commit()
    print("Workspace branded: icon=%s color=%s seq=%s app=%s" % (
        w.icon, w.get("indicator_color"), w.sequence_id, w.app))
