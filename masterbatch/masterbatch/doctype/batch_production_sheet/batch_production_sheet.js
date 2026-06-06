frappe.ui.form.on('Batch Production Sheet', {
    refresh(frm) {
        // Guided helper button: pull the recipe from the Lab Formulation
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button('Get Raw Materials from Recipe', () => fill_from_formulation(frm, true));
        }
        // Post stock from the batch
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
            frm.add_custom_button('View Stock Entry', () => frappe.set_route('Form', 'Stock Entry', frm.doc.stock_entry));
        }
    },

    // Pick a finished item -> auto-find its approved formulation
    finished_item(frm) {
        if (frm.doc.finished_item && !frm.doc.formulation_no) {
            frappe.call({
                method: 'masterbatch.masterbatch.doctype.batch_production_sheet.batch_production_sheet.find_formulation',
                args: { finished_item: frm.doc.finished_item },
                callback: (r) => { if (r.message) frm.set_value('formulation_no', r.message); }
            });
        }
    },

    // Pick a formulation -> load finished item, shade and the recipe rows
    formulation_no(frm) {
        if (frm.doc.formulation_no) fill_from_formulation(frm, false);
    },

    // Change the planned qty -> rescale the recipe
    planned_qty(frm) {
        if (frm.doc.formulation_no && frm.doc.planned_qty) fill_from_formulation(frm, false);
    }
});

function fill_from_formulation(frm, alert) {
    if (!frm.doc.formulation_no) {
        if (alert) frappe.msgprint('Select a Finished Item or Lab Formulation first.');
        return;
    }
    frappe.call({
        method: 'masterbatch.masterbatch.doctype.batch_production_sheet.batch_production_sheet.get_formulation_items',
        args: { formulation: frm.doc.formulation_no, planned_qty: frm.doc.planned_qty || 0 },
        callback: (r) => {
            if (!r.message) return;
            if (r.message.finished_item) frm.set_value('finished_item', r.message.finished_item);
            if (r.message.shade_code) frm.set_value('shade_code', r.message.shade_code);
            frm.clear_table('consumption_items');
            (r.message.items || []).forEach((it) => {
                const row = frm.add_child('consumption_items');
                row.item_code = it.item_code;
                row.item_name = it.item_name;
                row.planned_qty = it.planned_qty;
                row.qty_consumed = it.qty_consumed;
                row.uom = it.uom || 'KG';
            });
            frm.refresh_field('consumption_items');
            if (alert) frappe.show_alert({ message: 'Raw materials loaded from recipe', indicator: 'green' });
        }
    });
}
