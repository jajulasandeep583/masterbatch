"""HR demo data for the Capital Colours demo: employees, attendance, payroll,
salary slips + branded salary slip print format.

Run: bench --site colour execute masterbatch.demo.hr_demo.run
"""
import random
from datetime import date, timedelta

import frappe

COMPANY = "MasterBatch"
HOLIDAY_LIST = "MB Holiday List 2026"
SALARY_STRUCTURE = "MB Monthly Salary"
PRINT_FORMAT = "Capital Colours Salary Slip"

DEPARTMENTS = ["Production", "Quality", "Sales", "Accounts", "Human Resources", "Stores"]
DESIGNATIONS = ["Plant Manager", "Production Supervisor", "Machine Operator", "QC Chemist",
                "Lab Technician", "Sales Executive", "Accountant", "HR Executive", "Store Keeper"]

# first, last, gender, dob, doj, designation, department, base salary
EMPLOYEES = [
    ("Ramesh", "Kumar", "Male", "1980-05-12", "2023-04-10", "Plant Manager", "Production", 85000),
    ("Suresh", "Patil", "Male", "1986-08-23", "2023-06-01", "Production Supervisor", "Production", 45000),
    ("Mahesh", "Gowda", "Male", "1993-01-15", "2024-02-12", "Machine Operator", "Production", 22000),
    ("Venkatesh", "Rao", "Male", "1995-11-02", "2024-07-01", "Machine Operator", "Production", 21000),
    ("Manjunath", "Shetty", "Male", "1991-03-30", "2023-09-18", "Machine Operator", "Production", 23000),
    ("Priya", "Sharma", "Female", "1990-12-08", "2023-05-15", "QC Chemist", "Quality", 38000),
    ("Lakshmi", "Devi", "Female", "1996-04-19", "2025-01-06", "Lab Technician", "Quality", 26000),
    ("Arun", "Nair", "Male", "1988-07-27", "2023-08-01", "Sales Executive", "Sales", 35000),
    ("Divya", "Reddy", "Female", "1994-09-14", "2024-11-03", "Sales Executive", "Sales", 34000),
    ("Kiran", "Joshi", "Male", "1985-02-21", "2023-04-10", "Accountant", "Accounts", 40000),
    ("Anita", "Kulkarni", "Female", "1992-06-05", "2024-04-22", "HR Executive", "Human Resources", 32000),
    ("Mohammed", "Irfan", "Male", "1997-10-11", "2025-03-10", "Store Keeper", "Stores", 24000),
]

FESTIVALS = {
    "2026-01-01": "New Year", "2026-01-14": "Makar Sankranti", "2026-01-26": "Republic Day",
    "2026-03-19": "Ugadi", "2026-05-01": "May Day", "2026-08-15": "Independence Day",
    "2026-10-02": "Gandhi Jayanti", "2026-10-21": "Ayudha Pooja", "2026-11-08": "Deepavali",
    "2026-12-25": "Christmas",
}

# (component, abbr, type, formula_or_amount, depends_on_payment_days)
COMPONENTS = [
    ("Basic", "B", "Earning", "base * 0.50", 1),
    # formulas referencing B already scale with payment days — leave dpd off
    ("House Rent Allowance", "HRA", "Earning", "B * 0.40", 0),
    ("Conveyance Allowance", "CA", "Earning", 1600, 1),
    ("Special Allowance", "SA", "Earning", "base - B - HRA - 1600", 0),
    ("Provident Fund", "PF", "Deduction", "B * 0.12", 0),
    ("Professional Tax", "PT", "Deduction", 200, 0),
]

