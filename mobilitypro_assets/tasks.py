import json
import frappe
from frappe.utils import (today, now_datetime, get_datetime)
from datetime import timedelta
import time

def get_due_expense_entries():
	parent_docs = frappe.get_all('Deferred Expense', [['status', 'in', ['Partially Adjusted', 'Submitted']]], 'name')
	parent_names = []
	for parent in parent_docs:
		parent_names.append(parent.name)
	rows = frappe.get_all('Adjustments Schedule',[['schedule_date', '<', today()], ['docstatus', '=', 1], ['journal_entry', '=', ''], ['parent','in',parent_names ]], ['name', 'parent', 'schedule_date','adjustment_amount as amount', "idx"])
	return rows

def create_journal_entry(doc, date, amount, idx):
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
		'title': 'Deferred Expense ' + doc.name,
		'user_remark':  " مصروف مقدم " + doc.name + " عن " + frappe.utils.format_date(today(), 'MM-YYYY')
	}).insert()
	journal_entry.flags.ignore_links = True
	journal_entry.save()
	journal_entry.submit()
	return journal_entry.name

def make_expense_entries():
	try:
		rows = get_due_expense_entries()
		parent = ""
		for row in rows:
			doc = frappe.get_doc('Deferred Expense', row.parent)
			jv_name = create_journal_entry(doc, row.schedule_date, row.amount, row.idx)
			frappe.db.set_value('Adjustments Schedule', row.name, 'journal_entry', jv_name)
			if row.parent != parent:
				update_status(row.parent)
				update_balance(row.parent)
	except Exception as e:
		error = frappe.get_doc(dict(status="Failed", doctype="Scheduled Job Log", details=str(e), scheduled_job_type="tasks.make_expense_entries")).insert(ignore_permissions=True)
		users = frappe.db.get_list("User", {"name":["in", "ahmed.zaytoon@mobilityp.com,ahmed.sharaf@mobilityp.com"], "enabled": 1}, "email")
		message = '<p>'+str(e) +'on log'+ error.name +'<p>'
		for user in users:
			frappe.sendmail(
				recipients=user.email,
				sender="notification@example.com",
				subject="Error in schedular",
				message=message,
			)

		# frappe.throw(repr(error))

		

def update_status(document, status = "Partially Adjusted"):
	if type(document) is str:
		document = frappe.get_doc("Deferred Expense", document)
	rows = document.get("schedules")
	if rows[-1].journal_entry and status != "Closed":
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
	doc.db_set("accumulated_adjustment_amount", balance)
	doc.db_set("balance_after_adjustments", (doc.gross_expense_amount - balance))

@frappe.whitelist()
def close_expense(document, jv=None):
	if type(document) is str:
		document = frappe.get_doc("Deferred Expense", document)
	adjustments = []
	for row in document.schedules:
		if row.journal_entry:
			adjustments.append(row)
	if not jv:
		jv = create_journal_entry(document, today(), document.balance_after_adjustments, len(adjustments)+1)
	adjustments.append({
					"schedule_date": today(),
					"adjustment_amount": document.balance_after_adjustments,
					"accumulated_adjustment_amount": document.gross_expense_amount,
					"journal_entry": jv
					})
	document.get("schedules").clear()
	for row in adjustments:
		document.append("schedules", row)
	document.save()
	document.db_set("closing_date", today())
	document.db_set("balance_after_adjustments", document.gross_expense_amount)
	document.db_set("accumulated_adjustment_amount", 0)
	update_status(document, "Closed")
		