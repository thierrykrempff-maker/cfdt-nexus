"""Implementation-independent contract for the Career Evidence Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .career_evidence_models import (
    CareerEvidenceItem,
    CareerEvidenceReport,
    DocumentPassageReference,
    EvidenceBundle,
    EvidenceClaim,
    EvidenceConflict,
    EvidenceGap,
    EvidenceId,
    EvidenceRelationType,
    EvidenceReportView,
    EvidenceResolution,
)


@dataclass(frozen=True)
class CareerEvidenceSafetyContract:
    """Architecture-only constraints for evidence handling."""

    status: str = "ARCHITECTURE_ONLY"
    enabled: bool = False
    real_documents_allowed: bool = False
    document_content_allowed: bool = False
    network_allowed: bool = False
    scraping_allowed: bool = False
    download_allowed: bool = False
    retirement_calculation_allowed: bool = False
    c2p_calculation_allowed: bool = False


CAREER_EVIDENCE_SAFETY_CONTRACT = CareerEvidenceSafetyContract()


class CareerEvidencePort(Protocol):
    """Stable operations implemented by ``CareerEvidenceEngine``."""

    def create_empty_bundle(self, bundle_id: str) -> EvidenceBundle: ...

    def attach_evidence_to_event(
        self,
        bundle: EvidenceBundle,
        event_id: str,
        evidence: CareerEvidenceItem,
        relation_type: EvidenceRelationType = EvidenceRelationType.SUPPORTS,
    ) -> EvidenceBundle: ...

    def attach_evidence_to_period(
        self,
        bundle: EvidenceBundle,
        period_id: str,
        evidence: CareerEvidenceItem,
        relation_type: EvidenceRelationType = EvidenceRelationType.SUPPORTS,
    ) -> EvidenceBundle: ...

    def attach_document_passage(
        self,
        bundle: EvidenceBundle,
        evidence_id: EvidenceId,
        passage: DocumentPassageReference,
    ) -> EvidenceBundle: ...

    def remove_evidence(self, bundle: EvidenceBundle, evidence_id: EvidenceId) -> EvidenceBundle: ...

    def register_claim(self, bundle: EvidenceBundle, claim: EvidenceClaim) -> EvidenceBundle: ...

    def register_conflict(self, bundle: EvidenceBundle, conflict: EvidenceConflict) -> EvidenceBundle: ...

    def register_missing_evidence(self, bundle: EvidenceBundle, gap: EvidenceGap) -> EvidenceBundle: ...

    def resolve_evidence_state(
        self, bundle: EvidenceBundle, subject_id: str | None = None
    ) -> EvidenceResolution: ...

    def generate_evidence_report(
        self,
        bundle: EvidenceBundle,
        subject_id: str,
        view: EvidenceReportView,
    ) -> CareerEvidenceReport: ...


__all__ = (
    "CareerEvidencePort",
    "CAREER_EVIDENCE_SAFETY_CONTRACT",
)
