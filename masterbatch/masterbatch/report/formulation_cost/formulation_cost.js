frappe.query_reports["Formulation Cost"] = {
    filters: [
        { fieldname: "finished_item", label: "Finished Item", fieldtype: "Link", options: "Item" }
    ]
};
