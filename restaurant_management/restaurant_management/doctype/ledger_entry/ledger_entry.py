# Copyright (c) 2026, Ram and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class LedgerEntry(Document):
	def validate(self):
		if flt(self.debit) > 0 and flt(self.credit) > 0:
			frappe.throw("A Ledger Entry cannot have both Debit and Credit set.")

		if flt(self.debit) == 0 and flt(self.credit) == 0:
			frappe.throw("A Ledger Entry must have either a Debit or a Credit amount.")
