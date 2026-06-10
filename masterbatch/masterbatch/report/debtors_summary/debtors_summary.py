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
		{"fieldname": "label", "label": "Customer", "fieldtype": "Data", "width": 420},
		{"fieldname": "opening", "label": "Opening", "fieldtype": "Currency", "width": 180},
		{"fieldname": "invoiced", "label": "Invoiced", "fieldtype": "Currency", "width": 180},
		{"fieldname": "received", "label": "Received", "fieldtype": "Currency", "width": 180},
		{"fieldname": "outstanding", "label": "Outstanding", "fieldtype": "Currency", "width": 180},
	]

	# ── 1. Party financial data ───────────────────────────────────────────────
	# opening     = net of ALL entries before from_date
	# invoiced    = ALL positive entries in period (SI debits + JV debits = increases customer balance)
	# received    = ALL negative entries in period (PE credits + JV credits = decreases customer balance)
	# outstanding = net of ALL entries up to as_on_date (always correct)
	# Check: outstanding = opening + invoiced - received
	party_data = frappe.db.sql(
		"""
		SELECT
			c.customer_group  AS grp,
			ple.party         AS party,
			c.customer_name   AS party_name,
			SUM(CASE WHEN ple.posting_date < %(fd)s
				THEN ple.amount ELSE 0 END)                                        AS opening,
			SUM(CASE WHEN ple.amount > 0
					AND ple.posting_date >= %(fd)s AND ple.posting_date <= %(d)s
				THEN ple.amount ELSE 0 END)                                        AS invoiced,
			ABS(SUM(CASE WHEN ple.amount < 0
					AND ple.posting_date >= %(fd)s AND ple.posting_date <= %(d)s
				THEN ple.amount ELSE 0 END))                                       AS received,
			SUM(ple.amount)                                                        AS outstanding
		FROM `tabPayment Ledger Entry` ple
		INNER JOIN `tabCustomer` c ON c.name = ple.party
		WHERE
			ple.party_type   = 'Customer'
			AND ple.delinked = 0
			AND ple.posting_date <= %(d)s
			AND ple.company  = %(co)s
		GROUP BY c.customer_group, ple.party, c.customer_name
		HAVING ABS(SUM(ple.amount)) > 0.01
		ORDER BY c.customer_group, SUM(ple.amount) DESC
		""",
		{"fd": from_date, "d": as_on_date, "co": company},
		as_dict=True,
	)

	# ── 2. Customer Group tree — lft order = parents always before children ───
	cg_list = frappe.db.sql(
		"""
		SELECT name, parent_customer_group
		FROM `tabCustomer Group`
		ORDER BY lft
		""",
		as_dict=True,
	)

	cg_parent = {}
	cg_children = {}
	for cg in cg_list:
		cg_parent[cg["name"]] = cg.get("parent_customer_group") or ""
		p = cg.get("parent_customer_group") or ""
		if p:
			cg_children.setdefault(p, []).append(cg["name"])

	# ── 3. Customers indexed by their direct group ─────────────────────────────
	parties_by_group = {}
	for r in party_data:
		g = r.get("grp") or "Ungrouped"
		parties_by_group.setdefault(g, []).append(r)

	# ── 4. Depth map ───────────────────────────────────────────────────────────
	group_depth = {"All Customer Groups": -1}
	for cg in cg_list:
		gn = cg["name"]
		if gn == "All Customer Groups":
			continue
		p = cg.get("parent_customer_group") or ""
		group_depth[gn] = group_depth.get(p, -1) + 1

	# ── 5. Aggregate & has_data — bottom-up via reverse index ──────────────────
	group_agg = {}
	group_has_data = {}

	for idx in range(len(cg_list) - 1, -1, -1):
		cg = cg_list[idx]
		gn = cg["name"]
		o = iv = rc = os_ = 0.0
		hd = False
		for c in parties_by_group.get(gn, []):
			o += flt(c.get("opening"))
			iv += flt(c.get("invoiced"))
			rc += flt(c.get("received"))
			os_ += flt(c.get("outstanding"))
			hd = True
		for child in cg_children.get(gn, []):
			ca = group_agg.get(child) or {"opening": 0.0, "invoiced": 0.0, "received": 0.0, "outstanding": 0.0}
			o += ca["opening"]
			iv += ca["invoiced"]
			rc += ca["received"]
			os_ += ca["outstanding"]
			if group_has_data.get(child):
				hd = True
		group_agg[gn] = {"opening": o, "invoiced": iv, "received": rc, "outstanding": os_}
		group_has_data[gn] = hd

	# ── 6. Build rows ───────────────────────────────────────────────────────────
	rows = []
	gid_counter = [0]
	group_row_ids = {}

	for cg in cg_list:
		gn = cg["name"]
		if gn == "All Customer Groups":
			continue
		if not group_has_data.get(gn):
			continue
		depth = group_depth.get(gn, 0)
		parent_cg = cg.get("parent_customer_group") or ""
		parent_row_id = None
		if parent_cg and parent_cg != "All Customer Groups":
			parent_row_id = group_row_ids.get(parent_cg)
		gid_counter[0] += 1
		g_row_id = "G" + str(gid_counter[0])
		group_row_ids[gn] = g_row_id
		agg = group_agg.get(gn) or {"opening": 0.0, "invoiced": 0.0, "received": 0.0, "outstanding": 0.0}
		rows.append(
			{
				"row_id": g_row_id,
				"parent_id": parent_row_id,
				"party_id": None,
				"label": gn,
				"opening": agg["opening"],
				"invoiced": agg["invoiced"],
				"received": agg["received"],
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
					"received": flt(p.get("received")),
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
		o = iv = rc = os_ = 0.0
		for c in parties_by_group.get(grp, []):
			o += flt(c.get("opening"))
			iv += flt(c.get("invoiced"))
			rc += flt(c.get("received"))
			os_ += flt(c.get("outstanding"))
		rows.append(
			{
				"row_id": g_row_id,
				"parent_id": None,
				"party_id": None,
				"label": grp,
				"opening": o,
				"invoiced": iv,
				"received": rc,
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
					"received": flt(p.get("received")),
					"outstanding": flt(p.get("outstanding")),
					"indent": 1,
				}
			)

	# ── 8. Grand totals ──────────────────────────────────────────────────────────
	grand_opening = sum(flt(r.get("opening")) for r in party_data)
	grand_invoiced = sum(flt(r.get("invoiced")) for r in party_data)
	grand_received = sum(flt(r.get("received")) for r in party_data)
	grand_total = sum(flt(r.get("outstanding")) for r in party_data)

	report_summary = [
		{"value": grand_opening, "label": "Opening Balance", "datatype": "Currency", "currency": "INR", "indicator": "grey"},
		{"value": grand_invoiced, "label": "Invoiced", "datatype": "Currency", "currency": "INR", "indicator": "blue"},
		{"value": grand_received, "label": "Received", "datatype": "Currency", "currency": "INR", "indicator": "green"},
		{"value": grand_total, "label": "Net Receivable", "datatype": "Currency", "currency": "INR", "indicator": "orange"},
	]

	return columns, rows, None, None, report_summary
