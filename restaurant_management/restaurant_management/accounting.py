# Copyright (c) 2026, Ram and contributors
# For license information, please see license.txt

"""
Shared minimal double-entry accounting helpers.

Used by both Order (post/reverse Sales, Tax, Receivable on status change)
and Restaurant Payment (post Cash/Bank vs Receivable on payment, keep in
sync on edit/delete). Kept here, not inside either doctype's controller,
so the two don't need to import from each other for this.
"""

import frappe
from frappe.utils import flt

ACCOUNT_RECEIVABLE = "Customer Receivable"
ACCOUNT_SALES = "Sales Revenue"
ACCOUNT_TAX = "Tax Payable"

ACCOUNT_TYPES = {
	ACCOUNT_RECEIVABLE: "Asset",
	ACCOUNT_SALES: "Income",
	ACCOUNT_TAX: "Liability",
}


def get_or_create_account(account_name):
	"""The 3 core system accounts (Receivable/Sales/Tax) are required for
	posting to work at all, so they're ensured to exist rather than making
	the user set up a chart of accounts before the app is usable."""
	if not frappe.db.exists("Account", account_name):
		frappe.get_doc(
			{
				"doctype": "Account",
				"account_name": account_name,
				"account_type": ACCOUNT_TYPES[account_name],
			}
		).insert(ignore_permissions=True)
	return account_name


def get_payment_mode_account(payment_mode):
	account = frappe.db.get_value("Payment Mode Account", payment_mode, "account")
	if not account:
		frappe.throw(
			f"No Account configured for payment mode '{payment_mode}'. "
			f"Create a Payment Mode Account record for it first."
		)
	return account


def make_ledger_entry(
	account, debit, credit, against_voucher_type, against_voucher, customer=None, remarks=None, posting_date=None
):
	if flt(debit) == 0 and flt(credit) == 0:
		return
	frappe.get_doc(
		{
			"doctype": "Ledger Entry",
			"posting_date": posting_date or frappe.utils.today(),
			"account": account,
			"debit": flt(debit),
			"credit": flt(credit),
			"against_voucher_type": against_voucher_type,
			"against_voucher": against_voucher,
			"customer": customer,
			"remarks": remarks,
		}
	).insert(ignore_permissions=True)


def _has_entries(order_name, remarks_like):
	return frappe.db.exists(
		"Ledger Entry",
		{"against_voucher_type": "Order", "against_voucher": order_name, "remarks": ["like", remarks_like]},
	)


def post_order_confirmed_entries(order_doc):
	"""Debit Receivable, Credit Sales + Tax. Idempotent: skipped if already posted."""
	if _has_entries(order_doc.name, "Order Confirmed%"):
		return

	receivable = get_or_create_account(ACCOUNT_RECEIVABLE)
	sales = get_or_create_account(ACCOUNT_SALES)
	tax = get_or_create_account(ACCOUNT_TAX)

	net_sales = flt(order_doc.subtotal) - flt(order_doc.discount_amount)
	remarks = f"Order Confirmed - {order_doc.name}"

	make_ledger_entry(
		receivable, flt(order_doc.total_amount), 0, "Order", order_doc.name, order_doc.customer, remarks, order_doc.order_date
	)
	make_ledger_entry(sales, 0, net_sales, "Order", order_doc.name, order_doc.customer, remarks, order_doc.order_date)
	make_ledger_entry(
		tax, 0, flt(order_doc.tax_amount), "Order", order_doc.name, order_doc.customer, remarks, order_doc.order_date
	)


def post_order_cancelled_entries(order_doc):
	"""Reverse the Confirmed entries (Credit Receivable, Debit Sales + Tax).
	Does not delete the original entries — preserves history. Idempotent,
	and only reverses if the order actually had Confirmed entries to reverse."""
	if not _has_entries(order_doc.name, "Order Confirmed%"):
		return
	if _has_entries(order_doc.name, "Order Cancelled%"):
		return

	receivable = get_or_create_account(ACCOUNT_RECEIVABLE)
	sales = get_or_create_account(ACCOUNT_SALES)
	tax = get_or_create_account(ACCOUNT_TAX)

	net_sales = flt(order_doc.subtotal) - flt(order_doc.discount_amount)
	remarks = f"Order Cancelled (reversal) - {order_doc.name}"

	make_ledger_entry(receivable, 0, flt(order_doc.total_amount), "Order", order_doc.name, order_doc.customer, remarks)
	make_ledger_entry(sales, net_sales, 0, "Order", order_doc.name, order_doc.customer, remarks)
	make_ledger_entry(tax, flt(order_doc.tax_amount), 0, "Order", order_doc.name, order_doc.customer, remarks)


def sync_payment_ledger_entries(payment_doc):
	"""Delete-and-recreate the two entries for this Payment (Debit payment-mode
	account, Credit Receivable), keeping create and edit consistent with one
	code path instead of two."""
	frappe.db.delete(
		"Ledger Entry", {"against_voucher_type": "Restaurant Payment", "against_voucher": payment_doc.name}
	)

	if flt(payment_doc.amount) <= 0 or not payment_doc.order:
		return

	account = get_payment_mode_account(payment_doc.payment_mode)
	receivable = get_or_create_account(ACCOUNT_RECEIVABLE)
	customer = frappe.db.get_value("Order", payment_doc.order, "customer")
	remarks = f"Payment Received - {payment_doc.name}"

	make_ledger_entry(
		account, flt(payment_doc.amount), 0, "Restaurant Payment", payment_doc.name, customer, remarks, payment_doc.payment_date
	)
	make_ledger_entry(
		receivable, 0, flt(payment_doc.amount), "Restaurant Payment", payment_doc.name, customer, remarks, payment_doc.payment_date
	)


def delete_payment_ledger_entries(payment_name):
	frappe.db.delete(
		"Ledger Entry", {"against_voucher_type": "Restaurant Payment", "against_voucher": payment_name}
	)
