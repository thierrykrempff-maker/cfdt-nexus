"""Mandatory privacy and prudence rules for synthetic payslip metadata."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PayslipPolicyRule:
    rule_id: str
    description: str


PAYSLIP_POLICY = (
    PayslipPolicyRule("immutable", "Original synthetic metadata remains immutable."),
    PayslipPolicyRule("provenance", "Explicit provenance is mandatory for converted records."),
    PayslipPolicyRule("no_auto_correction", "No payroll value is corrected automatically."),
    PayslipPolicyRule("no_merge", "Periods and payroll items are not merged automatically."),
    PayslipPolicyRule("no_delete", "Duplicates and inconsistencies remain visible."),
    PayslipPolicyRule("no_decision", "No legal, payroll or administrative decision is made."),
    PayslipPolicyRule("no_retirement_calculation", "No retirement entitlement, date or amount is calculated."),
    PayslipPolicyRule("no_real_payslip", "Real payslips and document content are prohibited."),
    PayslipPolicyRule("no_identity", "Real names, employee numbers and social-security numbers are prohibited."),
    PayslipPolicyRule("no_bank_data", "IBAN and bank-account data are prohibited."),
    PayslipPolicyRule("human_review", "Prepared information always requires human review."),
)
