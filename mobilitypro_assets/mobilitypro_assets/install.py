import frappe

def before_install():
    customize_journal_entry_account_reference_type_field()

def customize_journal_entry_account_reference_type_field():
    options = frappe.db.get_value("Property Setter", {"doc_type": "Journal Entry Account", "field_name":"reference_type", "property":"options"}, "value")
    options += "\nDefered Entry"
    frappe.db.set_value("Property Setter", 
                        {"doc_type": "Journal Entry Account", "field_name":"reference_type", "property":"options"},
                        "value", options)
    frappe.db.commit()
    frappe.clear_cache()