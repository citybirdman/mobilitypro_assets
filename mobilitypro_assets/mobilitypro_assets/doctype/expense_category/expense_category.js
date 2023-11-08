// Copyright (c) 2023, Ahmed Zaytoon and contributors
// For license information, please see license.txt

frappe.ui.form.on('Expense Category', {
	onload: function(frm){
		frm.set_query("defered_expense_account", {filters: {root_type: 'Asset', is_group:0} });
		frm.set_query("expense_account", {filters: {root_type: 'Expense', is_group:0} });
		frm.set_query("parent_expense_category", {filters: {is_group:1} });
	}
});
