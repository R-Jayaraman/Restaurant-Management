# Copyright (c) 2026, Ram and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class Purchase(Document):
	def validate(self):
		self.validate_items()
		self.calculate_totals()

	def validate_items(self):
		for item in self.items:
			if flt(item.qty) <= 0:
				frappe.throw(f"Qty must be greater than zero for item {item.item_name or item.item}.")

			if flt(item.rate) < 0:
				frappe.throw(f"Rate cannot be negative for item {item.item_name or item.item}.")

			if item.item and not frappe.db.get_value("Inventory Item", item.item, "is_active"):
				frappe.throw(f"Inventory Item {item.item_name or item.item} is inactive and cannot be purchased.")

	def calculate_totals(self):
		total_amount = 0.0

		for item in self.items:
			item.amount = flt(item.qty) * flt(item.rate)
			total_amount += item.amount

		self.total_amount = total_amount
