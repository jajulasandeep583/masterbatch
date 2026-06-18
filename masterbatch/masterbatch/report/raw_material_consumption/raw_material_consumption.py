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
        {"label": "Date",          "fieldname": "production_date", "fieldtype": "Date", "width": 110},
        {"label": "Batch No",      "fieldname": "batch_no",       "fieldtype": "Data", "width": 120},
        {"label": "Finished Item", "fieldname": "finished_item",  "fieldtype": "Data", "width": 160},
        {"label": "Raw Material",  "fieldname": "item_code",      "fieldtype": "Data", "width": 150},
        {"label": "Item Name",     "fieldname": "item_name",      "fieldtype": "Data", "width": 170},
        {"label": "Item Group",    "fieldname": "item_group",     "fieldtype": "Link", "options": "Item Group", "width": 150},
        {"label": "Planned (KG)",  "fieldname": "planned_qty",    "fieldtype": "Float","width": 110},
        {"label": "Consumed (KG)", "fieldname": "qty_consumed",   "fieldtype": "Float","width": 120},
        {"label": "Variance (KG)", "fieldname": "variance",       "fieldtype": "Float","width": 110},
    ]

    cond = "b.docstatus = 1"
    if filters.get("from_date"):
        cond += " AND b.production_date >= %(from_date)s"
    if filters.get("to_date"):
        cond += " AND b.production_date <= %(to_date)s"
    if filters.get("item_code"):
        cond += " AND bi.item_code = %(item_code)s"
    if filters.get("item_group"):
        filters["item_groups"] = tuple(_item_group_tree(filters.get("item_group")))
        cond += " AND it.item_group IN %(item_groups)s"

    data = frappe.db.sql(f"""
        SELECT
            b.production_date, b.batch_no, b.finished_item,
            bi.item_code, bi.item_name, it.item_group,
            bi.planned_qty, bi.qty_consumed,
            ROUND(bi.qty_consumed - bi.planned_qty, 3) AS variance
        FROM `tabBatch Production Sheet` b
        JOIN `tabBatch Production Sheet Item` bi ON bi.parent = b.name
        LEFT JOIN `tabItem` it ON it.name = bi.item_code
        WHERE {cond}
        ORDER BY b.production_date DESC, b.batch_no
    """, filters, as_dict=True)

    total_planned = sum(d.planned_qty or 0 for d in data)
    total_consumed = sum(d.qty_consumed or 0 for d in data)
    variance = round(total_consumed - total_planned, 1)
    materials = len({d.item_code for d in data})

    report_summary = [
        {"value": materials, "label": "Raw Materials Used", "datatype": "Int", "indicator": "Blue"},
        {"value": round(total_planned), "label": "Planned (KG)", "datatype": "Int", "indicator": "Blue"},
        {"value": round(total_consumed), "label": "Consumed (KG)", "datatype": "Int", "indicator": "Orange"},
        {"value": variance, "label": "Variance (KG)", "datatype": "Float",
         "indicator": "Red" if variance > 0 else "Green"},
    ]

    # When filtered by Item Group, chart consumption by group; otherwise top materials.
    if filters.get("item_group"):
        bygroup = {}
        for d in data:
            k = d.item_group or "Unassigned"
            bygroup[k] = bygroup.get(k, 0) + (d.qty_consumed or 0)
        top = sorted(bygroup.items(), key=lambda x: x[1], reverse=True)
        chart = {
            "data": {
                "labels": [t[0] for t in top],
                "datasets": [{"name": "Consumed by Item Group (KG)", "values": [round(t[1]) for t in top]}],
            },
            "type": "bar", "colors": ["#E07B00"],
        }
    else:
        by_item = {}
        for d in data:
            by_item[d.item_name or d.item_code] = by_item.get(d.item_name or d.item_code, 0) + (d.qty_consumed or 0)
        top = sorted(by_item.items(), key=lambda x: x[1], reverse=True)[:12]
        chart = {
            "data": {
                "labels": [t[0] for t in top],
                "datasets": [{"name": "Consumed (KG)", "values": [round(t[1]) for t in top]}],
            },
            "type": "bar", "colors": ["#E07B00"],
        }

    return columns, data, None, chart, report_summary


def get_filters():
    return [
        {"fieldname": "from_date", "label": "From Date", "fieldtype": "Date"},
        {"fieldname": "to_date",   "label": "To Date",   "fieldtype": "Date"},
        {"fieldname": "item_code", "label": "Raw Material", "fieldtype": "Link", "options": "Item"},
        {"fieldname": "item_group", "label": "Item Group", "fieldtype": "Link", "options": "Item Group"},
    ]
