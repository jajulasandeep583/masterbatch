import frappe
from frappe.utils import today, get_first_day

from masterbatch.warehouse_utils import get_default_company, get_fg_warehouse


@frappe.whitelist()
def cockpit_data():
    company = get_default_company()
    wh_fg = get_fg_warehouse(company)
    mstart = get_first_day(today())
    d = {}

    r = frappe.db.sql("""SELECT COUNT(*) c, COALESCE(SUM(actual_output_kg),0) o
        FROM `tabBatch Production Sheet` WHERE docstatus=1 AND production_date=%s""", today(), as_dict=True)[0]
    d["today_batches"], d["today_output"] = r.c, int(r.o)

    r = frappe.db.sql("""SELECT COUNT(*) c, COALESCE(SUM(actual_output_kg),0) o
        FROM `tabBatch Production Sheet` WHERE docstatus=1 AND production_date>=%s""", mstart, as_dict=True)[0]
    d["month_batches"], d["month_output"] = r.c, int(r.o)

    consumed = frappe.db.sql("""SELECT COALESCE(SUM(sed.qty),0)
        FROM `tabStock Entry Detail` sed JOIN `tabStock Entry` se ON se.name=sed.parent
        WHERE se.docstatus=1 AND se.stock_entry_type='Manufacture'
        AND sed.s_warehouse IS NOT NULL AND sed.s_warehouse!='' AND se.posting_date>=%s""", mstart)[0][0]
    d["month_consumed"] = int(consumed or 0)

    tot = frappe.db.count("Batch Production Sheet", {"docstatus": 1})
    passed = frappe.db.count("Batch Production Sheet", {"docstatus": 1, "qc_status": "Passed"})
    failed = frappe.db.count("Batch Production Sheet", {"docstatus": 1, "qc_status": "Failed"})
    d["total_batches"], d["qc_rate"], d["qc_failed"] = tot, round(passed / tot * 100, 1) if tot else 0, failed

    so = frappe.db.sql("""SELECT COUNT(*) c, COALESCE(SUM(base_grand_total),0) v
        FROM `tabSales Order` WHERE docstatus=1 AND IFNULL(per_delivered,0)<100""", as_dict=True)[0]
    d["pending_deliveries"], d["pending_value"] = so.c, int(so.v)

    po = frappe.db.sql("""SELECT COUNT(*) c FROM `tabPurchase Order`
        WHERE docstatus=1 AND IFNULL(per_received,0)<100""", as_dict=True)[0]
    d["open_pos"] = po.c

    d["fg_stock_value"] = int(frappe.db.sql(
        "SELECT COALESCE(SUM(stock_value),0) FROM `tabBin` WHERE warehouse=%s", wh_fg)[0][0] or 0) if wh_fg else 0
    d["fg_stock_qty"] = int(frappe.db.sql(
        "SELECT COALESCE(SUM(actual_qty),0) FROM `tabBin` WHERE warehouse=%s", wh_fg)[0][0] or 0) if wh_fg else 0

    d["pending_so"] = frappe.db.sql("""SELECT so.name, so.customer, so.delivery_date,
        soi.item_code, soi.qty, IFNULL(so.per_delivered,0) per
        FROM `tabSales Order` so JOIN `tabSales Order Item` soi ON soi.parent=so.name
        WHERE so.docstatus=1 AND IFNULL(so.per_delivered,0)<100
        ORDER BY so.delivery_date LIMIT 10""", as_dict=True)

    d["recent"] = frappe.db.sql("""SELECT batch_no, finished_item, shade_code, actual_output_kg,
        qc_status, production_date FROM `tabBatch Production Sheet`
        WHERE docstatus=1 ORDER BY production_date DESC, batch_no DESC LIMIT 8""", as_dict=True)

    top = frappe.db.sql("""SELECT shade_code, SUM(actual_output_kg) o
        FROM `tabBatch Production Sheet` WHERE docstatus=1
        GROUP BY shade_code ORDER BY o DESC LIMIT 6""", as_dict=True)
    mx = max([t.o for t in top], default=1) or 1
    for t in top:
        t["pct"] = round((t.o or 0) / mx * 100)
        t["o"] = int(t.o or 0)
    d["top_shades"] = top

    d["company"] = company
    return d