SLIP_HTML = """
<style>
  .ccs {{ font-family: Arial, sans-serif; font-size: 12px; color:#222; }}
  .ccs .head {{ background: linear-gradient(135deg,#7c3aed,#4f46e5); color:#fff;
               padding:14px 18px; border-radius:8px 8px 0 0; }}
  .ccs .head h2 {{ margin:0; color:#fff; }}
  .ccs table {{ width:100%; border-collapse:collapse; margin-top:10px; }}
  .ccs th, .ccs td {{ border:1px solid #ddd; padding:6px 8px; }}
  .ccs th {{ background:#f3f0ff; text-align:left; }}
  .ccs .num {{ text-align:right; }}
  .ccs .tot {{ font-weight:bold; background:#fafafa; }}
  .ccs .net {{ background:#7c3aed; color:#fff; font-weight:bold; font-size:13px; }}
  .ccs .meta td {{ border:none; padding:2px 8px; }}
</style>
<div class="ccs">
  <div class="head">
    <h2>Capital Colours</h2>
    <div>Masterbatch &amp; Polymer Compounds &mdash; Salary Slip</div>
  </div>
  <table class="meta">
    <tr><td><b>Employee</b>: {{{{ doc.employee_name }}}} ({{{{ doc.employee }}}})</td>
        <td><b>Pay Period</b>: {{{{ frappe.utils.formatdate(doc.start_date) }}}} &ndash; {{{{ frappe.utils.formatdate(doc.end_date) }}}}</td></tr>
    <tr><td><b>Designation</b>: {{{{ doc.designation or "" }}}}</td>
        <td><b>Department</b>: {{{{ doc.department or "" }}}}</td></tr>
    <tr><td><b>Working Days</b>: {{{{ doc.total_working_days }}}}</td>
        <td><b>Payment Days</b>: {{{{ doc.payment_days }}}}</td></tr>
  </table>
  <table>
    <tr><th style="width:50%">Earnings</th><th class="num">Amount</th></tr>
    {{% for e in doc.earnings %}}
    <tr><td>{{{{ e.salary_component }}}}</td><td class="num">{{{{ frappe.utils.fmt_money(e.amount, currency="INR") }}}}</td></tr>
    {{% endfor %}}
    <tr class="tot"><td>Gross Pay</td><td class="num">{{{{ frappe.utils.fmt_money(doc.gross_pay, currency="INR") }}}}</td></tr>
  </table>
  <table>
    <tr><th style="width:50%">Deductions</th><th class="num">Amount</th></tr>
    {{% for d in doc.deductions %}}
    <tr><td>{{{{ d.salary_component }}}}</td><td class="num">{{{{ frappe.utils.fmt_money(d.amount, currency="INR") }}}}</td></tr>
    {{% endfor %}}
    <tr class="tot"><td>Total Deductions</td><td class="num">{{{{ frappe.utils.fmt_money(doc.total_deduction, currency="INR") }}}}</td></tr>
  </table>
  <table>
    <tr class="net"><td style="width:50%">Net Pay</td><td class="num">{{{{ frappe.utils.fmt_money(doc.net_pay, currency="INR") }}}}</td></tr>
    <tr><td colspan="2"><b>In words</b>: {{{{ doc.total_in_words }}}}</td></tr>
  </table>
  <p style="margin-top:18px;color:#888">This is a computer generated salary slip and does not require a signature.</p>
</div>
"""


def setup_masters():
    for d in DEPARTMENTS:
        if not frappe.db.exists("Department", {"department_name": d, "company": COMPANY}):
            frappe.get_doc({"doctype": "Department", "department_name": d, "company": COMPANY}).insert()
    for d in DESIGNATIONS:
        if not frappe.db.exists("Designation", d):
            frappe.get_doc({"doctype": "Designation", "designation_name": d}).insert()

    if not frappe.db.exists("Holiday List", HOLIDAY_LIST):
        hl = frappe.new_doc("Holiday List")
        hl.holiday_list_name = HOLIDAY_LIST
        hl.from_date, hl.to_date = "2026-01-01", "2026-12-31"
        d = date(2026, 1, 1)
        while d <= date(2026, 12, 31):
            if d.weekday() == 6:
                hl.append("holidays", {"holiday_date": d, "description": "Sunday", "weekly_off": 1})
            d += timedelta(days=1)
        for hd, desc in FESTIVALS.items():
            if not any(str(h.holiday_date) == hd for h in hl.holidays):
                hl.append("holidays", {"holiday_date": hd, "description": desc})
        hl.insert()
    frappe.db.set_value("Company", COMPANY, "default_holiday_list", HOLIDAY_LIST)

    # hrms v16 resolves holidays via Holiday List Assignment, not the company field
    if not frappe.db.exists("Holiday List Assignment",
                            {"applicable_for": "Company", "assigned_to": COMPANY, "docstatus": 1}):
        hla = frappe.get_doc({"doctype": "Holiday List Assignment", "applicable_for": "Company",
                              "assigned_to": COMPANY, "holiday_list": HOLIDAY_LIST,
                              "from_date": "2026-01-01"})
        hla.insert()
        hla.submit()

    # don't try to email slips to employees without email ids
    frappe.db.set_single_value("Payroll Settings", "email_salary_slip_to_employee", 0)
    print("masters done")


