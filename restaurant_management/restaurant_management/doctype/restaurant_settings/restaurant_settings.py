# Copyright (c) 2026, Ram and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RestaurantSettings(Document):
	def validate(self):
		if self.opening_time and self.closing_time and self.opening_time >= self.closing_time:
			frappe.throw("Opening Time must be before Closing Time.")
