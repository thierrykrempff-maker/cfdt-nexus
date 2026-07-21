"""Declarative document-rule models with no legal interpretation logic."""

from __future__ import annotations

from dataclasses import dataclass

from .document_knowledge_models import DocumentPeriod, DocumentPriority, DocumentValidity


@dataclass(frozen=True)
class ApplicableRule:
    """Rule metadata candidate; it does not assert an individual entitlement."""

    rule_id: str
    label: str
    conditions: tuple[str, ...]
    document_ids: tuple[str, ...]
    priority: DocumentPriority
    domain: str
    validity_period: DocumentPeriod
    validity: DocumentValidity
    source_ids: tuple[str, ...]
    authority_level: str
    minimum_evidence: tuple[str, ...]


@dataclass(frozen=True)
class RuleCandidate:
    """Possible rule reference awaiting documentary and expert validation."""

    candidate_id: str
    rule: ApplicableRule
    matched_criteria: tuple[str, ...]
    missing_evidence: tuple[str, ...] = ()
    official_validation_required: bool = True
