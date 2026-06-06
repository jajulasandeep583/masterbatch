frappe.ui.form.on('Batch Production Sheet', {
    onload(frm) {
        if (frm.is_new()) {
            if (!frm.doc.production_date) frm.set_value('production_date', frappe.datetime.get_today());
            // came from Sales Order "Create Batch" with finished item prefilled
            if (frm.doc.finished_item && !frm.doc.formulation_no) load_recipe_for_item(frm);
        }
    },

    refresh(frm) {
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button('⟳ Load Raw Materials from Recipe', () => fill_recipe(frm, true))
                .removeClass('btn-default').addClass('btn-primary');
        }
        if (frm.doc.docstatus === 1 && !frm.doc.stock_entry) {
            const passed = (frm.doc.qc_status === 'Passed');
            const btn = frm.add_custom_button('▶ Create Stock Entry (post production)', () => {
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
            });
            btn.removeClass('btn-default').addClass(passed ? 'btn-primary' : 'btn-warning');
            if (!passed) {
                frm.dashboard.set_headline('⚠ QC is "' + (frm.doc.qc_status || 'Pending') +
                    '". Finished goods can be posted to stock only after QC is Passed.');
            }
        }
        if (frm.doc.stock_entry) {
            frm.add_custom_button('✓ View Stock Entry', () => frappe.set_route('Form', 'Stock Entry', frm.doc.stock_entry))
                .removeClass('btn-default').addClass('btn-success');
        }
        if (frm.doc.formulation_no) {
            frm.add_custom_button('Recipe', () => frappe.set_route('Form', 'Lab Formulation', frm.doc.formulation_no));
        }
    },

    // user picked the finished item -> find its recipe and load it
    finished_item(frm) {
        if (frm.doc.finished_item && !frm.doc.formulation_no) load_recipe_for_item(frm);
    },

    // user picked the formulation directly -> load it
    formulation_no(frm) {
        if (frm.doc.formulation_no) fill_recipe(frm, false);
    },

    // change planned qty -> rescale the recipe
    planned_qty(frm) {
        if (frm.doc.formulation_no && frm.doc.planned_qty) fill_recipe(frm, false);
    }
});

// find the approved formulation for the finished item, then load it
function load_recipe_for_item(frm) {
    frappe.call({
        method: 'masterbatch.masterbatch.doctype.batch_production_sheet.batch_production_sheet.find_formulation',
        args: { finished_item: frm.doc.finished_item },
        callback: (r) => {
            if (r.message) {
                frm.doc.formulation_no = r.message;
                frm.refresh_field('formulation_no');
                fill_recipe(frm, false);
            }
        }
    });
}

// pull recipe rows and fill the consumption table (no event re-trigger)
function fill_recipe(frm, alert) {
    if (!frm.doc.formulation_no) {
        if (alert) frappe.msgprint('Select a Finished Item or Lab Formulation first.');
        return;
    }
    frappe.call({
        method: 'masterbatch.masterbatch.doctype.batch_production_sheet.batch_production_sheet.get_formulation_items',
        args: { formulation: frm.doc.formulation_no, planned_qty: frm.doc.planned_qty || 0 },
        callback: (r) => {
            if (!r.message) return;
            // set parent fields WITHOUT triggering their change handlers
            frm.doc.finished_item = r.message.finished_item;
            frm.doc.shade_code = r.message.shade_code;
            frm.refresh_field('finished_item');
            frm.refresh_field('shade_code');
            // fill the raw-material table
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
            frappe.show_alert({ message: (r.message.items || []).length + ' raw materials loaded from recipe', indicator: 'green' });
        }
    });
}
