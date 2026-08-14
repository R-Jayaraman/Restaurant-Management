# Copyright (c) 2026, Ram and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

from restaurant_management.restaurant_management.accounting import (
	delete_payment_ledger_entries,
	sync_payment_ledger_entries,
)


class RestaurantPayment(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw("Amount must be greater than zero.")

		if self.order and frappe.db.get_value("Order", self.order, "status") == "Cancelled":
			frappe.throw("Cannot record a Payment against a Cancelled Order.")

		self.validate_against_balance()

	def validate_against_balance(self):
		if not self.order:
			return

		order_balance = flt(frappe.db.get_value("Order", self.order, "balance_amount"))

		# Editing an existing payment: the Order's current balance already reflects
		# this payment's own prior amount, so add that back before comparing,
		# otherwise a valid edit (e.g. correcting 300 -> 320) would be wrongly blocked.
		previous = self.get_doc_before_save()
		previous_amount = flt(previous.amount) if previous else 0
		available = order_balance + previous_amount

		if flt(self.amount) > available + 0.01:
			frappe.throw(f"Amount ({self.amount}) cannot exceed the remaining balance ({available}).")

	def on_update(self):
		update_order_payment_status(self.order)
		sync_payment_ledger_entries(self)

	def on_trash(self):
		# Must remove the Ledger Entries here (before deletion), not in
		# after_delete: Frappe's own dynamic-link integrity check runs
		# between on_trash and the actual delete, and would block deleting
		# this Payment while a Ledger Entry still references it.
		delete_payment_ledger_entries(self.name)

	def after_delete(self):
		# Must recalculate here, not on_trash: the Payment row still exists
		# in the database during on_trash, which would make the balance sum
		# stale by still counting the payment that's about to be removed.
		update_order_payment_status(self.order)


def get_total_paid(order_name):
	"""Sum of all Restaurant Payments recorded against the given Order."""
	return flt(
		frappe.db.sql("select sum(amount) from `tabRestaurant Payment` where `order` = %s", order_name)[0][0]
	)


def update_order_payment_status(order_name):
	if not order_name or not frappe.db.exists("Order", order_name):
		return

	total_paid = get_total_paid(order_name)
	total_amount = flt(frappe.db.get_value("Order", order_name, "total_amount"))
	balance_amount = total_amount - total_paid

	if total_paid <= 0:
		status = "Unpaid"
	elif total_paid < total_amount:
		status = "Partial"
	else:
		status = "Paid"

	current = frappe.db.get_value("Order", order_name, ["payment_status", "balance_amount"], as_dict=True)
	if current.payment_status != status or flt(current.balance_amount) != balance_amount:
		frappe.db.set_value(
			"Order", order_name, {"payment_status": status, "balance_amount": balance_amount}
		)
