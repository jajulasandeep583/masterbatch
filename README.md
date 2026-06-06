# Masterbatch – Capital Colours ERPNext Custom App

Custom Frappe/ERPNext app for masterbatch manufacturing companies.

## What's Included
- Batch Production Sheet (custom doctype)
- Lab Formulation / Recipe Register
- Shade Code master
- Stock Valuation & Production Reports
- Demo fixture data (items, BOMs, customers, suppliers, work orders)

## Install
```bash
cd ~/frappe-bench
bench get-app masterbatch https://github.com/YOUR_USERNAME/masterbatch
bench --site colour install-app masterbatch
bench --site colour migrate
bench --site colour execute masterbatch.demo.load_demo_data
bench restart
```
