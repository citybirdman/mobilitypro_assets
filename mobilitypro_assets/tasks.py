import frappe
from frappe.utils import (today, add_months)

def get_due_expense_entries():
	parent_docs = frappe.get_all('Deferred Expense', [['status', 'in', ['Partially Adjusted', 'Submitted']]], 'name')
	parent_names = []
	for parent in parent_docs:
		parent_names.append(parent.name)
	rows = frappe.get_all('Adjustments Schedule',[['schedule_date', 'Between', [add_months(today(), -12), today()]], ['docstatus', '=', 1], ['journal_entry', '=', ''], ['parent','in',parent_names]], ['name', 'parent', 'schedule_date','adjustment_amount as amount'])
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
	journal_entry.flags.ignore_links = True
	journal_entry.save()
	journal_entry.submit()
	return journal_entry.name

def make_expense_entries():
	rows = get_due_expense_entries()
	parent = ""
	for row in rows:
		doc = frappe.get_doc('Deferred Expense', row.parent)
		jv_name = create_journal_entry(doc, row.schedule_date, row.amount)
		frappe.db.set_value('Adjustments Schedule', row.name, 'journal_entry', jv_name)
		if row.parent != parent:
			update_status(row.parent)
			update_balance(row.parent)

def update_status(document, status = "Partially Adjusted"):
	if type(document) is str:
		document = frappe.get_doc("Deferred Expense", document)
	rows = document.get("schedules")
	if rows[-1].journal_entry:
		status = "Fully Adjusted"
	document.db_set("status", status)

def update_balance(doc):
	balance = 0
	if type(doc) is str:
		doc = frappe.get_doc("Deferred Expense", doc)
	if doc.is_existing_expense and doc.opening_realized_expense_balance != 0:
		balance = doc.opening_realized_expense_balance
	for row in doc.get("schedules"):
		if not row.journal_entry:
			break
		balance = row.accumulated_adjustment_amount
	doc.db_set("balance_after_adjustments", balance)

@frappe.whitelist()
def close_expense(document, jv=None):
	if type(document) is str:
		document = frappe.get_doc("Deferred Expense", document)
	if not jv:
		jv = create_journal_entry(document, today(), (document.gross_expense_amount - document.balance_after_adjustments))
	document.db_set("closing_journal_entry", jv)
	document.db_set("closing_date", today())
	document.db_set("balance_after_adjustments", document.gross_expense_amount)
	update_status(document, "Closed")
		