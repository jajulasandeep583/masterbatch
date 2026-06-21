"""Capital Colours — Certificate of Analysis print formats.

Three Jinja print formats sharing one certificate body:
  - "Capital Colours COA"          on Sales Invoice  (one page per batch on the items)
  - "Capital Colours COA - DN"     on Delivery Note  (same)
  - "Capital Colours COA - Batch"  on Batch Production Sheet (single certificate)

Create/update them with:
  bench --site colour execute masterbatch.demo.coa_print_format.run
"""

import frappe

# certificate body — expects Jinja vars: b (Batch Production Sheet doc),
# coa_no, ref_html (reference/customer lines), qty_html (qty supplied line), cert_date
CERT_BODY = """
  <h2 style="text-align:center;margin:6px 0 2px;letter-spacing:2px;color:#7c3aed;">CERTIFICATE OF ANALYSIS</h2>
  <div style="text-align:center;font-size:11px;color:#555;margin-bottom:10px;">Quality Assurance Department</div>

  <table style="width:100%;font-size:11px;margin-bottom:8px;">
    <tr>
      <td style="vertical-align:top;width:50%;">
        <b>Product:</b> {{ frappe.db.get_value("Item", b.finished_item, "item_name") or b.finished_item }}<br/>
        <b>Item Code:</b> {{ b.finished_item }}<br/>
        {% if b.shade_code %}<b>Shade Code:</b> {{ b.shade_code }}<br/>{% endif %}
        <b>Batch No:</b> {{ b.batch_no }}<br/>
        <b>Mfg Date:</b> {{ frappe.utils.formatdate(b.production_date) }}
      </td>
      <td style="vertical-align:top;text-align:right;">
        <b>COA No:</b> {{ coa_no }}<br/>
        <b>Date:</b> {{ frappe.utils.formatdate(cert_date) }}<br/>
        {{ ref_html }}
        {{ qty_html }}
      </td>
    </tr>
  </table>

  <table style="width:100%;border-collapse:collapse;font-size:11px;" border="1">
    <thead style="background:#f3e8ff;">
      <tr>
        <th style="padding:5px;">#</th>
        <th style="padding:5px;text-align:left;">Parameter</th>
        <th style="padding:5px;">Test Method</th>
        <th style="padding:5px;">Unit</th>
        <th style="padding:5px;">Specification</th>
        <th style="padding:5px;">Result</th>
        <th style="padding:5px;">Status</th>
      </tr>
    </thead>
    <tbody>
      {% for p in b.qc_parameters %}
      <tr>
        <td style="padding:5px;text-align:center;">{{ loop.index }}</td>
        <td style="padding:5px;">{{ p.parameter }}</td>
        <td style="padding:5px;text-align:center;">{{ p.test_method or '' }}</td>
        <td style="padding:5px;text-align:center;">{{ p.unit or '' }}</td>
        <td style="padding:5px;text-align:center;">{{ p.specification or '' }}</td>
        <td style="padding:5px;text-align:center;font-weight:600;">{{ p.result or '' }}</td>
        <td style="padding:5px;text-align:center;font-weight:700;color:{{ '#dc2626' if p.status == 'Fail' else '#16a34a' }};">{{ p.status or 'Pass' }}</td>
      </tr>
      {% else %}
      <tr><td colspan="7" style="padding:8px;text-align:center;color:#888;">QC parameters not recorded for this batch.</td></tr>
      {% endfor %}
    </tbody>
  </table>

  {% set passed = (b.qc_status or '') == 'Passed' %}
  <div style="margin-top:14px;border:2px solid {{ '#16a34a' if passed else '#dc2626' }};border-radius:6px;padding:10px 14px;display:flex;justify-content:space-between;align-items:center;">
    <div style="font-size:11px;">
      {% if passed %}This batch conforms to Capital Colours quality specifications and is approved for supply.{% else %}This batch does NOT conform to Capital Colours quality specifications.{% endif %}
    </div>
    <div style="font-size:16px;font-weight:800;letter-spacing:2px;color:{{ '#16a34a' if passed else '#dc2626' }};">
      {{ 'PASSED &#10003;' if passed else (b.qc_status or 'PENDING')|upper }}
    </div>
  </div>

  <div style="margin-top:28px;display:flex;justify-content:space-between;font-size:11px;color:#555;">
    <div>Tested by: {{ b.operator or 'QC Lab' }}<br/><br/><br/>QC Chemist</div>
    <div style="text-align:right;">For <b>Capital Colours</b><br/><br/><br/>QC Manager / Authorised Signatory</div>
  </div>
"""

