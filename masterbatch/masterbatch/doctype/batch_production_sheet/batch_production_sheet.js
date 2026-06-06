frappe.ui.form.on('Batch Production Sheet', {
    refresh(frm) {
        if (frm.doc.docstatus === 1 && !frm.doc.stock_entry) {
            frm.add_custom_button('Create Stock Entry', () => {
                frappe.call({
                    method: 'masterbatch.masterbatch.doctype.batch_production_sheet.batch_production_sheet.make_stock_entry',
                    args: { batch: frm.doc.name },
                    freeze: true,
                    freeze_message: 'Posting stock: consuming raw materials, producing finished goods...',
                    callback: (r) => {
                        if (r.message) {
                            frappe.show_alert({ message: 'Stock Entry ' + r.message + ' posted', indicator: 'green' });
                            frm.reload_doc();
                        }
                    }
                });
            }, 'Actions');
        }
        if (frm.doc.stock_entry) {
            frm.add_custom_button('View Stock Entry', () => {
                frappe.set_route('Form', 'Stock Entry', frm.doc.stock_entry);
            });
        }
    }
});
