"""Prudence and confidentiality rules for synthetic Kelio metadata."""

from dataclasses import dataclass


@dataclass(frozen=True)
class KelioPolicyRule:
    rule_id: str
    description: str


KELIO_POLICY = (
    KelioPolicyRule("immutable", "Original synthetic export metadata remains immutable."),
    KelioPolicyRule("provenance", "Explicit provenance is mandatory."),
    KelioPolicyRule("no_auto_correction", "Schedules, dates and counters are never corrected automatically."),
    KelioPolicyRule("no_auto_merge", "Working periods and counters are never merged automatically."),
    KelioPolicyRule("no_delete", "Duplicates and inconsistencies remain visible."),
    KelioPolicyRule("no_decision", "No legal, payroll or administrative decision is made."),
    KelioPolicyRule("no_calculation", "No entitlement, payroll or retirement calculation is performed."),
    KelioPolicyRule("no_real_export", "Real exports and file content are prohibited."),
    KelioPolicyRule("no_identity", "Names, employee numbers and Kelio identifiers are prohibited."),
    KelioPolicyRule("human_review", "Every prepared record remains subject to human review."),
)