def make_employees():
    dep_map = {d: frappe.db.get_value("Department", {"department_name": d, "company": COMPANY})
               for d in DEPARTMENTS}
    out = []
    for fn, ln, g, dob, doj, desig, dep, base in EMPLOYEES:
        name = frappe.db.get_value("Employee", {"first_name": fn, "last_name": ln, "company": COMPANY})
        if not name:
            emp = frappe.get_doc({
                "doctype": "Employee", "first_name": fn, "last_name": ln, "gender": g,
                "date_of_birth": dob, "date_of_joining": doj, "company": COMPANY,
                "status": "Active", "designation": desig, "department": dep_map[dep],
                "holiday_list": HOLIDAY_LIST,
            }).insert()
            name = emp.name
        out.append((name, base))
    print(f"employees: {len(out)}")
    return out


def setup_payroll(emps):
    for comp, abbr, typ, _, dpd in COMPONENTS:
        if not frappe.db.exists("Salary Component", comp):
            frappe.get_doc({"doctype": "Salary Component", "salary_component": comp,
                            "salary_component_abbr": abbr, "type": typ,
                            "depends_on_payment_days": dpd}).insert()
        else:
            frappe.db.set_value("Salary Component", comp, "depends_on_payment_days", dpd)

    if not frappe.db.exists("Salary Structure", SALARY_STRUCTURE):
        ss = frappe.new_doc("Salary Structure")
        ss.name = SALARY_STRUCTURE
        ss.company = COMPANY
        ss.payroll_frequency = "Monthly"
        ss.is_active = "Yes"
        for comp, abbr, typ, val, dpd in COMPONENTS:
            row = {"salary_component": comp, "abbr": abbr, "depends_on_payment_days": dpd}
            if isinstance(val, str):
                row.update({"amount_based_on_formula": 1, "formula": val})
            else:
                row.update({"amount_based_on_formula": 0, "amount": val})
            ss.append("earnings" if typ == "Earning" else "deductions", row)
        ss.insert()
        ss.submit()

    for emp, base in emps:
        if not frappe.db.exists("Salary Structure Assignment",
                                {"employee": emp, "salary_structure": SALARY_STRUCTURE, "docstatus": 1}):
            ssa = frappe.get_doc({"doctype": "Salary Structure Assignment", "employee": emp,
                                  "salary_structure": SALARY_STRUCTURE, "from_date": "2026-01-01",
                                  "company": COMPANY, "base": base, "variable": 0})
            ssa.insert()
            ssa.submit()
    print("payroll structure + assignments done")


def make_attendance(emps):
    random.seed(42)
    holidays = {str(h) for h in frappe.get_all("Holiday", filters={"parent": HOLIDAY_LIST},
                                               pluck="holiday_date")}
    has_half_status = frappe.get_meta("Attendance").has_field("half_day_status")
    start, end = date(2026, 4, 1), frappe.utils.getdate(frappe.utils.add_days(frappe.utils.today(), -1))
    n = 0
    d = start
    while d <= end:
        if str(d) not in holidays:
            for emp, _ in emps:
                if frappe.db.exists("Attendance", {"employee": emp, "attendance_date": d,
                                                   "docstatus": ["<", 2]}):
                    continue
                r = random.random()
                status = "Present" if r < 0.92 else ("Absent" if r < 0.96 else "Half Day")
                att = frappe.get_doc({"doctype": "Attendance", "employee": emp,
                                      "attendance_date": d, "status": status, "company": COMPANY})
                if status == "Half Day" and has_half_status:
                    att.half_day_status = "Present"
                try:
                    att.insert()
                    att.submit()
                    n += 1
                except Exception as e:
                    print(f"attendance skip {emp} {d}: {e}")
        d += timedelta(days=1)
    print(f"attendance records created: {n}")


