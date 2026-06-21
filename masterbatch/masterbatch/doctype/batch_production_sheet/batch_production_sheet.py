import frappe
from frappe.model.document import Document
from frappe.utils import flt

from masterbatch.warehouse_utils import (
    get_default_company, get_source_warehouse, get_fg_warehouse, get_default_uom)


def evaluate_qc_status(row):
    """Pass/Fail for a QC row from its result vs the parameter's limits (server-side authority)."""
    result = row.result
    if result is None or str(result).strip() == "":
        return row.status or "Pass"
    et = row.evaluation_type or "Range"
    if et == "Text Match":
        return "Pass" if str(result).strip().lower() == str(row.target_text or "").strip().lower() else "Fail"
    try:
        val = float(str(result).strip())
    except (TypeError, ValueError):
        return "Fail"
    mn = row.min_value or 0
    mx = row.max_value or 0
    if et == "Minimum":
        return "Pass" if val >= mn else "Fail"
    if et == "Maximum":
        return "Pass" if val <= mx else "Fail"
    return "Pass" if (mn <= val <= mx) else "Fail"


class BatchProductionSheet(Document):
    def validate(self):
        if self.actual_output_kg and self.planned_qty:
            total_input = sum(r.qty_consumed or 0 for r in self.consumption_items)
            self.rejection_kg = total_input - self.actual_output_kg if total_input > self.actual_output_kg else 0
            # process loss % = material lost (input not turned into output) / input
            self.loss_percentage = round(self.rejection_kg / total_input * 100, 2) if total_input else 0
        # auto Pass/Fail each QC parameter from its result and the master's limits
        for row in (self.qc_parameters or []):
            row.status = evaluate_qc_status(row)

    def before_submit(self):
        # don't let a batch submit if a raw material isn't actually in stock —
        # replace the short item with an available one (or add stock) first.
        self.check_raw_material_stock()

    def check_raw_material_stock(self):
        company = get_default_company()
        # required qty per (item, its source warehouse)
        need_by = {}
        names = {}
        for r in self.consumption_items:
            if not (r.item_code and r.qty_consumed):
                continue
            wh = get_source_warehouse(company, r.item_code)
            if not wh:
                continue  # can't determine a warehouse — let the stock entry surface it
            key = (r.item_code, wh)
            need_by[key] = need_by.get(key, 0) + flt(r.qty_consumed)
            names[r.item_code] = r.item_name or r.item_code
        short = []
        for (item_code, wh), need in need_by.items():
            avail = flt(frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": wh}, "actual_qty"))
            if avail < need:
                short.append((item_code, names.get(item_code), need, avail, wh))
        if short:
            rows = "".join(
                "<li><b>{n}</b> ({c}): need {need:g}, only <b>{avail:g}</b> in {wh}</li>".format(
                    n=n or c, c=c, need=need, avail=avail, wh=wh)
                for c, n, need, avail, wh in short
            )
            frappe.throw(
                "These raw materials don't have enough stock:<ul>{rows}</ul>"
                "Replace the short item(s) in the <b>Raw Material Consumption</b> table with an "
                "available raw material (or add stock), then submit the batch again.".format(rows=rows),
                title="Insufficient Raw Material Stock",
            )

    def on_submit(self):
        frappe.msgprint(f"Batch {self.batch_no} submitted. Use 'Create Stock Entry' to post stock "
                        f"(consume raw materials, produce finished goods).")


@frappe.whitelist()
def find_formulation(finished_item):
    """Return the approved Lab Formulation for a finished item (so the batch can auto-load its recipe)."""
    return frappe.db.get_value(
        "Lab Formulation",
        {"finished_item": finished_item, "docstatus": 1},
        "name",
    ) or frappe.db.get_value("Lab Formulation", {"finished_item": finished_item}, "name")


@frappe.whitelist()
def find_recipe_source(finished_item):
    """Where to load a batch recipe for a finished item: its approved Lab Formulation
    if one exists, otherwise its default / active BOM. Lets a manually created batch
    auto-fill raw materials on sites that use BOMs (no Lab Formulation needed)."""
    if not finished_item:
        return {}
    lf = find_formulation(finished_item)
    if lf:
        return {"formulation": lf}
    bom = (frappe.db.get_value("BOM", {"item": finished_item, "is_default": 1, "docstatus": 1}, "name")
           or frappe.db.get_value("BOM", {"item": finished_item, "is_active": 1, "docstatus": 1}, "name")
           or frappe.db.get_value("BOM", {"item": finished_item, "docstatus": 1}, "name"))
    if bom:
        return {"bom": bom}
    return {}


@frappe.whitelist()
def get_formulation_items(formulation, planned_qty=0):
    """Return the recipe rows, scaled to the planned batch quantity, to auto-fill the batch sheet."""
    planned_qty = float(planned_qty or 0)
    uom = get_default_uom()
    lf = frappe.get_doc("Lab Formulation", formulation)
    rows = []
    for it in lf.formulation_items:
        plan = round((it.qty_per_100kg / 100.0) * planned_qty, 3) if planned_qty else it.qty_per_100kg
        rows.append({
            "item_code": it.item_code,
            "item_name": it.item_name or frappe.db.get_value("Item", it.item_code, "item_name"),
            "planned_qty": plan,
            "qty_consumed": plan,
            "uom": it.uom or frappe.db.get_value("Item", it.item_code, "stock_uom") or uom,
        })
    return {"finished_item": lf.finished_item, "shade_code": lf.shade_code, "items": rows}


@frappe.whitelist()
def get_bom_items(bom, planned_qty=0):
    """Return a BOM's components scaled to the planned batch quantity, in the same
    shape as get_formulation_items — so a batch can be (re)filled from a BOM with NO
    Lab Formulation. planned_qty=0 -> components for the BOM's own output quantity."""
    planned_qty = float(planned_qty or 0)
    doc = frappe.get_doc("BOM", bom)
    base = float(doc.quantity or 0) or 1.0           # BOM output qty (avoid div-by-zero)
    factor = (planned_qty / base) if planned_qty else 1.0
    rows = []
    for it in doc.items:
        per = float(it.stock_qty or it.qty or 0)     # component qty for the BOM's output
        plan = round(per * factor, 3)
        rows.append({
            "item_code": it.item_code,
            "item_name": it.item_name or frappe.db.get_value("Item", it.item_code, "item_name"),
            "planned_qty": plan,
            "qty_consumed": plan,
            "uom": it.stock_uom or frappe.db.get_value("Item", it.item_code, "stock_uom"),
        })
    shade = frappe.db.get_value("Lab Formulation", {"finished_item": doc.item}, "shade_code")
    return {"finished_item": doc.item, "shade_code": shade, "items": rows}


@frappe.whitelist()
def make_batch_sheet(source_name, target_doc=None):
    """Create a Batch Production Sheet from a BOM — recipe taken from the BOM's
    components, so a Lab Formulation is NOT required. Components are loaded as
    produced for the BOM's own output quantity (qty in stock UOM)."""
    from frappe.model.mapper import get_mapped_doc

    def _post(source, target):
        target.planned_qty = source.quantity or 0
        target.production_date = frappe.utils.today()
        # carry a shade code if the finished item has one on a Lab Formulation
        target.shade_code = frappe.db.get_value(
            "Lab Formulation", {"finished_item": source.item}, "shade_code")
        for row in target.consumption_items:
            row.qty_consumed = row.planned_qty

    return get_mapped_doc("BOM", source_name, {
        "BOM": {
            "doctype": "Batch Production Sheet",
            "field_map": {
                "name": "source_bom",
                "item": "finished_item",
            },
        },
        "BOM Item": {
            "doctype": "Batch Production Sheet Item",
            "field_map": {
                "item_code": "item_code",
                "item_name": "item_name",
                "stock_qty": "planned_qty",
                "stock_uom": "uom",
            },
        },
    }, target_doc, _post)


@frappe.whitelist()
def make_stock_entry(batch):
    """Post real stock for a batch: consume raw materials, produce the finished masterbatch."""
    doc = frappe.get_doc("Batch Production Sheet", batch)
    if doc.stock_entry and frappe.db.exists("Stock Entry", doc.stock_entry):
        return doc.stock_entry
    if not doc.consumption_items:
        frappe.throw("No raw-material consumption rows to post.")

    # Finished-goods quality gate: only QC-passed batches enter sellable stock
    if (doc.qc_status or "").strip() != "Passed":
        frappe.throw(
            f"Batch {doc.batch_no}: finished goods can move to sellable stock only after "
            f"QC is <b>Passed</b> (current QC status: {doc.qc_status or 'Pending'})."
        )

    company = get_default_company()
    uom = get_default_uom()

    def _row_uom(item_code, row_uom=None):
        # use the item's own stock UOM so this works on any site; fall back to the configured default
        return row_uom or frappe.db.get_value("Item", item_code, "stock_uom") or uom

    wh_fg = get_fg_warehouse(company, doc.finished_item)
    if not wh_fg:
        frappe.throw("No finished-goods warehouse could be determined. Set a "
                     "<b>Default Finished Goods Warehouse</b> in Masterbatch Settings.")

    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Manufacture"
    se.company = company
    se.posting_date = doc.production_date
    for r in doc.consumption_items:
        if not r.qty_consumed:
            continue
        wh_src = get_source_warehouse(company, r.item_code)
        if not wh_src:
            frappe.throw(f"No source warehouse for raw material <b>{r.item_code}</b>. Set a default "
                         "warehouse on the item, or a Default Source Warehouse in Masterbatch Settings.")
        se.append("items", {"item_code": r.item_code, "qty": r.qty_consumed,
                            "s_warehouse": wh_src, "uom": _row_uom(r.item_code, r.uom)})
    se.append("items", {"item_code": doc.finished_item, "qty": doc.actual_output_kg,
                        "t_warehouse": wh_fg, "is_finished_item": 1, "uom": _row_uom(doc.finished_item)})
    # rejection becomes sellable scrap stock under the chosen rejection item
    if (doc.rejection_kg or 0) > 0 and doc.rejection_item:
        se.append("items", {"item_code": doc.rejection_item, "qty": doc.rejection_kg,
                            "t_warehouse": get_fg_warehouse(company, doc.rejection_item),
                            "type": "Scrap", "allow_zero_valuation_rate": 1, "uom": _row_uom(doc.rejection_item)})
    se.insert(ignore_permissions=True)
    se.submit()
    doc.db_set("stock_entry", se.name)
    return se.name
