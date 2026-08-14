# Copyright (c) 2026, Ram and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Table(Document):
	def validate(self):
		if self.capacity is not None and self.capacity <= 0:
			frappe.throw("Capacity must be greater than zero.")
