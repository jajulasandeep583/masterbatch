import frappe

def go():
    frappe.set_user("Administrator")
    si = frappe.get_all("Sales Invoice", filters={"docstatus":1,"grand_total":[">",0]}, pluck="name")[0]
    pi = frappe.get_all("Purchase Invoice", filters={"docstatus":1}, pluck="name")[0]
    for dt, nm, pf in [("Sales Invoice", si, "Capital Colours Tax Invoice"),
                       ("Purchase Invoice", pi, "Capital Colours Purchase Bill")]:
        try:
            html = frappe.get_print(dt, nm, print_format=pf)
            print(f"OK {dt} {nm} via '{pf}' -> {len(html)} chars rendered")
        except Exception as e:
            print(f"FAIL {dt} {nm}: {str(e)[:200]}")
