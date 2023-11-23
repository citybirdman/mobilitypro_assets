# Copyright (c) 2023, Ahmed Zaytoon and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.delete_doc import update_flags
from frappe.utils import (add_months, date_diff, get_last_day, get_first_day, add_days, getdate)
from mobilitypro_assets.tasks import update_balance

from erpnext.controllers.accounts_controller import AccountsController

class DeferredExpense(AccountsController):

	def validate(self):
		self.flags.ignore_links = True
		self.validate_category_accounts()

	def before_save(self):
		self.make_adjustment_entries()
		update_balance(self)

	def on_submit(self):
		self.set_status("Submitted")

	def on_cancel(self):
		self.set_status("Cancelled")
		self.unlink_journal_entries()
		self.ignore_doctypes = ["Journal Entry", "GL Entry", "Stock Ledger Entry"]



	def validate_adjustment_entries(self):
		if self.total_number_of_adjustments.is_dirty():
			self.calculate_adjustment_entries()	

	def validate_basics(self):
		# checking if all required fields are filled
		if not self.gross_expense_amount or not self.total_number_of_adjustments or not self.start_service_date:
			return False
		
		if self.gross_expense_amount == 0:
			frappe.throw("The expense amount cannot be zero")
	
	def validate_category_accounts(self):
		if frappe.get_cached_value("Deferred Expense Category", self.deferred_expense_category, "is_group") == 1:
			frappe.throw(_("Deferred Expense Category cannot be parent"))
		if not self.deferred_expense_account:
			frappe.throw(_("Deferred Expense Category does not have Deferred Expense Account"))
		if not self.expense_account:
			frappe.throw(_("Deferred Expense Category does not have Expense Account"))

	def edit_last_adjustment_last_date(self, date = None, months = 0):
		if not date:
			date = add_months(self.start_service_date, months)
		else:
			date = add_months(date, months)
		self.schedules[-1].schedule_date = date

	def unlink_journal_entries(self):
		docs = []
		if self.closing_journal_entry:
			docs.append(self.closing_journal_entry)
		for row in self.get("schedules"):
			if row.journal_entry != None:
				docs.append(row.journal_entry)
		for jv in docs:
			je = frappe.get_doc("Journal Entry", jv)
			je.cancel()
			je.delete(force=True, ignore_permissions=True, delete_permanently=True)

	def set_status(self, status):
		self.db_set("status", status)









	######################################################################################################################
	def make_adjustment_entries(self):
		starting_date , num_of_months, expense_amount = self.start_service_date, self.total_number_of_adjustments, self.gross_expense_amount
		if self.validate_is_existing_expense():
			starting_date = add_months(starting_date, self.number_of_adjustments_booked)
			expense_amount -= self.opening_realized_expense_balance
			num_of_months -= self.number_of_adjustments_booked
		schedules = self.get_adjustment_entries(starting_date, num_of_months, expense_amount, self.validate_is_existing_expense())
		self.set("schedules", schedules)




	def validate_is_existing_expense(self):
		if self.is_existing_expense:
			if self.opening_realized_expense_balance and self.opening_realized_expense_balance != 0:
				if not self.number_of_adjustments_booked:
					frappe.throw(_("Please add Number Of Adjustments Booked"))

				if self.opening_realized_expense_balance >= self.gross_expense_amount:
					frappe.throw(_("Opening Realized Expense Balance must be less than Gross Expense Amount"))

				if self.opening_realized_expense_balance == 0:
					frappe.throw(_("Opening Realized Expense Balance cannot be zero"))

				return True
		else: return False


	def get_adjustment_entries(self, starting_date, num_of_months, expense_amount, deducted = False):
		num_of_entries = num_of_months + 1 if ((getdate(starting_date) != get_first_day(starting_date) 
						 and getdate(starting_date) != get_last_day(starting_date))
						 or (self.is_existing_expense and self.opening_realized_expense_balance < 
						 self.gross_expense_amount * self.number_of_adjustments_booked 
						 / self.total_number_of_adjustments)) else num_of_months
		date = starting_date
		accumulated_amount, schedules = self.gross_expense_amount - expense_amount, []
		for n in range(num_of_entries):
			amount, entry_day = 0, get_last_day(add_months(date, n))
			if n == 0 and num_of_entries != num_of_months and not deducted:
				part = expense_amount / num_of_months
				month_days = date_diff(get_last_day(entry_day), get_last_day(add_months(entry_day, -1)))
				amount_per_day = part / month_days
				first_month_remaining_days = date_diff(get_last_day(date), date) + 1
				amount = first_month_remaining_days * amount_per_day

			elif n+1 == num_of_entries:
				entry_day = add_days(add_months(starting_date, num_of_months), -1)
				amount = self.gross_expense_amount - accumulated_amount
				# frappe.throw(str(accumulated_amount))
				
			else:
				if num_of_entries != num_of_months and not deducted:
					part = expense_amount / num_of_months
					amount = (expense_amount - part) / (num_of_entries - 2)
				elif deducted:
					amount = self.gross_expense_amount / self.total_number_of_adjustments
					if self.opening_realized_expense_balance / self.number_of_adjustments_booked > amount:
						frappe.throw(_("The calculation of Opening Realized Expense Balance over Number Of Adjustments Booked cannot be greater than the Adjustment Amount per month (" + str(amount) + ")"))

				else:
					amount = expense_amount / num_of_entries

			accumulated_amount += amount
			if amount != 0:
				schedules.append({
					"schedule_date": entry_day,
					"adjustment_amount": amount,
					"accumulated_adjustment_amount": accumulated_amount
					})
		return schedules
