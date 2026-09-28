frappe.listview_settings['Deferred Expense'] = {
	add_fields: ['status'],
	get_indicator: function (doc) {
		if (doc.status === "Fully Adjusted") {
			return [__("Fully Adjusted"), "green", "status,=,Fully Adjusted"];

		} else if (doc.status === "Partially Adjusted") {
			return [__("Partially Adjusted"), "grey", "status,=,Partially Adjusted"];

		} else if (doc.status === "Closed") {
			return [__("Closed"), "green", "status,=,Sold"];

		}
	}
}
