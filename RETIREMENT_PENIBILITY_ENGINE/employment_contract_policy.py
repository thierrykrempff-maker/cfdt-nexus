"""Prudence and privacy rules for synthetic employment contracts."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EmploymentContractPolicyRule:
    rule_id: str
    description: str


EMPLOYMENT_CONTRACT_POLICY = (
    EmploymentContractPolicyRule("immutable", "Original synthetic contract metadata remains immutable."),
    EmploymentContractPolicyRule("provenance", "Explicit provenance is mandatory."),
    EmploymentContractPolicyRule("no_auto_merge", "Contracts and amendments are never merged automatically."),
    EmploymentContractPolicyRule("no_auto_correction", "Dates, versions and terms are never corrected automatically."),
    EmploymentContractPolicyRule("no_delete", "Duplicates and superseded versions remain visible."),
    EmploymentContractPolicyRule("no_decision", "No legal or administrative decision is made."),
    EmploymentContractPolicyRule("no_calculation", "No payroll, retirement or entitlement calculation is performed."),
    EmploymentContractPolicyRule("no_real_document", "Real contracts, amendments and document content are prohibited."),
    EmploymentContractPolicyRule("no_identity", "Names, addresses, employee numbers, signatures and social-security numbers are prohibited."),
    EmploymentContractPolicyRule("human_review", "Every prepared change remains subject to human review."),
)
