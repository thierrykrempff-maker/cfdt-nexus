"""Traceable models for the Alsace-Moselle local-law audit layer."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field

APPLICABILITY_STATUSES = frozenset({"applicable","probably_applicable","applicability_uncertain","not_applicable","insufficient_information"})
CURRENT_STATUSES = frozenset({"verification_required","not_investigated","validated","historical"})
LOCAL_DEPARTMENTS = frozenset({"57","67","68","moselle","bas-rhin","haut-rhin"})

@dataclass(frozen=True)
class LocalRule:
    local_rule_id: str; title: str; legal_area: str
    territorial_scope: tuple[str,...]; personal_scope: tuple[str,...] = ("employee",)
    employer_scope: tuple[str,...] = (); establishment_scope: tuple[str,...] = ()
    applicability_conditions: tuple[str,...] = (); exclusions: tuple[str,...] = ()
    legal_references: tuple[str,...] = (); authority_level: str = "primary_law"
    effective_from: str|None = None; effective_to: str|None = None
    current_status: str = "verification_required"; comparison_required: bool = True
    payroll_impact_hint: str|None = None; protection_sociale_impact_hint: str|None = None
    source_ids: tuple[str,...] = (); warnings: tuple[str,...] = (); schema_version: str = "1.0"
    def __post_init__(self):
        if self.current_status not in CURRENT_STATUSES: raise ValueError("invalid current_status")
        if not self.local_rule_id or not self.legal_references: raise ValueError("rule identity and references required")
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class EmploymentContext:
    habitual_work_department: str|None = None; establishment_department: str|None = None
    employer_head_office_department: str|None = None; contract_location_department: str|None = None
    multiple_work_departments: tuple[str,...] = (); telework: bool = False
    temporary_assignment: bool = False; municipality: str|None = None

@dataclass(frozen=True)
class ApplicabilityAssessment:
    status: str; considered_facts: tuple[str,...]; assumptions: tuple[str,...]
    missing_facts: tuple[str,...]; warnings: tuple[str,...]; confidence: str
    def __post_init__(self):
        if self.status not in APPLICABILITY_STATUSES: raise ValueError("invalid applicability status")

@dataclass(frozen=True)
class TriggerAssessment:
    local_law_check_required: bool; local_law_domains_to_check: tuple[str,...]
    applicability_status: str; missing_facts: tuple[str,...]
    source_queries: tuple[str,...]; warnings: tuple[str,...]
