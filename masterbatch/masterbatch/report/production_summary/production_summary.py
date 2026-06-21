import frappe


def _item_group_tree(item_group):
    """Return the selected Item Group plus all its descendant groups (nested set)."""
    if not item_group:
        return None
    lft, rgt = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"]) or (None, None)
    if lft is None:
        return [item_group]
    return frappe.db.sql_list(
        "SELECT name FROM `tabItem Group` WHERE lft >= %s AND rgt <= %s", (lft, rgt)
    ) or [item_group]


def execute(filters=None):
    filters = filters or {}

    columns = [
        {"label": "Date",           "fieldname": "production_date", "fieldtype": "Date",  "width": 110},
        {"label": "Batch No",       "fieldname": "batch_no",        "fieldtype": "Data",  "width": 120},
        {"label": "Finished Item",  "fieldname": "finished_item",   "fieldtype": "Data",  "width": 170},
        {"label": "Item Group",     "fieldname": "item_group",      "fieldtype": "Link",  "options": "Item Group", "width": 150},
        {"label": "Shade Code",     "fieldname": "shade_code",      "fieldtype": "Data",  "width": 110},
        {"label": "Planned (KG)",   "fieldname": "planned_qty",     "fieldtype": "Float", "width": 110},
        {"label": "Output (KG)",    "fieldname": "actual_output_kg","fieldtype": "Float", "width": 110},
        {"label": "Rejection (KG)", "fieldname": "rejection_kg",    "fieldtype": "Float", "width": 120},
        {"label": "Loss %",         "fieldname": "loss_pct",        "fieldtype": "Percent", "width": 90},
        {"label": "Yield %",        "fieldname": "yield_pct",       "fieldtype": "Float", "width": 90},
        {"label": "QC Status",      "fieldname": "qc_status",       "fieldtype": "Data",  "width": 100},
        {"label": "Operator",       "fieldname": "operator",        "fieldtype": "Data",  "width": 120},
    ]

    cond = "b.docstatus = 1"
    if filters.get("from_date"):
        cond += " AND b.production_date >= %(from_date)s"
    if filters.get("to_date"):
        cond += " AND b.production_date <= %(to_date)s"
    if filters.get("finished_item"):
        cond += " AND b.finished_item = %(finished_item)s"
    if filters.get("item_group"):
        filters["item_groups"] = tuple(_item_group_tree(filters.get("item_group")))
        cond += " AND it.item_group IN %(item_groups)s"

    data = frappe.db.sql(f"""
        SELECT
            b.production_date, b.batch_no, b.finished_item,
            it.item_group, b.shade_code,
            b.planned_qty, b.actual_output_kg, b.rejection_kg,
            CASE WHEN (b.rejection_kg + b.actual_output_kg) > 0
                 THEN ROUND(b.rejection_kg / (b.rejection_kg + b.actual_output_kg) * 100, 2)
                 ELSE 0 END AS loss_pct,
            CASE WHEN b.planned_qty > 0
                 THEN ROUND((b.actual_output_kg / b.planned_qty) * 100, 2)
                 ELSE 0 END AS yield_pct,
            b.qc_status, b.operator
        FROM `tabBatch Production Sheet` b
        LEFT JOIN `tabItem` it ON it.name = b.finished_item
        WHERE {cond}
        ORDER BY b.production_date DESC, b.batch_no DESC
    """, filters, as_dict=True)

    n = len(data)
    out = sum(d.actual_output_kg or 0 for d in data)
    plan = sum(d.planned_qty or 0 for d in data)
    rej = sum(d.rejection_kg or 0 for d in data)
    avg_yield = round(out / plan * 100, 1) if plan else 0
    total_input = out + rej
    avg_loss = round(rej / total_input * 100, 1) if total_input else 0
    passed = sum(1 for d in data if d.qc_status == "Passed")
    pass_rate = round(passed / n * 100, 1) if n else 0

    report_summary = [
        {"value": n, "label": "Total Batches", "datatype": "Int", "indicator": "Blue"},
        {"value": round(out), "label": "Total Output (KG)", "datatype": "Int", "indicator": "Green"},
        {"value": avg_yield, "label": "Avg Yield %", "datatype": "Float",
         "indicator": "Green" if avg_yield >= 98 else "Orange"},
        {"value": round(rej), "label": "Total Rejection (KG)", "datatype": "Int", "indicator": "Red"},
        {"value": avg_loss, "label": "Avg Loss %", "datatype": "Float",
         "indicator": "Green" if avg_loss <= 2 else "Orange"},
        {"value": pass_rate, "label": "QC Pass Rate %", "datatype": "Float",
         "indicator": "Green" if pass_rate >= 80 else "Orange"},
    ]

    # When filtered by Item Group, chart output by group; otherwise by date.
    if filters.get("item_group"):
        bygroup = {}
        for d in data:
            k = d.item_group or "Unassigned"
            bygroup[k] = bygroup.get(k, 0) + (d.actual_output_kg or 0)
        labels = sorted(bygroup.keys())
        values = [round(bygroup[k]) for k in labels]
        chart = {
            "data": {"labels": labels, "datasets": [{"name": "Output by Item Group (KG)", "values": values}]},
            "type": "bar", "colors": ["#7B2D8B"],
        }
    else:
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
        {"fieldname": "item_group",    "label": "Item Group",    "fieldtype": "Link", "options": "Item Group"},
    ]
