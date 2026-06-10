import frappe

def go():
    print("=== Sales Invoice print formats ===")
    for p in frappe.get_all("Print Format", filters={"doc_type":"Sales Invoice"}, fields=["name","standard","disabled"]):
        print("  ", p.name, "std=",p.standard, "disabled=",p.disabled)
    print("=== Purchase Invoice print formats ===")
    for p in frappe.get_all("Print Format", filters={"doc_type":"Purchase Invoice"}, fields=["name","standard"]):
        print("  ", p.name)
    print("=== Masterbatch workspace ===")
    if frappe.db.exists("Workspace","Masterbatch"):
        w = frappe.get_doc("Workspace","Masterbatch")
        print("  public=",w.public,"icon=",w.icon,"module=",w.module,"for_user=",w.for_user,
              "parent=",w.parent_page,"is_hidden=",w.get("is_hidden"),"sequence=",w.get("sequence_id"),"title=",w.title)
    else:
        print("  NO Masterbatch workspace")
    print("=== All public workspaces (sidebar order) ===")
    for w in frappe.get_all("Workspace", filters={"public":1}, fields=["name","icon","sequence_id","parent_page"], order_by="sequence_id asc"):
        print("  ", w.sequence_id, w.name, "icon=",w.icon, "parent=",w.parent_page)
