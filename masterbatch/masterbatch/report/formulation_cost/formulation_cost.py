import frappe


def execute(filters=None):
    filters = filters or {}

    columns = [
        {"label": "Formulation",       "fieldname": "formulation_no", "fieldtype": "Link",  "options": "Lab Formulation", "width": 160},
        {"label": "Finished Item",     "fieldname": "finished_item",  "fieldtype": "Data",  "width": 200},
        {"label": "Shade",             "fieldname": "shade_code",     "fieldtype": "Data",  "width": 90},
        {"label": "Ingredients",       "fieldname": "ingredients",    "fieldtype": "Int",   "width": 100},
        {"label": "Material Cost / 100KG", "fieldname": "cost_100",   "fieldtype": "Currency", "width": 160},
        {"label": "Material Cost / KG",    "fieldname": "cost_kg",    "fieldtype": "Currency", "width": 150},
        {"label": "Status",            "fieldname": "status",         "fieldtype": "Data",  "width": 90},
        {"label": "Production BOM",     "fieldname": "bom",            "fieldtype": "Link",  "options": "BOM", "width": 150},
    ]

    cond = "lf.docstatus < 2"
    if filters.get("finished_item"):
        cond += " AND lf.finished_item = %(finished_item)s"

    rows = frappe.db.sql(f"""
        SELECT
            lf.name AS formulation_no, lf.finished_item, lf.shade_code, lf.status, lf.bom,
            COUNT(lfi.name) AS ingredients,
            ROUND(SUM(lfi.qty_per_100kg * IFNULL(it.valuation_rate, 0)), 2) AS cost_100
        FROM `tabLab Formulation` lf
        LEFT JOIN `tabLab Formulation Item` lfi ON lfi.parent = lf.name
        LEFT JOIN `tabItem` it ON it.name = lfi.item_code
        WHERE {cond}
        GROUP BY lf.name
        ORDER BY cost_100 DESC
    """, filters, as_dict=True)

    for r in rows:
        r["cost_kg"] = round((r.cost_100 or 0) / 100.0, 2)

    n = len(rows)
    avg_kg = round(sum(r.cost_kg for r in rows) / n, 2) if n else 0
    costliest = rows[0].finished_item if rows else "-"
    cheapest = rows[-1].finished_item if rows else "-"

    report_summary = [
        {"value": n, "label": "Formulations", "datatype": "Int", "indicator": "Blue"},
        {"value": avg_kg, "label": "Avg Material Cost / KG", "datatype": "Currency", "indicator": "Orange"},
        {"value": costliest, "label": "Costliest Recipe", "datatype": "Data", "indicator": "Red"},
        {"value": cheapest, "label": "Cheapest Recipe", "datatype": "Data", "indicator": "Green"},
    ]

    top = rows[:12]
    chart = {
        "data": {"labels": [r.shade_code or r.formulation_no for r in top],
                 "datasets": [{"name": "Material Cost / KG", "values": [r.cost_kg for r in top]}]},
        "type": "bar", "colors": ["#7B2D8B"],
    }
    return columns, rows, None, chart, report_summary
