import frappe

def before_uninstall():
    reset_journal_entry_account_reference_type_field()

def reset_journal_entry_account_reference_type_field():
    options = frappe.db.get_value("Property Setter", {"doc_type": "Journal Entry Account", "field_name":"reference_type", "property":"options"}, "value")
    if not options:
        options = frappe.db.get_value("DocField", {"parent": "Journal Entry Account", "fieldname":"reference_type"}, "options")
    options = options.split("\n")
    options.pop()
    options = "\n".join(options)
    frappe.db.set_value("Property Setter", 
                        {"doc_type": "Journal Entry Account", "field_name":"reference_type", "property":"options"},
                        "value", options)
    frappe.db.set_value("DocField", {"parent": "Journal Entry Account", "fieldname":"reference_type"}, "options", options)
    frappe.db.commit()
    frappe.clear_cache()