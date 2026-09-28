import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

REFERENCE_TYPE = "Deferred Expense"

def after_install():
    customize_journal_entry_account_reference_type_field()

def after_migrate():
    # migrate reloads Journal Entry Account from erpnext, so make sure the option is still there
    customize_journal_entry_account_reference_type_field()

def get_reference_type_options():
    # meta already includes any existing Property Setter on the field
    options = frappe.get_meta("Journal Entry Account").get_field("reference_type").options or ""
    return options.split("\n")

def set_reference_type_options(options):
    make_property_setter("Journal Entry Account", "reference_type", "options", "\n".join(options), "Text")
    frappe.clear_cache(doctype="Journal Entry Account")

def customize_journal_entry_account_reference_type_field():
    options = get_reference_type_options()
    if REFERENCE_TYPE in options:
        return
    options.append(REFERENCE_TYPE)
    set_reference_type_options(options)
