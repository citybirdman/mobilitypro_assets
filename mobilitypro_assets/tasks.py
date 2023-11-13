import frappe
from frappe.utils import (today, add_months)

def get_due_expense_entries():
	parent_docs = frappe.get_all('Deferred Expense', [['status', 'in', ['Partially Adjusted', 'Submitted']]], 'name')
	parent_names = []
	for parent in parent_docs:
		parent_names.append(parent.name)
	rows = frappe.get_all('Adjustments Schedule',[['schedule_date', 'Between', [add_months(today(), -12), today()]], ['docstatus', '=', 1], ['journal_entry', '=', ''], ['parent','in',parent_names]], ['name', 'parent', 'accumulated_adjustment_amount as amount'])
	return rows

def create_journal_entry(doc, date, amount):
	accounts = []
	accounts.append({
		'account': doc.expense_account,
		'debit_in_account_currency': abs(amount),
		'reference_type': 'Deferred Expense',
		'reference_name': doc.name,
		'branch': doc.branch
	})
	accounts.append({
		'account': doc.deferred_expense_account,
		'credit_in_account_currency': abs(amount)
	})
	
	
	journal_entry = frappe.get_doc({
		'doctype': 'Journal Entry',
		'company': doc.company,
		'posting_date': date,
		'accounts': accounts,
		'voucher_type': 'Cash Entry',
		'title': 'Deferred Expense ' + doc.name,
		# 'user_remark': 'مصاريف فسح حركة مخزنية رقم ' + doc.name
	}).insert()
	journal_entry.submit()
	return journal_entry.name

def update_status():
	pass

def make_expense_entries():
	rows = get_due_expense_entries()
	# frappe.throw("hhh")
	for row in rows:
		doc = frappe.get_doc('Deferred Expense', row.parent)
		jv_name = create_journal_entry(doc, today(), row.amount)
		frappe.db.set_value('Adjustments Schedule', row.name, 'journal_entry', jv_name)
		update_status()


def delete_jv():
	frappe.delete_doc("Journal Entry", "ACC-JV-2023-06131", force=True, ignore_permissions=True)