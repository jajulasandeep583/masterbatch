from setuptools import setup, find_packages
setup(
    name="masterbatch",
    version="0.0.1",
    description="Capital Colours – Masterbatch Manufacturing App for ERPNext",
    author="Sandeep",
    author_email="admin@colour.local",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=["frappe"],
)