def make_salary_slips(emps):
    periods = [("2026-04-01", "2026-04-30"), ("2026-05-01", "2026-05-31")]
    n = 0
    for start, end in periods:
        for emp, _ in emps:
            if frappe.db.exists("Salary Slip", {"employee": emp, "start_date": start,
                                                "docstatus": ["<", 2]}):
                continue
            try:
                # employee must be set at construction: the naming series
                # "Sal Slip/{employee}/.#####" is built in __init__
                slip = frappe.get_doc({"doctype": "Salary Slip", "employee": emp,
                                       "start_date": start, "end_date": end,
                                       "posting_date": end, "company": COMPANY})
                slip.insert()
                slip.submit()
                n += 1
            except Exception as e:
                print(f"slip FAIL {emp} {start}: {e}")
    print(f"salary slips created: {n}")


def fix_slip_names():
    """Cancel + delete slips that got named 'Sal Slip/None/...' and recreate them."""
    bad = frappe.get_all("Salary Slip", filters={"name": ["like", "Sal Slip/None/%"]}, pluck="name")
    for name in bad:
        doc = frappe.get_doc("Salary Slip", name)
        if doc.docstatus == 1:
            doc.cancel()
        frappe.delete_doc("Salary Slip", name, force=1)
    print(f"deleted misnamed slips: {len(bad)}")


def make_print_format():
    if frappe.db.exists("Print Format", PRINT_FORMAT):
        pf = frappe.get_doc("Print Format", PRINT_FORMAT)
    else:
        pf = frappe.new_doc("Print Format")
        pf.name = PRINT_FORMAT
    pf.update({"doc_type": "Salary Slip", "module": "Masterbatch", "custom_format": 1,
               "print_format_type": "Jinja", "standard": "No", "disabled": 0,
               "html": SLIP_HTML.format()})
    pf.save()

    ps = frappe.db.exists("Property Setter", {"doc_type": "Salary Slip",
                                              "property": "default_print_format"})
    if ps:
        frappe.db.set_value("Property Setter", ps, "value", PRINT_FORMAT)
    else:
        frappe.get_doc({"doctype": "Property Setter", "doctype_or_field": "DocType",
                        "doc_type": "Salary Slip", "property": "default_print_format",
                        "property_type": "Data", "value": PRINT_FORMAT}).insert()
    print(f"print format '{PRINT_FORMAT}' set as Salary Slip default")


def verify():
    print("--- verify ---")
    print(f"Employees: {frappe.db.count('Employee', {'status': 'Active', 'company': COMPANY})}")
    print(f"Attendance (submitted): {frappe.db.count('Attendance', {'docstatus': 1})}")
    print(f"Salary Slips (submitted): {frappe.db.count('Salary Slip', {'docstatus': 1})}")
    slip = frappe.db.get_value("Salary Slip", {"docstatus": 1}, "name")
    html = frappe.get_print("Salary Slip", slip, PRINT_FORMAT)
    ok = "Capital Colours" in html and "Net Pay" in html
    print(f"print render of {slip}: {'OK' if ok else 'PROBLEM'} ({len(html)} chars)")
    one = frappe.get_doc("Salary Slip", slip)
    print(f"sample: {one.employee_name} gross={one.gross_pay} ded={one.total_deduction} net={one.net_pay}")


def run():
    setup_masters()
    emps = make_employees()
    setup_payroll(emps)
    make_attendance(emps)
    fix_slip_names()
    make_salary_slips(emps)
    make_print_format()
    frappe.db.commit()
    verify()
    print("HR DEMO DONE")
