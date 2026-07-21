"""Audience-safe explainable reports for career evidence."""

from __future__ import annotations

import re

from .career_evidence_models import (
    CareerEvidenceItem,
    CareerEvidenceReport,
    EvidenceBundle,
    EvidenceRelationType,
    EvidenceReportView,
    EvidenceResolution,
    EvidenceResolutionState,
    EvidenceSourceType,
)


_SENSITIVE_MARKERS = ("secret", "token", "password", "diagnosis", "medical detail", "nir")


def _safe(value: str) -> str:
    lowered = value.lower()
    if any(marker in lowered for marker in _SENSITIVE_MARKERS):
        return "[REDACTED]"
    if re.search(r"(?:^|\s)[a-zA-Z]:[\\/]", value) or value.startswith(("/", "\\\\")):
        return "[REDACTED]"
    return value


class CareerEvidenceReportBuilder:
    """Create employee or expert projections without exposing forbidden data."""

    def build(
        self,
        bundle: EvidenceBundle,
        resolution: EvidenceResolution,
        subject_id: str,
        view: EvidenceReportView,
    ) -> CareerEvidenceReport:
        relevant = self._relevant_evidence(bundle, subject_id)
        supporting = self._by_relations(
            bundle,
            subject_id,
            {
                EvidenceRelationType.SUPPORTS,
                EvidenceRelationType.PARTIALLY_SUPPORTS,
                EvidenceRelationType.CORROBORATES,
            },
            view,
        )
        contradictory = self._by_relations(
            bundle, subject_id, {EvidenceRelationType.CONTRADICTS}, view
        )
        contextual = self._by_relations(
            bundle, subject_id, {EvidenceRelationType.CONTEXTUALIZES}, view
        )
        collective = tuple(
            self._label(item, view)
            for item in relevant
            if item.reference.source_type
            in {EvidenceSourceType.INEOS_AGREEMENT, EvidenceSourceType.COLLECTIVE_AGREEMENT}
        )
        claims = tuple(
            _safe(claim.statement)
            for claim in bundle.claims
            if claim.subject_id == subject_id
        )
        gaps = tuple(_safe(gap.description) for gap in bundle.gaps if gap.subject_id == subject_id)
        provenance = tuple(
            _safe(item.reference.provenance)
            for item in relevant
            if item.reference.provenance
        )
        passages = ()
        if view is EvidenceReportView.EXPERT_VIEW:
            passage_ids = {
                relation.target_id
                for relation in bundle.relations
                if relation.source_kind == "EVIDENCE"
                and relation.source_id in {str(item.reference.evidence_id) for item in relevant}
                and relation.target_kind == "DOCUMENT_PASSAGE"
            }
            passages = tuple(
                _safe(f"{passage.document_id}: {passage.locator}")
                for passage in bundle.passages
                if passage.passage_id in passage_ids
            )
        warnings = (
            "This report contains documentary metadata only.",
            "Sensitive and medical details are not reproduced.",
            "No legal or retirement entitlement is determined.",
        )
        return CareerEvidenceReport(
            view=view,
            subject_id=subject_id if view is EvidenceReportView.EXPERT_VIEW else "career subject",
            claims_examined=claims,
            supporting_evidence=supporting,
            contradictory_evidence=contradictory,
            contextual_evidence=contextual,
            collective_rules=collective,
            missing_documents=gaps,
            confirmation_level=resolution.state,
            official_validation_required=resolution.state
            in {
                EvidenceResolutionState.REQUIRES_OFFICIAL_VALIDATION,
                EvidenceResolutionState.INSUFFICIENT_EVIDENCE,
                EvidenceResolutionState.CONFLICTED,
            },
            provenance=provenance,
            warnings=warnings,
            passages=passages,
            resolution_reasons=resolution.reasons if view is EvidenceReportView.EXPERT_VIEW else (),
        )

    @staticmethod
    def _relevant_evidence(bundle: EvidenceBundle, subject_id: str) -> tuple[CareerEvidenceItem, ...]:
        ids = {
            relation.source_id
            for relation in bundle.relations
            if relation.source_kind == "EVIDENCE" and relation.target_id == subject_id
        }
        return tuple(item for item in bundle.evidence if str(item.reference.evidence_id) in ids)

    def _by_relations(
        self,
        bundle: EvidenceBundle,
        subject_id: str,
        relation_types: set[EvidenceRelationType],
        view: EvidenceReportView,
    ) -> tuple[str, ...]:
        ids = {
            relation.source_id
            for relation in bundle.relations
            if relation.source_kind == "EVIDENCE"
            and relation.target_id == subject_id
            and relation.relation_type in relation_types
        }
        return tuple(
            self._label(item, view)
            for item in bundle.evidence
            if str(item.reference.evidence_id) in ids
        )

    @staticmethod
    def _label(item: CareerEvidenceItem, view: EvidenceReportView) -> str:
        if item.reference.source_type is EvidenceSourceType.MEDICAL_OR_ATMP_NOTIFICATION:
            return "Restricted documentary reference"
        if view is EvidenceReportView.EMPLOYEE_VIEW:
            return item.reference.source_type.value.replace("_", " ").title()
        return _safe(
            f"{item.reference.source_type.value}: {item.reference.title} "
            f"[{item.reference.reference}] ({item.status.value})"
        )
