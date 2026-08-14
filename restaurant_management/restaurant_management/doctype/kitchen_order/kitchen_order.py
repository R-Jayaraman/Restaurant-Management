# Copyright (c) 2026, Ram and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class KitchenOrder(Document):
	def validate(self):
		self.validate_order_not_cancelled()

	def validate_order_not_cancelled(self):
		if self.order and frappe.db.get_value("Order", self.order, "status") == "Cancelled":
			frappe.throw("Cannot create a Kitchen Order against a Cancelled Order.")


@frappe.whitelist()
def get_order_items(order):
	"""Return the Order Item rows of the given Order, for copying into a Kitchen Order."""
	if not order:
		return []

	return frappe.get_all(
		"Order Item",
		filters={"parent": order},
		fields=["name", "item_name", "qty"],
		order_by="idx asc",
	)
