"""One-time fixes to make the Shade -> Formulation -> BOM -> Batch -> Stock Entry
chain complete for the Capital Colours demo.

Run: bench --site colour execute masterbatch.demo.fix_demo_gaps.run
"""
import frappe

JUNK_LFS = ["1", "123", "12345", "1456", "LF-MB-PEARL-012"]
JUNK_BOMS = ["BOM-RM-TIO2-001", "BOM-PKG-BAG-25-001"]

BOM_CLIENT_SCRIPT = """frappe.ui.form.on('BOM', {
  refresh(frm) {
    if (frm.doc.docstatus === 1 && frm.doc.is_active) {
      frm.add_custom_button('\\u25B6 Create Batch (produce)', () => {
        frappe.route_options = { finished_item: frm.doc.item, planned_qty: frm.doc.quantity };
        frappe.new_doc('Batch Production Sheet');
      }).removeClass('btn-default').addClass('btn-primary');
    }
  }
});"""


def delete_junk():
    for name in JUNK_LFS:
        if frappe.db.exists("Lab Formulation", name):
            doc = frappe.get_doc("Lab Formulation", name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc("Lab Formulation", name, force=1)
            print(f"deleted Lab Formulation {name}")
    for name in JUNK_BOMS:
        if frappe.db.exists("BOM", name):
            doc = frappe.get_doc("BOM", name)
            if doc.docstatus == 1:
                doc.flags.ignore_links = True
                doc.cancel()
            frappe.delete_doc("BOM", name, force=1)
            print(f"deleted BOM {name}")
    if frappe.db.exists("Workspace", "cgwcj"):
        frappe.delete_doc("Workspace", "cgwcj", force=1)
        print("deleted junk workspace cgwcj")


def link_formulations_to_boms():
    lfs = frappe.get_all("Lab Formulation", filters={"bom": ["is", "not set"]},
                         fields=["name", "finished_item"])
    for lf in lfs:
        bom = frappe.db.get_value("BOM", {"item": lf.finished_item, "is_active": 1,
                                          "is_default": 1, "docstatus": 1}, "name")
        if bom:
            frappe.db.set_value("Lab Formulation", lf.name, "bom", bom)
            print(f"linked {lf.name} -> {bom}")
        else:
            print(f"WARNING: no BOM found for {lf.name} ({lf.finished_item})")


def add_bom_client_script():
    name = "BOM Create Batch"
    if frappe.db.exists("Client Script", name):
        doc = frappe.get_doc("Client Script", name)
        doc.script = BOM_CLIENT_SCRIPT
        doc.enabled = 1
        doc.save()
        print(f"updated Client Script {name}")
        return
    doc = frappe.new_doc("Client Script")
    doc.update({"dt": "BOM", "view": "Form", "enabled": 1, "script": BOM_CLIENT_SCRIPT})
    doc.__newname = name
    doc.name = name
    doc.insert()
    print(f"created Client Script {name}")


def fix_workspace():
    import json
    ws = frappe.get_doc("Workspace", "Masterbatch")
    existing = {s.label: s for s in ws.shortcuts}
    order = ["Shade Code", "Lab Formulation", "Production BOM", "Batch Production Sheet",
             "Stock Entry", "Production Summary", "RM Consumption",
             "Shade-wise Production", "Formulation Cost"]
    rows = []
    for label in order:
        s = existing.get(label)
        if s:
            rows.append({"type": s.type, "label": s.label, "link_to": s.link_to,
                         "doc_view": s.doc_view, "color": s.color,
                         "stats_filter": s.stats_filter})
        elif label == "Production BOM":
            rows.append({"type": "DocType", "label": "Production BOM", "link_to": "BOM",
                         "doc_view": "List", "color": "Orange"})
        elif label == "Stock Entry":
            rows.append({"type": "DocType", "label": "Stock Entry", "link_to": "Stock Entry",
                         "doc_view": "List", "color": "Blue"})
    ws.set("shortcuts", [])
    for r in rows:
        ws.append("shortcuts", r)

    content = json.loads(ws.content)
    # keep everything up to (not including) the "Quick Links" header; rebuild the rest
    keep = []
    for block in content:
        if block.get("type") in ("header",) and "Quick Links" in (block.get("data", {}).get("text") or ""):
            break
        if block.get("type") == "shortcut":
            continue
        keep.append(block)
    keep.append({"id": frappe.generate_hash(length=10), "type": "header",
                 "data": {"text": "<span><b>Process Flow — Shade → Lab Recipe → BOM → Batch → Stock</b></span>", "col": 12}})
    for label in order:
        keep.append({"id": frappe.generate_hash(length=10), "type": "shortcut",
                     "data": {"shortcut_name": label, "col": 4}})
    ws.content = json.dumps(keep)
    ws.flags.ignore_links = True
    ws.save()
    print(f"workspace Masterbatch: {len(rows)} shortcuts in process order, content rebuilt")


def verify():
    n = frappe.db.count("Lab Formulation")
    nb = frappe.db.count("Lab Formulation", {"bom": ["is", "not set"]})
    print(f"Lab Formulations: {n}, without BOM: {nb}")
    boms = frappe.db.count("BOM", {"docstatus": 1, "is_active": 1})
    print(f"Active BOMs: {boms}")
    shades = frappe.get_all("Shade Code", pluck="name")
    missing = [s for s in shades
               if not frappe.db.exists("Lab Formulation", {"shade_code": s, "docstatus": 1})]
    print(f"Shades without formulation: {missing or 'none'}")
    print(f"cgwcj exists: {bool(frappe.db.exists('Workspace', 'cgwcj'))}")
    print(f"BOM Create Batch script: {bool(frappe.db.exists('Client Script', 'BOM Create Batch'))}")


def run():
    delete_junk()
    link_formulations_to_boms()
    add_bom_client_script()
    fix_workspace()
    frappe.db.commit()
    frappe.clear_cache()
    verify()
    print("DONE")
