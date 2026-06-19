import frappe


def get_default_company():
    return (frappe.defaults.get_user_default("Company")
            or frappe.db.get_single_value("Global Defaults", "default_company"))


def _wh(company, name=None, name_like=None):
    filters = {"company": company, "is_group": 0, "disabled": 0}
    if name:
        filters["name"] = name
    elif name_like:
        filters["name"] = ["like", name_like]
    return frappe.db.get_value("Warehouse", filters, "name")


def get_stores_warehouse(company=None):
    """Source warehouse that raw materials are consumed from.

    Portable across sites: tries the standard ERPNext 'Stores - {abbr}' name, then any
    'Stores'/'Raw' warehouse of the company, then the Stock Settings default warehouse,
    then any non-group warehouse of the company.
    """
    company = company or get_default_company()
    abbr = frappe.db.get_value("Company", company, "abbr")
    return (_wh(company, name=f"Stores - {abbr}")
            or _wh(company, name_like="%Stores%")
            or _wh(company, name_like="%Raw%")
            or frappe.db.get_single_value("Stock Settings", "default_warehouse")
            or _wh(company))


def get_fg_warehouse(company=None, item_code=None):
    """Target warehouse that finished goods / scrap are received into.

    Tries 'Finished Goods - {abbr}' then any 'Finished' warehouse first (so finished goods
    never land in stores), then the item's own default warehouse, then the stores warehouse.
    """
    company = company or get_default_company()
    abbr = frappe.db.get_value("Company", company, "abbr")
    wh = (_wh(company, name=f"Finished Goods - {abbr}")
          or _wh(company, name_like="%Finished%"))
    if wh:
        return wh
    if item_code:
        idef = frappe.db.get_value("Item Default", {"parent": item_code, "company": company}, "default_warehouse")
        if idef:
            return idef
    return get_stores_warehouse(company)
