// Masterbatch: show available stock when picking an item on a Sales Order, and
// raise a draft raw-material Material Request (exploded from the recipe) when short.

frappe.ui.form.on('Sales Order Item', {
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
                    frappe.show_alert({
                        message: row.item_code + ' — 0 in stock. Use "Create > Raw Material Request" to procure raw materials.',
                        indicator: 'orange'
                    }, 7);
                } else {
                    frappe.show_alert({ message: row.item_code + ': ' + qty + ' available in stock', indicator: 'green' }, 5);
                }
            }
        });
    }
});

frappe.ui.form.on('Sales Order', {
    refresh(frm) {
        if (frm.is_new() || frm.doc.docstatus === 2) return;
        frm.add_custom_button('Raw Material Request', () => {
            if (frm.is_dirty()) {
                frappe.msgprint('Please save the Sales Order first.');
                return;
            }
            frappe.call({
                method: 'masterbatch.sales_tools.make_raw_material_request',
                args: { sales_order: frm.doc.name },
                freeze: true,
                freeze_message: 'Exploding recipes and building a draft Material Request…',
                callback: (r) => {
                    if (r.message) {
                        frappe.show_alert({
                            message: 'Draft Material Request ' + r.message + ' created — review, edit and submit.',
                            indicator: 'green'
                        });
                        frappe.set_route('Form', 'Material Request', r.message);
                    }
                }
            });
        }, 'Create');
    }
});
