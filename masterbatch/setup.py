import frappe

def after_install():
    from masterbatch.demo.load_demo_data import run
    run()
