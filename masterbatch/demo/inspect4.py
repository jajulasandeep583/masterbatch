import frappe, json

def go():
    frappe.set_user("Administrator")
    from frappe.desk.desktop import get_workspace_sidebar_items
    items = get_workspace_sidebar_items().get("pages", [])
    print("SIDEBAR PAGES COUNT:", len(items))
    for p in items:
        if p.get("name") in ("Masterbatch",) or p.get("module")=="Masterbatch":
            print("MASTERBATCH ENTRY:", json.dumps({k:p.get(k) for k in ["name","title","icon","public","module","app","parent_page","is_hidden","sequence_id"]}, default=str))
    # show the app grouping if present
    apps = set(p.get("app") for p in items)
    print("APPS referenced by sidebar pages:", apps)
    # Workspace meta has app field?
    meta = frappe.get_meta("Workspace")
    print("Workspace has 'app' field:", bool(meta.get_field("app")))
    print("Workspace fields:", [f.fieldname for f in meta.fields if f.fieldname in ("app","module","icon","indicator_color","public","for_user","parent_page","is_hidden","hide_custom","sequence_id")])
    # Module Def
    if frappe.db.exists("Module Def","Masterbatch"):
        md = frappe.get_doc("Module Def","Masterbatch")
        print("Module Def Masterbatch: app=",md.app_name," restrict_to_domain=",md.restrict_to_domain)
