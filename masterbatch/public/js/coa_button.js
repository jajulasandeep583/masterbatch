// Capital Colours — Certificate of Analysis (COA) from Sales Invoice / Delivery Note.
// Pick the QC-passed batch on each item row, then print the COA without leaving the form.

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
        const with_batch = (frm.doc.items || []).filter((r) => r.batch_production_sheet);
        if (!with_batch.length) {
            frappe.msgprint('Select <b>Batch (COA)</b> on the item rows first — only QC-Passed batches can be certified.');
            return;
        }
        const url = '/printview?doctype=' + encodeURIComponent(frm.doc.doctype) +
            '&name=' + encodeURIComponent(frm.doc.name) +
            '&format=' + encodeURIComponent(COA_FORMATS[frm.doc.doctype]) +
            '&no_letterhead=0&letterhead=' + encodeURIComponent('Capital Colours');
        window.open(url, '_blank');
    }).removeClass('btn-default').addClass('btn-primary');
}

['Sales Invoice', 'Delivery Note'].forEach((dt) => {
    frappe.ui.form.on(dt, {
        setup: coa_set_batch_query,
        refresh: coa_add_print_button,
    });
});
