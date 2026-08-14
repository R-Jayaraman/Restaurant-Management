// Copyright (c) 2026, Ram and contributors
// For license information, please see license.txt

frappe.ui.form.on("Kitchen Order", {
	order(frm) {
		frm.clear_table("items");

		if (!frm.doc.order) {
			frm.refresh_field("items");
			return;
		}

		frappe.call({
			method:
				"restaurant_management.restaurant_management.doctype.kitchen_order.kitchen_order.get_order_items",
			args: { order: frm.doc.order },
			callback: function (r) {
				(r.message || []).forEach(function (row) {
					let child = frm.add_child("items");
					child.order_item = row.name;
					child.item_name = row.item_name;
					child.qty = row.qty;
				});
				frm.refresh_field("items");
			},
		});
	},
});
