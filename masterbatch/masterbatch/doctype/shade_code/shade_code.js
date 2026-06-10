frappe.ui.form.on('Shade Code', {
    refresh(frm) {
        if (frm.is_new()) return;
        frappe.db.get_value('Lab Formulation', { shade_code: frm.doc.name, docstatus: 1 }, 'name').then((r) => {
            const existing = r.message && r.message.name;
            if (existing) {
                frm.add_custom_button('✓ View Lab Formulation', () => frappe.set_route('Form', 'Lab Formulation', existing))
                    .removeClass('btn-default').addClass('btn-success');
            }
            const btn = frm.add_custom_button('▶ New Lab Formulation', () => {
                frappe.route_options = { shade_code: frm.doc.name };
                frappe.new_doc('Lab Formulation');
            });
            if (!existing) {
                btn.removeClass('btn-default').addClass('btn-primary');
            }
        });
        frm.add_custom_button('Batches', () => {
            frappe.set_route('List', 'Batch Production Sheet', { shade_code: frm.doc.name });
        });
    }
});
