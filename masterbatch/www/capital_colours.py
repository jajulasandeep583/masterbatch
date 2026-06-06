import frappe

SWATCH = [
    ("white", "#F4F4F6", "#333"), ("black", "#23232B", "#fff"),
    ("red", "#D7263D", "#fff"), ("brick", "#B0413E", "#fff"),
    ("yellow", "#F7C948", "#333"), ("lemon", "#F7C948", "#333"),
    ("blue", "#2D6CDF", "#fff"), ("royal", "#2D6CDF", "#fff"),
    ("green", "#2BA84A", "#fff"), ("forest", "#1E7d34", "#fff"),
    ("filler", "#C7CCD1", "#333"), ("pearl", "#E7D6F0", "#5a2d70"),
    ("antiox", "#9C7A57", "#fff"), ("additive", "#9C7A57", "#fff"),
]


def _color(name):
    n = (name or "").lower()
    for key, bg, fg in SWATCH:
        if key in n:
            return bg, fg
    return "#7B2D8B", "#fff"


def get_context(context):
    context.no_cache = 1
    context.title = "Capital Colours"

    bps = frappe.db.sql("""
        SELECT COUNT(*) c,
               COALESCE(SUM(actual_output_kg),0) outp,
               COALESCE(SUM(planned_qty),0) plan,
               COALESCE(SUM(rejection_kg),0) rej,
               SUM(CASE WHEN qc_status='Passed' THEN 1 ELSE 0 END) passed
        FROM `tabBatch Production Sheet` WHERE docstatus=1
    """, as_dict=True)[0]

    context.total_batches = int(bps.c or 0)
    context.total_output = int(bps.outp or 0)
    context.avg_yield = round((bps.outp / bps.plan * 100) if bps.plan else 0, 1)
    context.total_rejection = int(bps.rej or 0)
    context.qc_rate = round((bps.passed / bps.c * 100) if bps.c else 0, 1)

    context.n_rm = frappe.db.count("Item", {"item_group": "Raw Materials - MB"})
    context.n_fg = frappe.db.count("Item", {"item_group": "Finished Goods - MB"})
    context.n_shades = frappe.db.count("Shade Code")
    context.n_formulations = frappe.db.count("Lab Formulation")
    context.n_boms = frappe.db.count("BOM")
    context.n_customers = frappe.db.count("Customer")
    context.n_suppliers = frappe.db.count("Supplier")
    context.n_po = frappe.db.count("Purchase Order", {"docstatus": 1})
    context.n_so = frappe.db.count("Sales Order", {"docstatus": 1})
    context.so_value = int(frappe.db.sql(
        "SELECT COALESCE(SUM(grand_total),0) FROM `tabSales Order` WHERE docstatus=1")[0][0] or 0)

    shades = frappe.get_all("Shade Code", fields=["shade_code", "shade_name", "product_type"],
                            order_by="shade_code", limit_page_length=0)
    for s in shades:
        s.bg, s.fg = _color(s.shade_name or s.shade_code)
    context.shades = shades

    top = frappe.db.sql("""
        SELECT shade_code, SUM(actual_output_kg) outp
        FROM `tabBatch Production Sheet` WHERE docstatus=1
        GROUP BY shade_code ORDER BY outp DESC LIMIT 8
    """, as_dict=True)
    mx = max([t.outp for t in top], default=1) or 1
    for t in top:
        t.pct = round((t.outp or 0) / mx * 100)
        t.outp = int(t.outp or 0)
    context.top_shades = top

    context.recent = frappe.db.sql("""
        SELECT batch_no, production_date, finished_item, shade_code, formulation_no,
               planned_qty, actual_output_kg, qc_status,
               ROUND(actual_output_kg/NULLIF(planned_qty,0)*100,1) yield_pct
        FROM `tabBatch Production Sheet` WHERE docstatus=1
        ORDER BY production_date DESC, batch_no DESC LIMIT 8
    """, as_dict=True)

    forms = frappe.db.sql("""
        SELECT lf.name formulation_no, lf.finished_item, lf.shade_code, lf.bom, lf.status,
               COUNT(lfi.name) ingredients,
               ROUND(SUM(lfi.qty_per_100kg*IFNULL(it.valuation_rate,0))/100,2) cost_kg
        FROM `tabLab Formulation` lf
        LEFT JOIN `tabLab Formulation Item` lfi ON lfi.parent=lf.name
        LEFT JOIN `tabItem` it ON it.name=lfi.item_code
        GROUP BY lf.name ORDER BY cost_kg DESC
    """, as_dict=True)
    context.formulations = forms

    if forms:
        context.sample_form = forms[len(forms) // 2]
        context.sample_items = frappe.db.sql("""
            SELECT item_code, item_name, qty_per_100kg
            FROM `tabLab Formulation Item` WHERE parent=%s ORDER BY qty_per_100kg DESC
        """, context.sample_form.formulation_no, as_dict=True)
    else:
        context.sample_form = None
        context.sample_items = []

    return context
