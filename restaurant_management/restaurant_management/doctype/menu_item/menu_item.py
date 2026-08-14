# Copyright (c) 2026, Ram and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class MenuItem(Document):
	def validate(self):
		if flt(self.price) <= 0:
			frappe.throw("Price must be greater than zero.")

		if flt(self.tax_rate) < 0 or flt(self.tax_rate) > 100:
			frappe.throw("Tax Rate must be between 0 and 100.")
