frappe.query_reports["Raw Material Consumption"] = {
    filters: [
        { fieldname: "from_date", label: "From Date", fieldtype: "Date",
          default: frappe.datetime.add_months(frappe.datetime.get_today(), -1) },
        { fieldname: "to_date", label: "To Date", fieldtype: "Date",
          default: frappe.datetime.get_today() },
        { fieldname: "item_code", label: "Raw Material", fieldtype: "Link", options: "Item" },
        { fieldname: "item_group", label: "Item Group", fieldtype: "Link", options: "Item Group" }
    ]
};
