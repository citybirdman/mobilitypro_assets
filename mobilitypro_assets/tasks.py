import frappe


def make_expense_entries():
	docs = frappe.get_all("Deffered Expense")
	for doc in docs:
		frappe.db.set_value("Deffered Expense", doc.name, "balance_after_adjustments" , 10)
		frappe.db.set_value("Scheduled Job Log", "a46cf601d3", "details", doc)