import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    from masterbatch.demo.load_demo_data import run
    run()


# batch link on sales rows so the Certificate of Analysis knows which
# production batch the goods were delivered from
COA_CUSTOM_FIELDS = {
    "Sales Invoice Item": [
        dict(
            fieldname="batch_production_sheet",
            label="Batch (COA)",
            fieldtype="Link",
            options="Batch Production Sheet",
            insert_after="item_name",
            in_list_view=1,
            columns=2,
            allow_on_submit=1,
            print_hide=1,
        ),
    ],
    "Delivery Note Item": [
        dict(
            fieldname="batch_production_sheet",
            label="Batch (COA)",
            fieldtype="Link",
            options="Batch Production Sheet",
            insert_after="item_name",
            in_list_view=1,
            columns=2,
            allow_on_submit=1,
            print_hide=1,
        ),
    ],
}


def make_coa_custom_fields():
    create_custom_fields(COA_CUSTOM_FIELDS, ignore_validate=True)


# Standard masterbatch QC parameters, seeded into the QC Parameter master so the
# Batch Production Sheet can pick them and auto-fill unit / spec / limits.
QC_PARAMETER_MASTERS = [
    {"parameter_name": "Melt Flow Index", "unit": "g/10 min", "test_method": "ASTM D1238",
     "evaluation_type": "Range", "min_value": 18.0, "max_value": 24.0},
    {"parameter_name": "Moisture Content", "unit": "%", "test_method": "ASTM D6980",
     "evaluation_type": "Maximum", "max_value": 0.10},
    {"parameter_name": "Pigment Content", "unit": "%", "test_method": "Muffle Furnace",
     "evaluation_type": "Range", "min_value": 38.0, "max_value": 42.0},
    {"parameter_name": "Colour Difference (ΔE)", "unit": "ΔE", "test_method": "Spectrophotometer",
     "evaluation_type": "Maximum", "max_value": 1.0},
    {"parameter_name": "Dispersion (Filter Pressure)", "unit": "bar/g", "test_method": "EN 13900-5",
     "evaluation_type": "Maximum", "max_value": 0.25},
    {"parameter_name": "Density", "unit": "g/cm³", "test_method": "ASTM D792",
     "evaluation_type": "Range", "min_value": 1.10, "max_value": 1.30},
]


def make_qc_parameter_masters():
    if not frappe.db.exists("DocType", "QC Parameter"):
        return
    for spec in QC_PARAMETER_MASTERS:
        if frappe.db.exists("QC Parameter", spec["parameter_name"]):
            continue
        doc = frappe.new_doc("QC Parameter")
        doc.update(spec)
        doc.insert(ignore_permissions=True)


def after_migrate():
    make_coa_custom_fields()
    make_qc_parameter_masters()
