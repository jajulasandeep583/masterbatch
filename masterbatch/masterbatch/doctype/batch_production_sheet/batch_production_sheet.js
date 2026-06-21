frappe.ui.form.on('Batch Production Sheet', {
    onload(frm) {
        if (frm.is_new()) {
            if (!frm.doc.production_date) frm.set_value('production_date', frappe.datetime.get_today());
            // came from Sales Order "Create Batch" with finished item prefilled.
            // Skip when the batch was created from a BOM — its recipe is already loaded.
            if (frm.doc.finished_item && !frm.doc.formulation_no && !frm.doc.source_bom)
                load_recipe_for_item(frm);
        }
    },

    refresh(frm) {
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button('⟳ Load Raw Materials from Recipe', () => {
                // if only a finished item is set, resolve its recipe source (Formulation/BOM) first
                if (frm.doc.finished_item && !frm.doc.formulation_no && !frm.doc.source_bom) {
                    load_recipe_for_item(frm);
                } else {
                    fill_recipe(frm, true);
                }
            }).removeClass('btn-default').addClass('btn-primary');
        }
        // QC decision on the finished goods (works after submit via allow_on_submit)
        if (frm.doc.docstatus === 1 && frm.doc.qc_status !== 'Passed' && !frm.doc.stock_entry) {
            frm.add_custom_button('✓ QC Passed', () => set_qc(frm, 'Passed'))
                .removeClass('btn-default').addClass('btn-success');
            frm.add_custom_button('✗ QC Failed', () => set_qc(frm, 'Failed'))
                .removeClass('btn-default').addClass('btn-danger');
        }
        // Certificate of Analysis straight from the batch (print format + letter head from settings)
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button('🖨 Print COA', () => {
                if (!(frm.doc.qc_parameters || []).length) {
                    frappe.msgprint('Add QC Parameters and enter results first — the COA prints these values.');
                    return;
                }
                Promise.all([
                    frappe.db.get_single_value('Masterbatch Settings', 'coa_print_format'),
                    frappe.db.get_single_value('Masterbatch Settings', 'coa_letter_head')
                ]).then(([pf, lh]) => {
                    if (!pf) {
                        frappe.msgprint('Set a <b>COA Print Format</b> in Masterbatch Settings first.');
                        return;
                    }
                    let url = '/printview?doctype=' + encodeURIComponent(frm.doc.doctype) +
                        '&name=' + encodeURIComponent(frm.doc.name) +
                        '&format=' + encodeURIComponent(pf) + '&no_letterhead=0';
                    if (lh) url += '&letterhead=' + encodeURIComponent(lh);
                    window.open(url, '_blank');
                });
            }).removeClass('btn-default').addClass('btn-primary');
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
        if (frm.doc.source_bom) {
            frm.add_custom_button('Source BOM', () => frappe.set_route('Form', 'BOM', frm.doc.source_bom));
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

    // change planned qty -> rescale the recipe (from BOM or Lab Formulation)
    planned_qty(frm) {
        if ((frm.doc.source_bom || frm.doc.formulation_no) && frm.doc.planned_qty) fill_recipe(frm, false);
    },

    // entering the actual output -> show the loss % live (server re-confirms on save)
    actual_output_kg(frm) {
        compute_loss(frm);
    }
});

// live process-loss %: (raw material input − output) / input × 100
function compute_loss(frm) {
    const input = (frm.doc.consumption_items || []).reduce((s, r) => s + (r.qty_consumed || 0), 0);
    const out = frm.doc.actual_output_kg || 0;
    const rej = input > out ? input - out : 0;
    frm.set_value('rejection_kg', rej);
    frm.set_value('loss_percentage', input ? Math.round((rej / input) * 10000) / 100 : 0);
}

// recompute loss whenever a consumed quantity changes
frappe.ui.form.on('Batch Production Sheet Item', {
    qty_consumed(frm) { compute_loss(frm); },
    consumption_items_remove(frm) { compute_loss(frm); }
});

// QC parameter rows: pick a parameter from the QC Parameter master -> unit / spec /
// test method / limits auto-fill; entering a result auto-marks Pass / Fail.
frappe.ui.form.on('Batch QC Parameter', {
    parameter(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.parameter) return;
        frappe.db.get_value('QC Parameter', row.parameter,
            ['unit', 'specification', 'test_method', 'evaluation_type', 'min_value', 'max_value', 'target_text'])
            .then((r) => {
                const v = (r && r.message) || {};
                frappe.model.set_value(cdt, cdn, 'unit', v.unit);
                frappe.model.set_value(cdt, cdn, 'specification', v.specification);
                frappe.model.set_value(cdt, cdn, 'test_method', v.test_method);
                frappe.model.set_value(cdt, cdn, 'evaluation_type', v.evaluation_type);
                frappe.model.set_value(cdt, cdn, 'min_value', v.min_value);
                frappe.model.set_value(cdt, cdn, 'max_value', v.max_value);
                frappe.model.set_value(cdt, cdn, 'target_text', v.target_text);
                compute_qc_status(cdt, cdn);
            });
    },
    result(frm, cdt, cdn) {
        compute_qc_status(cdt, cdn);
    }
});

