# Copyright (c) 2026, Ram and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Reservation(Document):
	def validate(self):
		if self.party_size is not None and self.party_size <= 0:
			frappe.throw("Party Size must be greater than zero.")
