import frappe

def go():
    frappe.set_user("Administrator")
    try:
        from frappe.apps import get_apps
        apps = get_apps()
        print("APPS ON LAUNCHER:")
        for a in apps:
            print("  ", a.get("name"), "| title=", a.get("title"), "| logo=", a.get("logo"), "| route=", a.get("route"))
        print("masterbatch present:", any(a.get("name")=="masterbatch" for a in apps))
    except Exception as e:
        print("get_apps err:", e)