// mirror of server-side evaluate_qc_status (instant feedback in the grid)
function compute_qc_status(cdt, cdn) {
    const row = locals[cdt][cdn];
    const res = row.result;
    if (res === undefined || res === null || String(res).trim() === '') return; // no result yet
    const et = row.evaluation_type || 'Range';
    let status;
    if (et === 'Text Match') {
        status = (String(res).trim().toLowerCase() === String(row.target_text || '').trim().toLowerCase()) ? 'Pass' : 'Fail';
    } else {
        const val = parseFloat(String(res).trim());
        if (isNaN(val)) {
            status = 'Fail';
        } else if (et === 'Minimum') {
            status = (val >= (row.min_value || 0)) ? 'Pass' : 'Fail';
        } else if (et === 'Maximum') {
            status = (val <= (row.max_value || 0)) ? 'Pass' : 'Fail';
        } else {
            status = (val >= (row.min_value || 0) && val <= (row.max_value || 0)) ? 'Pass' : 'Fail';
        }
    }
    frappe.model.set_value(cdt, cdn, 'status', status);
}

// QC decision on the finished goods (works after submit via allow_on_submit)
function set_qc(frm, status) {
    frappe.db.set_value('Batch Production Sheet', frm.doc.name, 'qc_status', status).then(() => {
        frappe.show_alert({ message: 'QC marked ' + status, indicator: status === 'Passed' ? 'green' : 'red' });
        frm.reload_doc();
    });
}

// resolve the recipe source for the finished item (Lab Formulation OR its BOM), then load it
function load_recipe_for_item(frm) {
    if (!frm.doc.finished_item) return;
    frappe.call({
        method: 'masterbatch.masterbatch.doctype.batch_production_sheet.batch_production_sheet.find_recipe_source',
        args: { finished_item: frm.doc.finished_item },
        callback: (r) => {
            const m = r.message || {};
            if (m.formulation) {
                frm.doc.source_bom = null;
                frm.doc.formulation_no = m.formulation;
                frm.refresh_field('formulation_no');
                fill_recipe(frm, false);
            } else if (m.bom) {
                frm.doc.formulation_no = null;
                frm.doc.source_bom = m.bom;
                frm.refresh_field('source_bom');
                fill_recipe(frm, false);
            } else {
                frappe.show_alert({
                    message: 'No Lab Formulation or BOM found for ' + frm.doc.finished_item +
                        '. Enter the raw materials manually.', indicator: 'orange'
                }, 6);
            }
        }
    });
}

// pull recipe rows and fill the consumption table, scaled to the planned qty.
// Source is the batch's BOM (no Lab Formulation needed) or its Lab Formulation.
function fill_recipe(frm, alert) {
    let method, args;
    if (frm.doc.source_bom) {
        method = 'masterbatch.masterbatch.doctype.batch_production_sheet.batch_production_sheet.get_bom_items';
        args = { bom: frm.doc.source_bom, planned_qty: frm.doc.planned_qty || 0 };
    } else if (frm.doc.formulation_no) {
        method = 'masterbatch.masterbatch.doctype.batch_production_sheet.batch_production_sheet.get_formulation_items';
        args = { formulation: frm.doc.formulation_no, planned_qty: frm.doc.planned_qty || 0 };
    } else {
        if (alert) frappe.msgprint('Select a Finished Item, BOM or Lab Formulation first.');
        return;
    }
    frappe.call({
        method: method,
        args: args,
        callback: (r) => {
            if (!r.message) return;
            // set parent fields WITHOUT triggering their change handlers
            frm.doc.finished_item = r.message.finished_item;
            if (r.message.shade_code) frm.doc.shade_code = r.message.shade_code;
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
                row.uom = it.uom;  // server resolves to the item's stock UOM (portable across sites)
            });
            frm.refresh_field('consumption_items');
            frappe.show_alert({ message: (r.message.items || []).length + ' raw materials loaded', indicator: 'green' });
        }
    });
}