# Sales Invoice / Delivery Note: one certificate page per distinct batch on the items.
# Each row's batch is the one chosen in "Batch (COA)" OR, if none was chosen, the
# latest QC-Passed batch for that item — so the COA prints reliably without manual
# batch selection.
SALES_COA_HTML = """
<div style="font-family:Helvetica,Arial,sans-serif;font-size:12px;color:#222;">
{% set seen = [] %}
{% for row in doc.items %}
{% set bname = row.batch_production_sheet or frappe.db.get_value("Batch Production Sheet", {"finished_item": row.item_code, "docstatus": 1, "qc_status": "Passed"}, "name", order_by="production_date desc") %}
{% if bname and bname not in seen %}
{% set _x = seen.append(bname) %}
{% set b = frappe.get_doc("Batch Production Sheet", bname) %}
{% set coa_no = "COA/" ~ doc.name ~ "/" ~ (seen | length) %}
{% set cert_date = doc.posting_date %}
{% set ref_html = "<b>Reference:</b> " ~ doc.doctype ~ " " ~ doc.name ~ "<br/><b>Customer:</b> " ~ (doc.customer_name or doc.customer) ~ "<br/>" %}
{% set qty_html = "<b>Qty Supplied:</b> " ~ (row.qty | round(2)) ~ " " ~ (row.uom or b.finished_item) %}
<div style="{% if seen | length > 1 %}page-break-before:always;{% endif %}">
""" + CERT_BODY + """
</div>
{% endif %}
{% endfor %}
{% if not seen %}
<div style="padding:20px;text-align:center;color:#888;">
  No QC-Passed batch was found for the items on this document. Produce and QC-pass a batch
  for these items (or set <b>Batch (COA)</b> on the rows) to print a Certificate of Analysis.
</div>
{% endif %}
</div>
"""

# Batch Production Sheet: the doc itself is the batch
BATCH_COA_HTML = """
<div style="font-family:Helvetica,Arial,sans-serif;font-size:12px;color:#222;">
{% set b = doc %}
{% set coa_no = "COA/" ~ doc.name %}
{% set cert_date = frappe.utils.today() %}
{% set ref_html = "<b>Reference:</b> Batch Production Sheet<br/>" %}
{% set qty_html = "<b>Batch Output:</b> " ~ ((doc.actual_output_kg or doc.planned_qty) | round(2)) ~ " KG" %}
""" + CERT_BODY + """
</div>
"""


def make_pf(name, doctype, html):
    if frappe.db.exists("Print Format", name):
        pf = frappe.get_doc("Print Format", name)
    else:
        pf = frappe.new_doc("Print Format")
        pf.name = name
    pf.doc_type = doctype
    pf.module = "Masterbatch"
    pf.print_format_type = "Jinja"
    pf.custom_format = 1
    pf.standard = "No"
    pf.html = html
    # only attach the branded letter head if this site actually has it
    if frappe.db.exists("Letter Head", "Capital Colours"):
        pf.letter_head = "Capital Colours"
    pf.save(ignore_permissions=True)
    print("Print Format ready:", name, "->", doctype)


def run():
    make_pf("Capital Colours COA", "Sales Invoice", SALES_COA_HTML)
    make_pf("Capital Colours COA - DN", "Delivery Note", SALES_COA_HTML)
    make_pf("Capital Colours COA - Batch", "Batch Production Sheet", BATCH_COA_HTML)
    frappe.db.commit()
    print("DONE COA print formats")
