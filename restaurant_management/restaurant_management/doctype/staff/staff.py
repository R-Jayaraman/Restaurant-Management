# Copyright (c) 2026, Ram and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class Staff(Document):
	def validate(self):
		if flt(self.salary) < 0:
			frappe.throw("Salary cannot be negative.")
