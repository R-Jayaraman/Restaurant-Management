# Copyright (c) 2026, Ram and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class InventoryItem(Document):
	def validate(self):
		if flt(self.standard_rate) < 0:
			frappe.throw("Standard Rate cannot be negative.")

		if flt(self.reorder_level) < 0:
			frappe.throw("Reorder Level cannot be negative.")
