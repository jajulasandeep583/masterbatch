import frappe

LETTERHEAD = """
<div style="display:flex;align-items:center;justify-content:space-between;border-bottom:3px solid #7c3aed;padding-bottom:8px;">
  <div style="display:flex;align-items:center;gap:12px;">
    <img src="/assets/masterbatch/images/masterbatch-logo.svg" style="height:46px;width:46px;"/>
    <div>
      <div style="font-size:20px;font-weight:700;color:#7c3aed;">Capital Colours</div>
      <div style="font-size:11px;color:#555;">Masterbatch &amp; Colour Compounds &bull; capitalcolours.co.in</div>
    </div>
  </div>
  <div style="text-align:right;font-size:11px;color:#555;">
    Plot 1, Industrial Area, Bengaluru,<br/>Karnataka 560001, India<br/>GSTIN: 29AAACM1001C1ZB
  </div>
</div>
"""

SALES_HTML = """
<div style="font-family:Helvetica,Arial,sans-serif;font-size:12px;color:#222;">
  <h2 style="text-align:center;margin:6px 0 2px;letter-spacing:2px;color:#7c3aed;">TAX INVOICE</h2>
  <table style="width:100%;margin-bottom:8px;font-size:11px;">
    <tr>
      <td style="vertical-align:top;width:55%;">
        <b>Bill To:</b><br/>
        <b>{{ doc.customer_name }}</b><br/>
        {% if doc.address_display %}{{ doc.address_display }}{% endif %}
        {% if doc.billing_address_gstin %}<br/>GSTIN: {{ doc.billing_address_gstin }}{% endif %}
        {% if doc.place_of_supply %}<br/>Place of Supply: {{ doc.place_of_supply }}{% endif %}
      </td>
      <td style="vertical-align:top;text-align:right;">
        <b>Invoice No:</b> {{ doc.name }}<br/>
        <b>Date:</b> {{ frappe.utils.formatdate(doc.posting_date) }}<br/>
        {% if doc.due_date %}<b>Due Date:</b> {{ frappe.utils.formatdate(doc.due_date) }}<br/>{% endif %}
        {% if doc.po_no %}<b>PO No:</b> {{ doc.po_no }}{% endif %}
      </td>
    </tr>
  </table>
  <table style="width:100%;border-collapse:collapse;font-size:11px;" border="1">
    <thead style="background:#f3e8ff;">
      <tr>
        <th style="padding:5px;">#</th><th style="padding:5px;text-align:left;">Item</th>
        <th style="padding:5px;">HSN</th><th style="padding:5px;">Qty</th>
        <th style="padding:5px;text-align:right;">Rate</th><th style="padding:5px;text-align:right;">Amount</th>
      </tr>
    </thead>
    <tbody>
      {% for row in doc.items %}
      <tr>
        <td style="padding:5px;text-align:center;">{{ loop.index }}</td>
        <td style="padding:5px;">{{ row.item_name }}</td>
        <td style="padding:5px;text-align:center;">{{ row.gst_hsn_code or '' }}</td>
        <td style="padding:5px;text-align:center;">{{ row.qty|round(2) }} {{ row.uom }}</td>
        <td style="padding:5px;text-align:right;">{{ frappe.utils.fmt_money(row.rate, currency=doc.currency) }}</td>
        <td style="padding:5px;text-align:right;">{{ frappe.utils.fmt_money(row.amount, currency=doc.currency) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  <table style="width:100%;margin-top:8px;font-size:11px;">
    <tr>
      <td style="vertical-align:top;width:55%;">
        <b>Amount in Words:</b><br/>{{ doc.in_words }}
      </td>
      <td style="text-align:right;">
        <table style="margin-left:auto;font-size:11px;">
          <tr><td style="padding:2px 12px;">Taxable Amount</td><td style="text-align:right;">{{ frappe.utils.fmt_money(doc.net_total, currency=doc.currency) }}</td></tr>
          {% for t in doc.taxes %}
          <tr><td style="padding:2px 12px;">{{ t.description }}</td><td style="text-align:right;">{{ frappe.utils.fmt_money(t.tax_amount, currency=doc.currency) }}</td></tr>
          {% endfor %}
          <tr style="font-weight:700;border-top:2px solid #7c3aed;">
            <td style="padding:4px 12px;">Grand Total</td>
            <td style="text-align:right;">{{ frappe.utils.fmt_money(doc.grand_total, currency=doc.currency) }}</td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
  <div style="margin-top:24px;display:flex;justify-content:space-between;font-size:11px;color:#555;">
    <div>Subject to Bengaluru jurisdiction. E. &amp; O.E.</div>
    <div style="text-align:right;">For <b>Capital Colours</b><br/><br/><br/>Authorised Signatory</div>
  </div>
</div>
"""

PURCHASE_HTML = SALES_HTML.replace("TAX INVOICE", "PURCHASE INVOICE") \
    .replace("Bill To:", "Supplier:") \
    .replace("doc.customer_name", "doc.supplier_name") \
    .replace("doc.billing_address_gstin", "doc.supplier_gstin") \
    .replace("For <b>Capital Colours</b>", "Received by <b>Capital Colours</b>")

def make_letterhead():
    if frappe.db.exists("Letter Head", "Capital Colours"):
        lh = frappe.get_doc("Letter Head", "Capital Colours")
    else:
        lh = frappe.new_doc("Letter Head"); lh.letter_head_name = "Capital Colours"
    lh.content = LETTERHEAD
    lh.source = "HTML"
    lh.is_default = 1
    lh.disabled = 0
    lh.save(ignore_permissions=True)
    print("Letter Head ready")

def make_pf(name, doctype, html):
    if frappe.db.exists("Print Format", name):
        pf = frappe.get_doc("Print Format", name)
    else:
        pf = frappe.new_doc("Print Format"); pf.name = name
    pf.doc_type = doctype
    pf.module = "Masterbatch"
    pf.print_format_type = "Jinja"
    pf.custom_format = 1
    pf.standard = "No"
    pf.html = html
    pf.letter_head = "Capital Colours"
    pf.save(ignore_permissions=True)
    # set as default for the doctype
    ps_name = doctype + "-main-default_print_format"
    if frappe.db.exists("Property Setter", ps_name):
        frappe.db.set_value("Property Setter", ps_name, "value", name)
    else:
        frappe.make_property_setter({
            "doctype": doctype, "doctype_or_field": "DocType",
            "property": "default_print_format", "value": name, "property_type": "Data",
        }, ignore_validate=True)
    print("Print Format ready + set default:", name)

def run():
    make_letterhead()
    make_pf("Capital Colours Tax Invoice", "Sales Invoice", SALES_HTML)
    make_pf("Capital Colours Purchase Bill", "Purchase Invoice", PURCHASE_HTML)
    frappe.db.commit()
    print("DONE print formats")
