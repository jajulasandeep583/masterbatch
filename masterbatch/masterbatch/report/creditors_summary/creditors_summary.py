import frappe
from frappe.utils import flt, nowdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	as_on_date = filters.get("as_on_date") or nowdate()
	company = filters.get("company") or frappe.db.get_default("Company")

	if filters.get("from_date"):
		from_date = filters.get("from_date")
	else:
		fy_start = frappe.db.get_value(
			"Fiscal Year",
			{"year_start_date": ("<=", as_on_date), "year_end_date": (">=", as_on_date)},
			"year_start_date",
		)
		from_date = str(fy_start) if fy_start else as_on_date

	columns = [
		{"fieldname": "row_id", "label": "Row ID", "fieldtype": "Data", "hidden": 1},
		{"fieldname": "parent_id", "label": "Parent ID", "fieldtype": "Data", "hidden": 1},
		{"fieldname": "party_id", "label": "Party ID", "fieldtype": "Data", "hidden": 1},
		{"fieldname": "label", "label": "Supplier", "fieldtype": "Data", "width": 430},
		{"fieldname": "opening", "label": "Opening", "fieldtype": "Currency", "width": 180},
		{"fieldname": "invoiced", "label": "Invoiced", "fieldtype": "Currency", "width": 180},
		{"fieldname": "paid", "label": "Paid", "fieldtype": "Currency", "width": 180},
		{"fieldname": "outstanding", "label": "Outstanding", "fieldtype": "Currency", "width": 180},
	]

	# ── 1. Party financial data ───────────────────────────────────────────────
	# opening     = net of ALL entries before from_date
	# invoiced    = ALL positive entries in period (PI debits + JV debits = increases payable)
	# paid        = ALL negative entries in period (PE credits + JV credits = decreases payable)
	# outstanding = net of ALL entries up to as_on_date (always correct)
	# Check: outstanding = opening + invoiced - paid
	party_data = frappe.db.sql(
		"""
		SELECT
			s.supplier_group  AS grp,
			ple.party         AS party,
			s.supplier_name   AS party_name,
			SUM(CASE WHEN ple.posting_date < %(fd)s
				THEN ple.amount ELSE 0 END)                                        AS opening,
			SUM(CASE WHEN ple.amount > 0
					AND ple.posting_date >= %(fd)s AND ple.posting_date <= %(d)s
				THEN ple.amount ELSE 0 END)                                        AS invoiced,
			ABS(SUM(CASE WHEN ple.amount < 0
					AND ple.posting_date >= %(fd)s AND ple.posting_date <= %(d)s
				THEN ple.amount ELSE 0 END))                                       AS paid,
			SUM(ple.amount)                                                        AS outstanding
		FROM `tabPayment Ledger Entry` ple
		INNER JOIN `tabSupplier` s ON s.name = ple.party
		WHERE
			ple.party_type   = 'Supplier'
			AND ple.delinked = 0
			AND ple.posting_date <= %(d)s
			AND ple.company  = %(co)s
		GROUP BY s.supplier_group, ple.party, s.supplier_name
		HAVING ABS(SUM(ple.amount)) > 0.01
		ORDER BY s.supplier_group, SUM(ple.amount) DESC
		""",
		{"fd": from_date, "d": as_on_date, "co": company},
		as_dict=True,
	)

	# ── 2. Supplier Group tree — lft order = parents always before children ───
	cg_list = frappe.db.sql(
		"""
		SELECT name, parent_supplier_group
		FROM `tabSupplier Group`
		ORDER BY lft
		""",
		as_dict=True,
	)

	cg_parent = {}
	cg_children = {}
	for cg in cg_list:
		cg_parent[cg["name"]] = cg.get("parent_supplier_group") or ""
		p = cg.get("parent_supplier_group") or ""
		if p:
			cg_children.setdefault(p, []).append(cg["name"])

	# ── 3. Suppliers indexed by their direct group ─────────────────────────────
	parties_by_group = {}
	for r in party_data:
		g = r.get("grp") or "Ungrouped"
		parties_by_group.setdefault(g, []).append(r)

	# ── 4. Depth map ───────────────────────────────────────────────────────────
	group_depth = {"All Supplier Groups": -1}
	for cg in cg_list:
		gn = cg["name"]
		if gn == "All Supplier Groups":
			continue
		p = cg.get("parent_supplier_group") or ""
		group_depth[gn] = group_depth.get(p, -1) + 1

	# ── 5. Aggregate & has_data — bottom-up via reverse index ──────────────────
	group_agg = {}
	group_has_data = {}

	for idx in range(len(cg_list) - 1, -1, -1):
		cg = cg_list[idx]
		gn = cg["name"]
		o = iv = pd = os_ = 0.0
		hd = False
		for c in parties_by_group.get(gn, []):
			o += flt(c.get("opening"))
			iv += flt(c.get("invoiced"))
			pd += flt(c.get("paid"))
			os_ += flt(c.get("outstanding"))
			hd = True
		for child in cg_children.get(gn, []):
			ca = group_agg.get(child) or {"opening": 0.0, "invoiced": 0.0, "paid": 0.0, "outstanding": 0.0}
			o += ca["opening"]
			iv += ca["invoiced"]
			pd += ca["paid"]
			os_ += ca["outstanding"]
			if group_has_data.get(child):
				hd = True
		group_agg[gn] = {"opening": o, "invoiced": iv, "paid": pd, "outstanding": os_}
		group_has_data[gn] = hd

	# ── 6. Build rows ───────────────────────────────────────────────────────────
	rows = []
	gid_counter = [0]
	group_row_ids = {}

	for cg in cg_list:
		gn = cg["name"]
		if gn == "All Supplier Groups":
			continue
		if not group_has_data.get(gn):
			continue
		depth = group_depth.get(gn, 0)
		parent_cg = cg.get("parent_supplier_group") or ""
		parent_row_id = None
		if parent_cg and parent_cg != "All Supplier Groups":
			parent_row_id = group_row_ids.get(parent_cg)
		gid_counter[0] += 1
		g_row_id = "G" + str(gid_counter[0])
		group_row_ids[gn] = g_row_id
		agg = group_agg.get(gn) or {"opening": 0.0, "invoiced": 0.0, "paid": 0.0, "outstanding": 0.0}
		rows.append(
			{
				"row_id": g_row_id,
				"parent_id": parent_row_id,
				"party_id": None,
				"label": gn,
				"opening": agg["opening"],
				"invoiced": agg["invoiced"],
				"paid": agg["paid"],
				"outstanding": agg["outstanding"],
				"indent": depth,
			}
		)
		for p in parties_by_group.get(gn, []):
			gid_counter[0] += 1
			rows.append(
				{
					"row_id": "P" + str(gid_counter[0]),
					"parent_id": g_row_id,
					"party_id": p.get("party") or "",
					"label": p.get("party_name") or p.get("party") or "",
					"opening": flt(p.get("opening")),
					"invoiced": flt(p.get("invoiced")),
					"paid": flt(p.get("paid")),
					"outstanding": flt(p.get("outstanding")),
					"indent": depth + 1,
				}
			)

	# ── 7. Fallback for groups not in ERPNext tree ──────────────────────────────
	known_groups = set(cg_parent.keys())
	for grp in sorted(parties_by_group.keys()):
		if grp in known_groups:
			continue
		gid_counter[0] += 1
		g_row_id = "G" + str(gid_counter[0])
		o = iv = pd = os_ = 0.0
		for c in parties_by_group.get(grp, []):
			o += flt(c.get("opening"))
			iv += flt(c.get("invoiced"))
			pd += flt(c.get("paid"))
			os_ += flt(c.get("outstanding"))
		rows.append(
			{
				"row_id": g_row_id,
				"parent_id": None,
				"party_id": None,
				"label": grp,
				"opening": o,
				"invoiced": iv,
				"paid": pd,
				"outstanding": os_,
				"indent": 0,
			}
		)
		for p in parties_by_group.get(grp, []):
			gid_counter[0] += 1
			rows.append(
				{
					"row_id": "P" + str(gid_counter[0]),
					"parent_id": g_row_id,
					"party_id": p.get("party") or "",
					"label": p.get("party_name") or p.get("party") or "",
					"opening": flt(p.get("opening")),
					"invoiced": flt(p.get("invoiced")),
					"paid": flt(p.get("paid")),
					"outstanding": flt(p.get("outstanding")),
					"indent": 1,
				}
			)

	# ── 8. Grand totals ──────────────────────────────────────────────────────────
	grand_opening = sum(flt(r.get("opening")) for r in party_data)
	grand_invoiced = sum(flt(r.get("invoiced")) for r in party_data)
	grand_paid = sum(flt(r.get("paid")) for r in party_data)
	grand_total = sum(flt(r.get("outstanding")) for r in party_data)

	report_summary = [
		{"value": grand_opening, "label": "Opening Balance", "datatype": "Currency", "currency": "INR", "indicator": "grey"},
		{"value": grand_invoiced, "label": "Invoiced", "datatype": "Currency", "currency": "INR", "indicator": "orange"},
		{"value": grand_paid, "label": "Paid", "datatype": "Currency", "currency": "INR", "indicator": "green"},
		{"value": grand_total, "label": "Net Payable", "datatype": "Currency", "currency": "INR", "indicator": "red"},
	]

	return columns, rows, None, None, report_summary
