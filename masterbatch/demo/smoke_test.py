import frappe


def run():
    ok, bad = [], []

    def check(label, fn):
        try:
            r = fn()
            ok.append(f"PASS {label}" + (f" -> {r}" if r else ""))
        except Exception as e:
            bad.append(f"FAIL {label}: {e}")

    from masterbatch.masterbatch.doctype.batch_production_sheet.batch_production_sheet import (
        find_formulation, get_formulation_items)

    # chain helpers for every shade's finished item
    items = frappe.get_all("Lab Formulation", filters={"docstatus": 1}, pluck="finished_item")
    misses = [i for i in set(items) if not find_formulation(i)]
    check("find_formulation for all 13 FG items", lambda: f"misses={misses or 'none'}")

    lf = frappe.db.get_value("Lab Formulation", {"finished_item": "MB-BLACK-PE"}, "name")
    check("get_formulation_items scaled to 500kg",
          lambda: f"{len(get_formulation_items(lf, 500))} rows")

    # cockpit api
    from masterbatch.api import cockpit_data
    check("cockpit_data", lambda: f"{len(cockpit_data() or {})} keys")

    # reports
    from frappe.desk.query_report import run as run_report
    today = frappe.utils.today()
    year_ago = frappe.utils.add_months(today, -12)
    for rep, flt in [("Production Summary", {"from_date": year_ago, "to_date": today}),
                     ("Raw Material Consumption", {"from_date": year_ago, "to_date": today}),
                     ("Shade-wise Production", {"from_date": year_ago, "to_date": today}),
                     ("Formulation Cost", {})]:
        check(f"report {rep}",
              lambda rep=rep, flt=flt: f"{len(run_report(rep, filters=flt, ignore_prepared_report=True).get('result') or [])} rows")

    # workspace + number cards + charts referenced in content still exist
    import json
    ws = frappe.get_doc("Workspace", "Masterbatch")
    for block in json.loads(ws.content):
        t, d = block["type"], block["data"]
        if t == "number_card":
            check(f"number card {d['number_card_name']}",
                  lambda n=d["number_card_name"]: bool(frappe.db.exists("Number Card", n)) or 1/0)
        elif t == "chart":
            check(f"chart {d['chart_name']}",
                  lambda n=d["chart_name"]: bool(frappe.db.exists("Dashboard Chart", n)) or 1/0)
        elif t == "shortcut":
            check(f"shortcut {d['shortcut_name']} in child table",
                  lambda n=d["shortcut_name"]: any(s.label == n for s in ws.shortcuts) or 1/0)

    # QC gate: make_stock_entry must refuse a failed batch
    failed = frappe.db.get_value("Batch Production Sheet", {"qc_status": "Failed", "docstatus": 1}, "name")
    if failed:
        from masterbatch.masterbatch.doctype.batch_production_sheet.batch_production_sheet import make_stock_entry
        try:
            make_stock_entry(failed)
            bad.append("FAIL QC gate: stock entry created for FAILED batch!")
            frappe.db.rollback()
        except Exception:
            frappe.db.rollback()
            ok.append("PASS QC gate blocks failed batch")

    print("\n".join(ok))
    if bad:
        print("\n".join(bad))
    else:
        print("ALL CHECKS PASSED")
