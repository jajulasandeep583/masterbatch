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


def after_migrate():
    make_coa_custom_fields()
