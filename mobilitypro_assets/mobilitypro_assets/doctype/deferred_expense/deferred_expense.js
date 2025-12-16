// Copyright (c) 2023, Ahmed Zaytoon and contributors
// For license information, please see license.txt

frappe.ui.form.on('Deferred Expense', {
	setup: function(frm){
		frm.ignore_doctypes_on_cancel_all = ['Journal Entry'];
		frappe.flags.ignore_links = true
	},
	onload: function(frm) {
		frm.set_query("deferred_expense_category", {filters: {is_group:0} });
	},
	accounting_dimensions_collapse: function(frm){
		frm.fields_dict.accounting_dimensions_section.collapse();
	},
	is_existing_expense: function(frm){
		if(!frm.doc.is_existing_expense){
			frm.doc.opening_realized_expense_balance = 0
			frm.doc.number_of_adjustments_booked = 0
		}
	},
	// insert:function(frm){
	// 	if(frm.doc.docstatus == 0){
	// 		frm.doc.closing_date = "";
	// 		frm.doc.closing_journal_entry = "";
	// 	}
	// },
	refresh: function(frm){
		if(frm.doc.gross_expense_amount - frm.doc.accumulated_adjustment_amount != frm.doc.balance_after_adjustments && frm.doc.accumulated_adjustment_amount)
			frm.set_value('balance_after_adjustments', frm.doc.gross_expense_amount - frm.doc.accumulated_adjustment_amount)
		if(frm.doc.docstatus == 1 && !frm.doc.closing_date){
			frm.add_custom_button(
				__('Close'), 
				function(){
					let d = new frappe.ui.Dialog({
						title: 'Confirmation',
						fields: [
							{
								label: __('Information'),
								fieldtype: 'HTML',
								options: '<p>Please add Closing Journal Entry if exist</p>',
							},
							{
								label: 'Closing Journal Entry',
								fieldname: 'closing_entry',
								fieldtype: 'Link',
								options: 'Journal Entry',
								default: '',
								get_query() {
									return {
										filters: {
											docstatus: 1,
											company: frm.doc.company
										}
									};
								}
							}
						],
						size: 'small', // small, large, extra-large 
						primary_action_label: 'Confirm',
						primary_action(values) {
							frappe.call({
								method: "mobilitypro_assets.tasks.close_expense",
								type: "POST",
								args: {
										document: frm.doc.name,
										jv : values.closing_entry
									} 
								}).then(()=>{frm.reload_doc()});
							d.hide();
						},
						secondary_action_label: 'Abort',
						secondary_action(){d.hide()}
					});
					
					d.show();
				}
			).css({'background-color': '#343a40', 'border-color': '#343a40', 'color':'#fff'});
		}
		if (frm.doc.docstatus === 1 && frm.doc.status === "Closed") {
			const closing_jv = frm.doc.closing_journal_entry || frm.doc.closing_journal_entry_name || "";

			frm.add_custom_button(__('Re-open'), function () {

				const msg = closing_jv
				? __(`This will CANCEL the closing Journal Entry <b>${closing_jv}</b> and re-open the schedule. Continue?`)
				: __('This will CANCEL the closing Journal Entry and re-open the schedule. Continue?');

				frappe.confirm(msg, () => {
					frappe.call({
						method: "mobilitypro_assets.tasks.reopen_expense",
						args: { document: frm.doc.name }
					}).then(() => {
						frm.reload_doc();
					});
				});

			}).addClass('btn-warning');
		}
	}
});
