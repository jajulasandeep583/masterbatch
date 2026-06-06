import frappe


def execute(filters=None):
    filters = filters or {}

    columns = [
        {"label": "Shade Code",        "fieldname": "shade_code",      "fieldtype": "Data",  "width": 120},
        {"label": "Finished Item",     "fieldname": "finished_item",   "fieldtype": "Data",  "width": 180},
        {"label": "Total Batches",     "fieldname": "total_batches",   "fieldtype": "Int",   "width": 120},
        {"label": "Total Output (KG)", "fieldname": "total_output",    "fieldtype": "Float", "width": 140},
        {"label": "Total Rejection",   "fieldname": "total_rejection", "fieldtype": "Float", "width": 130},
        {"label": "Avg Yield %",       "fieldname": "avg_yield",       "fieldtype": "Float", "width": 110},
    ]

    cond = "docstatus = 1"
    if filters.get("from_date"):
        cond += " AND production_date >= %(from_date)s"
    if filters.get("to_date"):
        cond += " AND production_date <= %(to_date)s"

    data = frappe.db.sql(f"""
        SELECT
            shade_code, finished_item,
            COUNT(*) AS total_batches,
            SUM(actual_output_kg) AS total_output,
            SUM(rejection_kg) AS total_rejection,
            ROUND(AVG(CASE WHEN planned_qty > 0 THEN (actual_output_kg/planned_qty)*100 ELSE 0 END), 2) AS avg_yield
        FROM `tabBatch Production Sheet`
        WHERE {cond}
        GROUP BY shade_code, finished_item
        ORDER BY total_output DESC
    """, filters, as_dict=True)

    total_out = sum(d.total_output or 0 for d in data)
    total_batches = sum(d.total_batches or 0 for d in data)
    best = data[0].shade_code if data else "-"

    report_summary = [
        {"value": len(data), "label": "Shade / Item Combos", "datatype": "Int", "indicator": "Blue"},
        {"value": total_batches, "label": "Total Batches", "datatype": "Int", "indicator": "Blue"},
        {"value": round(total_out), "label": "Total Output (KG)", "datatype": "Int", "indicator": "Green"},
        {"value": best, "label": "Top Shade by Output", "datatype": "Data", "indicator": "Purple"},
    ]

    top = data[:10]
    chart = {
        "data": {
            "labels": [d.shade_code for d in top],
            "datasets": [{"name": "Output (KG)", "values": [round(d.total_output or 0) for d in top]}],
        },
        "type": "bar", "colors": ["#00A9A5"],
    }

    return columns, data, None, chart, report_summary


def get_filters():
    return [
        {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date"},
        {"fieldname": "to_date",   "label": "To Date",   "fieldtype": "Date"},
    ]
