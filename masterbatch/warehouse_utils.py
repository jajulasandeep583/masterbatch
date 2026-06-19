import frappe


def get_default_company():
    return (frappe.defaults.get_user_default("Company")
            or frappe.db.get_single_value("Global Defaults", "default_company"))


def _settings(field):
    if frappe.db.exists("DocType", "Masterbatch Settings"):
        return frappe.db.get_single_value("Masterbatch Settings", field)
    return None


def _item_default_wh(item_code, company):
    if not item_code:
        return None
    return frappe.db.get_value("Item Default", {"parent": item_code, "company": company}, "default_warehouse")


def get_source_warehouse(company=None, item_code=None):
    """Warehouse a raw material is consumed from — driven by YOUR configuration, never by
    warehouse names. Order: the item's own default warehouse (keep an item in any warehouse you
    like) -> Masterbatch Settings 'Default Source Warehouse' -> Stock Settings default warehouse.
    """
    company = company or get_default_company()
    return (_item_default_wh(item_code, company)
            or _settings("default_source_warehouse")
            or frappe.db.get_single_value("Stock Settings", "default_warehouse"))


def get_fg_warehouse(company=None, item_code=None):
    """Warehouse finished goods / scrap are received into — your choice via settings. Order:
    Masterbatch Settings 'Default Finished Goods Warehouse' -> the item's own default warehouse
    -> Stock Settings default warehouse. No warehouse-name assumptions.
    """
    company = company or get_default_company()
    return (_settings("default_finished_goods_warehouse")
            or _item_default_wh(item_code, company)
            or frappe.db.get_single_value("Stock Settings", "default_warehouse"))


def get_default_uom():
    """Configurable default unit (Masterbatch Settings). Falls back to the first
    weight UOM that actually exists on this site so we never produce an invalid
    link on a fresh install (ERPNext ships 'Kg', not 'KG')."""
    configured = _settings("default_uom")
    if configured and frappe.db.exists("UOM", configured):
        return configured
    for name in ("KG", "Kg", "Kgs", "Kilogram"):
        if frappe.db.exists("UOM", name):
            return name
    return frappe.db.get_value("UOM", {}, "name")
