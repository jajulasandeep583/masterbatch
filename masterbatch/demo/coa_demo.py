"""Capital Colours — COA demo data.

Fills QC parameter results on all submitted Batch Production Sheets
(in-spec values for Passed batches, an out-of-spec ΔE for Failed ones)
and assigns a QC-Passed batch on Sales Invoice / Delivery Note item rows
so the Print COA button has something to certify.

Run with:
  bench --site colour execute masterbatch.demo.coa_demo.run
"""

import random

import frappe

# parameter, test method, unit, spec, (lo, hi) for in-spec random result, decimals
QC_PLAN = [
    ("Melt Flow Index", "ASTM D1238", "g/10 min", "18.0 – 24.0", (19.0, 23.0), 1),
    ("Moisture Content", "ASTM D6980", "%", "≤ 0.10", (0.03, 0.08), 3),
    ("Pigment Content", "Muffle Furnace", "%", "38.0 – 42.0", (38.5, 41.5), 1),
    ("Colour Difference (ΔE)", "Spectrophotometer", "ΔE", "≤ 1.0", (0.2, 0.8), 2),
    ("Dispersion (Filter Pressure)", "EN 13900-5", "bar/g", "≤ 0.25", (0.08, 0.20), 2),
    ("Density", "ASTM D792", "g/cm³", "1.10 – 1.30", (1.12, 1.28), 2),
]


def fill_batch_qc():
    batches = frappe.get_all(
        "Batch Production Sheet",
        filters={"docstatus": 1},
        fields=["name", "qc_status"],
    )
    done = skipped = 0
    for b in batches:
        doc = frappe.get_doc("Batch Production Sheet", b.name)
        if doc.get("qc_parameters"):
            skipped += 1
            continue
        rnd = random.Random(b.name)  # deterministic per batch -> idempotent-ish
        failed = (b.qc_status == "Failed")
        for param, method, unit, spec, (lo, hi), nd in QC_PLAN:
            if failed and param.startswith("Colour Difference"):
                result, status = round(rnd.uniform(1.4, 2.6), nd), "Fail"
            else:
                result, status = round(rnd.uniform(lo, hi), nd), "Pass"
            doc.append("qc_parameters", {
                "parameter": param,
                "test_method": method,
                "unit": unit,
                "specification": spec,
                "result": f"{result:.{nd}f}",
                "status": status,
            })
        doc.flags.ignore_validate_update_after_submit = True
        doc.save(ignore_permissions=True)
        done += 1
    print(f"QC parameters: filled {done} batches, skipped {skipped} (already had data)")


def passed_batches_by_item():
    rows = frappe.get_all(
        "Batch Production Sheet",
        filters={"docstatus": 1, "qc_status": "Passed"},
        fields=["name", "finished_item"],
        order_by="production_date desc",
    )
    by_item = {}
    for r in rows:
        by_item.setdefault(r.finished_item, []).append(r.name)
    return by_item


def assign_sales_batches():
    by_item = passed_batches_by_item()
    total = 0
    for child_dt, parent_dt in (("Sales Invoice Item", "Sales Invoice"), ("Delivery Note Item", "Delivery Note")):
        rows = frappe.get_all(
            child_dt,
            filters={"docstatus": 1, "batch_production_sheet": ("is", "not set")},
            fields=["name", "item_code", "parent"],
        )
        n = 0
        for row in rows:
            batches = by_item.get(row.item_code)
            if not batches:
                continue  # not a finished good (expense/RM rows have no batches)
            rnd = random.Random(row.name)
            frappe.db.set_value(child_dt, row.name, "batch_production_sheet", rnd.choice(batches), update_modified=False)
            n += 1
        total += n
        print(f"{parent_dt}: batch set on {n} item rows")
    print(f"Batch assignment done ({total} rows)")


def run():
    fill_batch_qc()
    assign_sales_batches()
    frappe.db.commit()
    print("DONE COA demo data")
