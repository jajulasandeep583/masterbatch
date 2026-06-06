frappe.query_reports["Production Summary"] = {
    filters: [
        { fieldname: "from_date", label: "From Date", fieldtype: "Date",
          default: frappe.datetime.add_months(frappe.datetime.get_today(), -1), reqd: 0 },
        { fieldname: "to_date", label: "To Date", fieldtype: "Date",
          default: frappe.datetime.get_today(), reqd: 0 },
        { fieldname: "finished_item", label: "Finished Item", fieldtype: "Link", options: "Item" }
    ]
};
