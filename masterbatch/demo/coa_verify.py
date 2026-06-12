"""Smoke test: COA print formats render with real data.

Run with: bench --site colour execute masterbatch.demo.coa_verify.run
"""

import frappe


def run():
    # a submitted SI whose rows have a batch assigned
    si_row = frappe.get_all(
        "Sales Invoice Item",
        filters={"docstatus": 1, "batch_production_sheet": ("is", "set")},
        fields=["parent", "batch_production_sheet"],
        limit=1,
    )[0]
    html = frappe.get_print("Sales Invoice", si_row.parent, "Capital Colours COA")
    assert "CERTIFICATE OF ANALYSIS" in html and "Melt Flow Index" in html, "SI COA missing content"
    print(f"SI COA OK: {si_row.parent} (batch {si_row.batch_production_sheet}, {len(html)} chars)")

    dn_row = frappe.get_all(
        "Delivery Note Item",
        filters={"docstatus": 1, "batch_production_sheet": ("is", "set")},
        fields=["parent"],
        limit=1,
    )
    if dn_row:
        html = frappe.get_print("Delivery Note", dn_row[0].parent, "Capital Colours COA - DN")
        assert "CERTIFICATE OF ANALYSIS" in html, "DN COA missing content"
        print(f"DN COA OK: {dn_row[0].parent} ({len(html)} chars)")

    batch = frappe.get_all(
        "Batch Production Sheet",
        filters={"docstatus": 1, "qc_status": "Passed"},
        limit=1,
    )[0].name
    html = frappe.get_print("Batch Production Sheet", batch, "Capital Colours COA - Batch")
    assert "CERTIFICATE OF ANALYSIS" in html and "PASSED" in html, "Batch COA missing content"
    print(f"Batch COA OK: {batch} ({len(html)} chars)")

    failed = frappe.get_all(
        "Batch Production Sheet",
        filters={"docstatus": 1, "qc_status": "Failed"},
        limit=1,
    )
    if failed:
        html = frappe.get_print("Batch Production Sheet", failed[0].name, "Capital Colours COA - Batch")
        assert "does NOT conform" in html, "Failed batch COA should show non-conformance"
        print(f"Failed-batch COA OK: {failed[0].name}")

    n_qc = frappe.db.count("Batch QC Parameter")
    print(f"QC parameter rows total: {n_qc}")
    print("ALL COA SMOKE TESTS PASSED")
