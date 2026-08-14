# Copyright (c) 2026, Ram and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

from restaurant_management.restaurant_management.doctype.restaurant_payment.restaurant_payment import (
	get_total_paid,
)
from restaurant_management.restaurant_management.accounting import (
	post_order_cancelled_entries,
	post_order_confirmed_entries,
)


class Order(Document):
	def validate(self):
		self.validate_order_type()
		self.validate_items()
		self.calculate_totals()
		self.validate_discount()

	def validate_order_type(self):
		# Table/Reservation are hidden in the form for Takeaway (depends_on), so
		# clear them server-side too rather than erroring on a field the user
		# can no longer see.
		if self.order_type == "Takeaway":
			self.reservation = None
			self.table = None

	def on_update(self):
		if self.status == "Confirmed":
			post_order_confirmed_entries(self)
		elif self.status == "Cancelled":
			post_order_cancelled_entries(self)

	def validate_items(self):
		for item in self.items:
			if flt(item.qty) <= 0:
				frappe.throw(f"Qty must be greater than zero for item {item.item_name or item.menu_item}.")

			if item.menu_item and not frappe.db.get_value("Menu Item", item.menu_item, "is_available"):
				frappe.throw(f"Menu Item {item.item_name or item.menu_item} is not available and cannot be ordered.")

	def calculate_totals(self):
		subtotal = 0.0
		tax_amount = 0.0

		for item in self.items:
			item.amount = flt(item.qty) * flt(item.rate)
			subtotal += item.amount

			item_tax_rate = frappe.db.get_value("Menu Item", item.menu_item, "tax_rate") or 0
			tax_amount += item.amount * flt(item_tax_rate) / 100

		self.subtotal = subtotal
		self.tax_amount = tax_amount
		self.total_amount = subtotal + tax_amount - flt(self.discount_amount)
		self.balance_amount = self.total_amount - get_total_paid(self.name)

	def validate_discount(self):
		if flt(self.discount_amount) < 0:
			frappe.throw("Discount Amount cannot be negative.")

		if flt(self.discount_amount) > flt(self.subtotal):
			frappe.throw("Discount Amount cannot be greater than Subtotal.")
