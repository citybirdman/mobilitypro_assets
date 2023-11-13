// Copyright (c) 2023, Ahmed Zaytoon and contributors
// For license information, please see license.txt

frappe.ui.form.on('Deferred Expense', {
	onload: function(frm) {
		frm.set_query("expense_category", {filters: {is_group:0} });
	},
	accounting_dimensions_collapse: function(frm){
		frm.fields_dict.accounting_dimensions_section.collapse();
	},
	expense_category: function(frm){
		if(frm.fields_dict.accounting_dimensions_section.is_collapsed())
			frm.trigger("accounting_dimensions_collapse");
	},
	branch: function(frm){
		if(!frm.fields_dict.accounting_dimensions_section.is_collapsed())
			frm.trigger("accounting_dimensions_collapse");
	},
	cost_center: function(frm){
		if(!frm.fields_dict.accounting_dimensions_section.is_collapsed())
			frm.trigger("accounting_dimensions_collapse");
	}
});
