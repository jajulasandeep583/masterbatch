import frappe

def execute(filters=None):
    filters = filters or {}

    columns = [
        {"label": "Date",           "fieldname": "production_date", "fieldtype": "Date",  "width": 110},
        {"label": "Batch No",       "fieldname": "batch_no",        "fieldtype": "Data",  "width": 120},
        {"label": "Finished Item",  "fieldname": "finished_item",   "fieldtype": "Data",  "width": 160},
        {"label": "Shade Code",     "fieldname": "shade_code",      "fieldtype": "Data",  "width": 110},
        {"label": "Planned (KG)",   "fieldname": "planned_qty",     "fieldtype": "Float", "width": 110},
        {"label": "Output (KG)",    "fieldname": "actual_output_kg","fieldtype": "Float", "width": 110},
        {"label": "Rejection (KG)", "fieldname": "rejection_kg",    "fieldtype": "Float", "width": 120},
        {"label": "Yield %",        "fieldname": "yield_pct",       "fieldtype": "Float", "width": 90},
        {"label": "QC Status",      "fieldname": "qc_status",       "fieldtype": "Data",  "width": 100},
        {"label": "Operator",       "fieldname": "operator",        "fieldtype": "Data",  "width": 120},
    ]

    cond = "docstatus = 1"
    if filters.get("from_date"):
        cond += f" AND production_date >= %(from_date)s"
    if filters.get("to_date"):
        cond += f" AND production_date <= %(to_date)s"
    if filters.get("finished_item"):
        cond += f" AND finished_item = %(finished_item)s"

    data = frappe.db.sql(f"""
        SELECT
            production_date, batch_no, finished_item, shade_code,
            planned_qty, actual_output_kg, rejection_kg,
            CASE WHEN planned_qty > 0
                 THEN ROUND((actual_output_kg / planned_qty) * 100, 2)
                 ELSE 0 END AS yield_pct,
            qc_status, operator
        FROM `tabBatch Production Sheet`
        WHERE {cond}
        ORDER BY production_date DESC, batch_no DESC
    """, filters, as_dict=True)

    return columns, data


def get_filters():
    return [
        {"fieldname": "from_date",     "label": "From Date",     "fieldtype": "Date"},
        {"fieldname": "to_date",       "label": "To Date",       "fieldtype": "Date"},
        {"fieldname": "finished_item", "label": "Finished Item", "fieldtype": "Link", "options": "Item"},
    ]
