import json
import frappe
import traceback
from frappe.utils import (today, format_date, date_diff, flt)
from frappe import _
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


def _get_currency_precision():
	precision = frappe.get_cached_value("System Settings", "System Settings", "currency_precision")
	return int(precision) if precision not in (None, "") else 3

def _je_total_amount(je_doc):
	"""
	Compute total of the Journal Entry from its accounts table.
	Most JEs are balanced; using total_debit is a reasonable proxy.
	We also validate it's balanced.
	"""
	total_debit = 0
	total_credit = 0
	for row in (je_doc.get("accounts") or []):
		total_debit += flt(row.debit_in_account_currency or 0)
		total_credit += flt(row.credit_in_account_currency or 0)

	return total_debit, total_credit

@frappe.whitelist()
def close_expense(document, jv=None):
	if isinstance(document, str):
		document = frappe.get_doc("Deferred Expense", document)

	# must be submitted if you want "close" only after submit (recommended)
	if document.docstatus != 1:
		frappe.throw(_("Deferred Expense must be submitted before closing."))

	remaining = flt(document.balance_after_adjustments)
	if remaining <= 0:
		frappe.throw(_("Remaining balance must be greater than zero to close."))

	precision = _get_currency_precision()

	# Collect already-posted schedule rows (keep them)
	adjustments = [row for row in (document.get("schedules") or []) if row.journal_entry]

	# If user supplied JV, validate it
	if jv:
		je = frappe.get_doc("Journal Entry", jv)

		# basic status checks
		if je.docstatus != 1:
			frappe.throw(_("Closing Journal Entry must be Submitted (docstatus = 1)."))

		# Amount check: JE amount should equal remaining balance
		total_debit, total_credit = _je_total_amount(je)

		# validate JE is balanced (optional but strongly recommended)
		if flt(total_debit, precision) != flt(total_credit, precision):
			frappe.throw(_("Journal Entry is not balanced (debit != credit)."))

		# match remaining balance (compare against total debit)
		if flt(total_debit, precision) != flt(remaining, precision):
			frappe.throw(_(
				"Closing Journal Entry amount ({0}) must equal remaining balance ({1})."
			).format(flt(total_debit, precision), flt(remaining, precision)))

		# Check if this JE is already linked as closing entry in another Deferred Expense
		existing_close = frappe.db.exists(
			"Deferred Expense",
			{
				"closing_journal_entry": jv,
				"name": ["!=", document.name],
				"docstatus": ["!=", 2],  # not cancelled docs
			},
		)
		if existing_close:
			frappe.throw(_(
				"Journal Entry {0} is already used as Closing Journal Entry in Deferred Expense {1}."
			).format(jv, existing_close))

		# Optional: also block if the same JE appears in ANY schedules row elsewhere
		used_in_schedule = frappe.db.sql(
			"""
			SELECT parent
			FROM `tabAdjustments Schedule`
			WHERE journal_entry = %s AND parent != %s
			LIMIT 1
			""",
			(jv, document.name),
		)
		if used_in_schedule:
			frappe.throw(_(
				"Journal Entry {0} is already linked in schedules of Deferred Expense {1}."
			).format(jv, used_in_schedule[0][0]))

	else:
		# Auto-create JE for the remaining balance
		jv = create_journal_entry(document, today(), remaining)

	# Append the closing schedule row
	adjustments.append({
		"schedule_date": today(),
		"adjustment_amount": remaining,
		"accumulated_adjustment_amount": document.gross_expense_amount,
		"journal_entry": jv
	})

	# Rewrite schedules to keep posted ones + closing row
	document.get("schedules").clear()
	for row in adjustments:
		document.append("schedules", row)

	# Save + mark closed fields
	document.save(ignore_permissions=True)
	document.db_set("closing_date", today())
	document.db_set("closing_journal_entry", jv)  # <-- requested
	document.db_set("balance_after_adjustments", 0)
	document.db_set("accumulated_adjustment_amount", document.gross_expense_amount)
	document.db_set("closing_journal_entry", jv)
	update_status(document, "Closed")
	return {"ok": True, "closing_journal_entry": jv}
		


import frappe
from frappe import _
from frappe.utils import flt

@frappe.whitelist()
def reopen_expense(document):
    doc = frappe.get_doc("Deferred Expense", document) if isinstance(document, str) else document

    if doc.docstatus != 1:
        frappe.throw(_("Only submitted documents can be re-opened."))

    if doc.status != "Closed" or not doc.closing_date:
        frappe.throw(_("Document is not closed."))

    closing_jv = getattr(doc, "closing_journal_entry", None)

    # 1) Build a map: schedule_date -> journal_entry (posted rows only), excluding closing JV
    posted_jv_by_date = {}
    for row in (doc.get("schedules") or []):
        if not row.journal_entry:
            continue
        if closing_jv and row.journal_entry == closing_jv:
            continue
        posted_jv_by_date[row.schedule_date] = row.journal_entry

    # 2) Cancel closing JE (DO NOT DELETE)
    if closing_jv:
        je = frappe.get_doc("Journal Entry", closing_jv)
        if je.docstatus == 1:
            je.cancel()

    # 3) Clear closing metadata BEFORE recompute (so it behaves like reopened)
    doc.db_set("closing_date", None)
    if hasattr(doc, "closing_journal_entry"):
        doc.db_set("closing_journal_entry", None)

    # 4) Recompute schedules fully using the DocType method
    doc.make_adjustment_entries()

    # 5) Re-attach the old posted journal entries onto the new schedule by date
    attached_count = 0
    for row in (doc.get("schedules") or []):
        jv = posted_jv_by_date.get(row.schedule_date)
        if jv:
            row.journal_entry = jv
            attached_count += 1

    # 6) Save and recompute balances
    doc.save(ignore_permissions=True)
    update_balance(doc)

    # 7) Status rule
    new_status = "Partially Adjusted" if attached_count > 0 else "Submitted"
    update_status(doc, new_status)

    return {
        "ok": True,
        "status": new_status,
        "attached_jv_count": attached_count,
        "missing_dates": [
            str(d) for d in posted_jv_by_date.keys()
            if d not in {r.schedule_date for r in (doc.get("schedules") or [])}
        ],
    }
