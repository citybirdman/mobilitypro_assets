# Copyright (c) 2023, Ahmed Zaytoon and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.delete_doc import update_flags
from frappe.utils import (add_months, date_diff, get_last_day, get_first_day, add_days, getdate, flt)
from mobilitypro_assets.tasks import update_balance

from frappe.model.document import Document
from erpnext.controllers.accounts_controller import AccountsController

class DeferredExpense(Document):
	pass