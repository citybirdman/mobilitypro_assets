# Copyright (c) 2023, Ahmed Zaytoon and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.delete_doc import update_flags
from frappe.utils import (add_months, date_diff, get_last_day, get_first_day, getdate)
from mobilitypro_assets.tasks import update_balance

from erpnext.controllers.accounts_controller import AccountsController

class DeferredExpense(AccountsController):

	def validate(self):
		self.flags.ignore_links = True

	def before_save(self):
		self.calculate_adjustment_entries()
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


	def calculate_adjustment_entries(self):
		if(self.validate_basics()):
			return
			
		expense_amount = self.deduct_opening()
		number_of_adjustments = self.total_number_of_adjustments
		#	clearing the table
		self.set("schedules", [])
		#	validating adjustments and date
		accumulated_amount, last_day, check_month = (self.opening_realized_expense_balance or 0, "", 0)
		# frappe.throw(frappe.utils.cstr(get_first_day(self.start_service_date) == getdate(self.start_service_date)))
		if get_first_day(self.start_service_date) == getdate(self.start_service_date):
			last_day = get_last_day(self.start_service_date)
		elif get_last_day(self.start_service_date) == getdate(self.start_service_date):
			last_day = add_months(get_last_day(self.start_service_date), 1)
		else:
			if not self.number_of_adjustments_booked:
				last_day = get_last_day(self.start_service_date)
				check_month = 1
			else:
				last_day = add_months(get_last_day(self.start_service_date), self.number_of_adjustments_booked)
		monthly_amount = self.gross_expense_amount / number_of_adjustments
		entries_number = number_of_adjustments + check_month
		if self.number_of_adjustments_booked and self.is_existing_expense:
			entries_number -= self.number_of_adjustments_booked - 1

		for n in range(entries_number):
			#	checking the start service date
			if n != 0:
				last_day = get_last_day(add_months(last_day, 1))
			amount = monthly_amount
			if(n == 0 and check_month == 1):
				month_range = date_diff(last_day, get_first_day(self.start_service_date)) + 1
				amount = monthly_amount * date_diff(last_day, self.start_service_date)/month_range

			elif n is (entries_number - 1):
				amount = self.gross_expense_amount - accumulated_amount
			if self.gross_expense_amount == accumulated_amount:
				break
			accumulated_amount += amount
			self.append(
				"schedules",
				{
					"schedule_date": last_day,
					"adjustment_amount": amount,
					"accumulated_adjustment_amount": accumulated_amount,
				},
			)
		if(check_month):
			self.edit_last_adjustment_last_date(months= self.total_number_of_adjustments + check_month -1)
			

	def validate_basics(self):
		# checking if all required fields are filled
		if not self.gross_expense_amount or not self.total_number_of_adjustments or not self.start_service_date:
			return False
		
		if self.gross_expense_amount == 0:
			frappe.throw("The expense amount cannot be zero")


	def deduct_opening(self):
		expense_amount, number_of_adjustments = (self.gross_expense_amount, self.total_number_of_adjustments)
		if self.is_existing_expense:	
			if self.opening_realized_expense_balance and self.opening_realized_expense_balance != 0:

				if not self.number_of_adjustments_booked:
					frappe.throw(_("Please add Number Of Adjustments Booked"))

				if self.opening_realized_expense_balance == expense_amount:
					frappe.throw(_("Opening Realized Expense Balance must be less than Gross Expense Amount"))

				#	calculating the remaining balance and number of adjustments
				expense_amount -= self.opening_realized_expense_balance
			else:
				frappe.throw("For existing expense Opening Realized Expense Balance cannot be Zero")

		return expense_amount

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
