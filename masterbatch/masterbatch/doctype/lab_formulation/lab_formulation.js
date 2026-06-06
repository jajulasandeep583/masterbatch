frappe.ui.form.on('Lab Formulation', {
    refresh(frm) {
        if (frm.doc.docstatus === 1 && !frm.doc.bom) {
            frm.add_custom_button('Create Production BOM', () => {
                frappe.call({
                    method: 'masterbatch.masterbatch.doctype.lab_formulation.lab_formulation.make_bom',
                    args: { formulation: frm.doc.name },
                    freeze: true,
                    freeze_message: 'Generating BOM from formulation...',
                    callback: (r) => {
                        if (r.message) {
                            frappe.show_alert({ message: 'Production BOM ' + r.message + ' linked', indicator: 'green' });
                            frm.reload_doc();
                        }
                    }
                });
            }, 'Actions');
        }
        if (frm.doc.bom) {
            frm.add_custom_button('View Production BOM', () => {
                frappe.set_route('Form', 'BOM', frm.doc.bom);
            });
        }
    }
});
