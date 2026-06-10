app_name = "masterbatch"
app_title = "Masterbatch"
app_publisher = "Sandeep"
app_description = "Capital Colours Masterbatch Manufacturing"
app_email = "admin@colour.local"
app_license = "MIT"

fixtures = [
    {"dt": "Item Group",    "filters": [["name","in",["Raw Materials - MB","Finished Goods - MB","Packing Materials - MB"]]]},
    {"dt": "UOM",           "filters": [["name","in",["KG","MT","Nos","Bag","Pcs"]]]},
    {"dt": "Warehouse",     "filters": [["name","like","% - colour"]]},
    {"dt": "Item",          "filters": [["item_group","like","% - MB"]]},
    {"dt": "BOM",           "filters": [["is_active","=",1],["item","like","MB-%"]]},
    {"dt": "Customer",      "filters": [["customer_name","in",["Vivid Plastics","Aluva Plastics","Supreme Polymers","Raj Films","Ganga Packaging"]]]},
    {"dt": "Supplier",      "filters": [["supplier_name","in",["Reliance Industries","Cabot Corporation","BASF India","Clariant India","Omya India"]]]},
]

# after_install (run demo loader manually) = "masterbatch.setup.after_install"


# keep desk sidebar links in the same tab (see public/js/sidebar_fix.js)
app_include_js = ["/assets/masterbatch/js/sidebar_fix.js"]

# --- App branding / launcher (added for demo) ---
app_logo_url = "/assets/masterbatch/images/masterbatch-logo.svg"
app_icon = "manufacturing"
app_color = "#7c3aed"

add_to_apps_screen = [
    {
        "name": "masterbatch",
        "logo": "/assets/masterbatch/images/masterbatch-logo.svg",
        "title": "Masterbatch",
        "route": "/app/masterbatch",
    }
]
