import json
import frappe
import traceback
from frappe.utils import (today, format_date, date_diff)
from datetime import timedelta, datetime
import time

def get_due_expense_entries():
	parent_docs = frappe.get_all('Deferred Expense', [['status', 'in', ['Partially Adjusted', 'Submitted']]], 'name')
	parent_names = []
	for parent in parent_docs:
		parent_names.append(parent.name)
	rows = frappe.get_all('Adjustments Schedule',[['schedule_date', '<=', today()], ['docstatus', '=', 1], ['journal_entry', '=', ''], ['parent','in',parent_names ]], ['name', 'parent', 'schedule_date','adjustment_amount as amount', "idx"])
	return rows

def create_journal_entry(doc, date, amount):
	accounts = []
	accounts.append({
		'account': doc.deferred_expense_account,
		'credit_in_account_currency': abs(amount),
	})

	accounts.append({
		'account': doc.expense_account,
		'debit_in_account_currency': abs(amount),
		'reference_type': 'Deferred Expense',
		'reference_name': doc.name,
		'branch': doc.branch,
	})
	for row in accounts:
		if not row["account"]:
			frappe.throw(_("Not all Accounts are set!"))
	journal_entry = frappe.get_doc({
		'doctype': 'Journal Entry',
		'company': doc.company,
		'posting_date': date,
		'accounts': accounts,
		'user_remark': doc.expense_name + " عن " + format_date(date, 'MM-YYYY') +"<br/>" + " مصروف مقدم رقم " + doc.name,
		'title': 'Deferred Expense ' + doc.name
	}).insert()
	journal_entry.flags.ignore_links = True
	journal_entry.save()
	journal_entry.submit()
	return journal_entry.name

def make_expense_entries():
	try:
		acc_settings = frappe.db.get_value("Accounts Settings", "Accounts Settings", ["acc_frozen_upto", "frozen_accounts_modifier"], as_dict = 1)
		rows = get_due_expense_entries()
		parent = ""
		for row in rows:
			doc = frappe.get_doc('Deferred Expense', row.parent)
			# (date_diff(row.schedule_date, acc_settings.acc_frozen_upto) <= 0 and acc_settings.frozen_accounts_modifier == "Administrator" ))
			if not acc_settings.acc_frozen_upto or date_diff(row.schedule_date, acc_settings.acc_frozen_upto) > 0:
				jv_name = create_journal_entry(doc, row.schedule_date, row.amount)
				frappe.db.set_value('Adjustments Schedule', row.name, 'journal_entry', jv_name)
			else:
				frappe.throw(f"You are not authorized to add or update entries before {acc_settings.acc_frozen_upto}")
			if row.parent != parent:
				update_status(row.parent)
				update_balance(row.parent)
		email = frappe.get_all("Email Account", filters={"default_outgoing": 1}, fields=["name", "email_id"])

	except Exception as e:
		logs = frappe.get_all("Scheduled Job Log", [["scheduled_job_type", "=", "tasks.make_expense_entries"],["status", "=", "Start"],["creation", ">", datetime.now() - timedelta(seconds=5)]])
		for log in logs:
			frappe.delete_doc("Scheduled Job Log", log.name, force=True, ignore_permissions=True, delete_permanently=True)
		error = frappe.get_doc(dict(status="Failed", doctype="Scheduled Job Log", details=traceback.format_exc(), scheduled_job_type="tasks.make_expense_entries")).insert(ignore_permissions=True)
		users = frappe.db.get_list("User", {"name":["in", "ahmed.zaytoon@mobilityp.com,ahmed.sharaf@mobilityp.com"], "enabled": 1}, "email")
		message = '<p>'+str(traceback.format_exc()) +'<br/>on log'+ str(error.name) +'<p>'
		email = frappe.get_all("Email Account", filters={"default_outgoing": 1}, fields=["name", "email_id"])
		if email:
			for user in users:
				frappe.sendmail(
					recipients=user.email,
					sender=email[0].email_id,
					subject="Error in scheduler",
					message=message,
				)

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
		jv = create_journal_entry(document, today(), document.balance_after_adjustments)
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
	document.db_set("balance_after_adjustments", 0)
	document.db_set("accumulated_adjustment_amount", document.gross_expense_amount)
	update_status(document, "Closed")
		
