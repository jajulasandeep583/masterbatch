import frappe


def execute(filters=None):
    filters = filters or {}

    columns = [
        {"label": "Date",           "fieldname": "production_date", "fieldtype": "Date",  "width": 110},
        {"label": "Batch No",       "fieldname": "batch_no",        "fieldtype": "Data",  "width": 120},
        {"label": "Finished Item",  "fieldname": "finished_item",   "fieldtype": "Data",  "width": 170},
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
        cond += " AND production_date >= %(from_date)s"
    if filters.get("to_date"):
        cond += " AND production_date <= %(to_date)s"
    if filters.get("finished_item"):
        cond += " AND finished_item = %(finished_item)s"

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

    n = len(data)
    out = sum(d.actual_output_kg or 0 for d in data)
    plan = sum(d.planned_qty or 0 for d in data)
    rej = sum(d.rejection_kg or 0 for d in data)
    avg_yield = round(out / plan * 100, 1) if plan else 0
    passed = sum(1 for d in data if d.qc_status == "Passed")
    pass_rate = round(passed / n * 100, 1) if n else 0

    report_summary = [
        {"value": n, "label": "Total Batches", "datatype": "Int", "indicator": "Blue"},
        {"value": round(out), "label": "Total Output (KG)", "datatype": "Int", "indicator": "Green"},
        {"value": avg_yield, "label": "Avg Yield %", "datatype": "Float",
         "indicator": "Green" if avg_yield >= 98 else "Orange"},
        {"value": round(rej), "label": "Total Rejection (KG)", "datatype": "Int", "indicator": "Red"},
        {"value": pass_rate, "label": "QC Pass Rate %", "datatype": "Float",
         "indicator": "Green" if pass_rate >= 80 else "Orange"},
    ]

    bydate = {}
    for d in data:
        k = str(d.production_date)
        bydate[k] = bydate.get(k, 0) + (d.actual_output_kg or 0)
    labels = sorted(bydate.keys())
    values = [round(bydate[k]) for k in labels]
    chart = {
        "data": {"labels": labels, "datasets": [{"name": "Daily Output (KG)", "values": values}]},
        "type": "line", "colors": ["#7B2D8B"], "lineOptions": {"hideDots": 1, "regionFill": 1},
    }

    return columns, data, None, chart, report_summary


def get_filters():
    return [
        {"fieldname": "from_date",     "label": "From Date",     "fieldtype": "Date"},
        {"fieldname": "to_date",       "label": "To Date",       "fieldtype": "Date"},
        {"fieldname": "finished_item", "label": "Finished Item", "fieldtype": "Link", "options": "Item"},
    ]
