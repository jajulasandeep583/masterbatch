import frappe

def go():
    rows = frappe.get_all("Account", filters={"company":"MasterBatch"},
                          fields=["name","is_group","root_type","parent_account"],
                          limit_page_length=0)
    eq = [a for a in rows if (a.root_type=="Equity") or (a.parent_account and "Equity" in a.parent_account)]
    print("EQUITY-RELATED ACCOUNTS:")
    for a in eq:
        print(f"  group={a.is_group} root={a.root_type} name={a.name} parent={a.parent_account}")
    print("ROOT ACCOUNTS (no parent):")
    for a in rows:
        if not a.parent_account:
            print(f"  group={a.is_group} root={a.root_type} name={a.name}")
