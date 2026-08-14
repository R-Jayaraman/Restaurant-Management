# Copyright (c) 2026, Ram and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class StockTransaction(Document):
	def validate(self):
		qty = flt(self.qty)

		if qty == 0:
			frappe.throw("Qty cannot be zero.")

		if self.transaction_type == "Purchase" and qty < 0:
			frappe.throw("Qty must be positive for a Purchase transaction.")

		if self.transaction_type == "Waste" and qty > 0:
			frappe.throw("Qty must be negative for a Waste transaction.")
