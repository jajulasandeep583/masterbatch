// Masterbatch: create a Batch Production Sheet straight from a BOM.
// Recipe (raw-material consumption) is taken from the BOM components, so a
// Lab Formulation is NOT required for the batch. Standalone toolbar button.
frappe.ui.form.on('BOM', {
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Make Batch Production Sheet'), () => {
                frappe.model.open_mapped_doc({
                    method: 'masterbatch.masterbatch.doctype.batch_production_sheet.batch_production_sheet.make_batch_sheet',
                    frm: frm,
                });
            }).removeClass('btn-default').addClass('btn-primary');
        }
    }
});
