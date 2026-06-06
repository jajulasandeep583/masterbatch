import frappe

def execute(filters=None):
    filters = filters or {}

    columns = [
        {"label": "Date",            "fieldname": "production_date","fieldtype": "Date", "width": 110},
        {"label": "Batch No",        "fieldname": "batch_no",       "fieldtype": "Data", "width": 120},
        {"label": "Finished Item",   "fieldname": "finished_item",  "fieldtype": "Data", "width": 150},
        {"label": "Raw Material",    "fieldname": "item_code",      "fieldtype": "Data", "width": 160},
        {"label": "Item Name",       "fieldname": "item_name",      "fieldtype": "Data", "width": 150},
        {"label": "Planned (KG)",    "fieldname": "planned_qty",    "fieldtype": "Float","width": 110},
        {"label": "Consumed (KG)",   "fieldname": "qty_consumed",   "fieldtype": "Float","width": 120},
        {"label": "Variance (KG)",   "fieldname": "variance",       "fieldtype": "Float","width": 110},
    ]

    cond = "b.docstatus = 1"
    if filters.get("from_date"):
        cond += " AND b.production_date >= %(from_date)s"
    if filters.get("to_date"):
        cond += " AND b.production_date <= %(to_date)s"
    if filters.get("item_code"):
        cond += " AND bi.item_code = %(item_code)s"

    data = frappe.db.sql(f"""
        SELECT
            b.production_date, b.batch_no, b.finished_item,
            bi.item_code, bi.item_name,
            bi.planned_qty, bi.qty_consumed,
            ROUND(bi.qty_consumed - bi.planned_qty, 3) AS variance
        FROM `tabBatch Production Sheet` b
        JOIN `tabBatch Production Sheet Item` bi ON bi.parent = b.name
        WHERE {cond}
        ORDER BY b.production_date DESC, b.batch_no
    """, filters, as_dict=True)

    return columns, data


def get_filters():
    return [
        {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date"},
        {"fieldname": "to_date",   "label": "To Date",   "fieldtype": "Date"},
        {"fieldname": "item_code", "label": "Raw Material", "fieldtype": "Link", "options": "Item"},
    ]
