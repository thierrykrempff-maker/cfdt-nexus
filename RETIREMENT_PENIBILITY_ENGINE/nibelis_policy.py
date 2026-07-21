"""Prudence and confidentiality rules for synthetic Nibelis metadata."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NibelisPolicyRule:
    rule_id: str
    description: str


NIBELIS_POLICY = (
    NibelisPolicyRule("immutable", "Original synthetic export metadata remains immutable."),
    NibelisPolicyRule("provenance", "Explicit provenance is mandatory."),
    NibelisPolicyRule("reuse_referential", "Rubric and parameter identifiers must come from existing CFDT Nexus referentials."),
    NibelisPolicyRule("no_duplicate_taxonomy", "The connector never redefines rubric categories or payroll business rules."),
    NibelisPolicyRule("no_auto_correction", "Payroll metadata is never corrected automatically."),
    NibelisPolicyRule("no_auto_merge", "Periods and payroll occurrences are never merged automatically."),
    NibelisPolicyRule("no_delete", "Duplicates and inconsistencies remain visible."),
    NibelisPolicyRule("no_retirement_calculation", "No retirement calculation is performed."),
    NibelisPolicyRule("no_decision", "No payroll, legal or administrative decision is made."),
    NibelisPolicyRule("no_real_data", "Real payslips, exports, identities and bank data are prohibited."),
    NibelisPolicyRule("human_review", "Every prepared record remains subject to human review."),
)
