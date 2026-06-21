// Capital Colours — Certificate of Analysis (COA) from Sales Invoice / Delivery Note.
// The batch on each item row can be chosen in "Batch (COA)"; if left blank the COA
// print format resolves the latest QC-Passed batch for that item automatically, so
// the COA prints reliably. Sales Invoice rows also show live Available Qty.

const COA_FORMATS = {
    'Sales Invoice': 'Capital Colours COA',
    'Delivery Note': 'Capital Colours COA - DN',
};

function coa_set_batch_query(frm) {
    // only QC-Passed, submitted batches of the row's item can be certified
    frm.set_query('batch_production_sheet', 'items', function (doc, cdt, cdn) {
        const row = locals[cdt][cdn];
        const filters = { docstatus: 1, qc_status: 'Passed' };
        if (row.item_code) filters.finished_item = row.item_code;
        return { filters };
    });
}

function coa_add_print_button(frm) {
    if (frm.is_new()) return;
    frm.add_custom_button('🖨 Print COA', () => {
        // letter head from Masterbatch Settings (falls back to none if not set)
        frappe.db.get_single_value('Masterbatch Settings', 'coa_letter_head').then((lh) => {
            let url = '/printview?doctype=' + encodeURIComponent(frm.doc.doctype) +
                '&name=' + encodeURIComponent(frm.doc.name) +
                '&format=' + encodeURIComponent(COA_FORMATS[frm.doc.doctype]) +
                '&no_letterhead=0';
            if (lh) url += '&letterhead=' + encodeURIComponent(lh);
            window.open(url, '_blank');
        });
    }).removeClass('btn-default').addClass('btn-primary');
}

['Sales Invoice', 'Delivery Note'].forEach((dt) => {
    frappe.ui.form.on(dt, {
        setup: coa_set_batch_query,
        refresh: coa_add_print_button,
    });
});

// Live available stock when picking an item on a Sales Invoice (same as Sales Order)
frappe.ui.form.on('Sales Invoice Item', {
    item_code(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.item_code) return;
        frappe.call({
            method: 'masterbatch.sales_tools.get_item_qty',
            args: { item_code: row.item_code, warehouse: row.warehouse || '' },
            callback: (r) => {
                const qty = (r.message != null) ? r.message : 0;
                frappe.model.set_value(cdt, cdn, 'available_qty', qty);
                if (qty <= 0) {
                    frappe.show_alert({ message: row.item_code + ' — 0 in stock', indicator: 'orange' }, 5);
                } else {
                    frappe.show_alert({ message: row.item_code + ': ' + qty + ' available in stock', indicator: 'green' }, 5);
                }
            }
        });
    }
});
