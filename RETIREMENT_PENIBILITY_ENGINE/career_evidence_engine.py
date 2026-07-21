"""Concrete coordination for the Career Evidence Engine."""

from __future__ import annotations

from .career_evidence_graph import CareerEvidenceGraph
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
from .career_evidence_report import CareerEvidenceReportBuilder
from .career_evidence_resolver import CareerEvidenceResolver
from .privacy_gate import RetirementPrivacyGate, require_privacy_gate


class CareerEvidenceEngine:
    """Coordinate immutable graph, resolution and report operations."""

    def __init__(
        self,
        graph: CareerEvidenceGraph | None = None,
        resolver: CareerEvidenceResolver | None = None,
        report_builder: CareerEvidenceReportBuilder | None = None,
        privacy_gate=RetirementPrivacyGate(),
    ) -> None:
        self._graph = graph or CareerEvidenceGraph()
        self._resolver = resolver or CareerEvidenceResolver()
        self._report_builder = report_builder or CareerEvidenceReportBuilder()
        self._privacy_gate = privacy_gate

    def create_empty_bundle(self, bundle_id: str) -> EvidenceBundle:
        return self._graph.create_empty(bundle_id)

    def attach_evidence_to_event(
        self,
        bundle: EvidenceBundle,
        event_id: str,
        evidence: CareerEvidenceItem,
        relation_type: EvidenceRelationType = EvidenceRelationType.SUPPORTS,
    ) -> EvidenceBundle:
        require_privacy_gate(self._privacy_gate).assert_safe((bundle, evidence))
        return self._graph.attach_to_subject(
            bundle, "CAREER_EVENT", event_id, evidence, relation_type
        )

    def attach_evidence_to_period(
        self,
        bundle: EvidenceBundle,
        period_id: str,
        evidence: CareerEvidenceItem,
        relation_type: EvidenceRelationType = EvidenceRelationType.SUPPORTS,
    ) -> EvidenceBundle:
        require_privacy_gate(self._privacy_gate).assert_safe((bundle, evidence))
        return self._graph.attach_to_subject(
            bundle, "CAREER_PERIOD", period_id, evidence, relation_type
        )

    def attach_document_passage(
        self,
        bundle: EvidenceBundle,
        evidence_id: EvidenceId,
        passage: DocumentPassageReference,
    ) -> EvidenceBundle:
        require_privacy_gate(self._privacy_gate).assert_safe((bundle, passage))
        return self._graph.attach_passage(bundle, evidence_id, passage)

    def remove_evidence(
        self, bundle: EvidenceBundle, evidence_id: EvidenceId
    ) -> EvidenceBundle:
        """Logically reject evidence while preserving provenance and relations."""

        require_privacy_gate(self._privacy_gate).assert_safe(bundle)
        return self._graph.mark_removed(bundle, evidence_id)

    def register_claim(
        self, bundle: EvidenceBundle, claim: EvidenceClaim
    ) -> EvidenceBundle:
        require_privacy_gate(self._privacy_gate).assert_safe((bundle, claim))
        return self._graph.add_claim(bundle, claim)

    def register_conflict(
        self, bundle: EvidenceBundle, conflict: EvidenceConflict
    ) -> EvidenceBundle:
        require_privacy_gate(self._privacy_gate).assert_safe((bundle, conflict))
        return self._graph.add_conflict(bundle, conflict)

    def register_missing_evidence(
        self, bundle: EvidenceBundle, gap: EvidenceGap
    ) -> EvidenceBundle:
        require_privacy_gate(self._privacy_gate).assert_safe((bundle, gap))
        return self._graph.add_gap(bundle, gap)

    def resolve_evidence_state(
        self, bundle: EvidenceBundle, subject_id: str | None = None
    ) -> EvidenceResolution:
        require_privacy_gate(self._privacy_gate).assert_safe(bundle)
        return self._resolver.resolve(bundle, subject_id)

    def generate_evidence_report(
        self,
        bundle: EvidenceBundle,
        subject_id: str,
        view: EvidenceReportView,
    ) -> CareerEvidenceReport:
        require_privacy_gate(self._privacy_gate).assert_safe(bundle)
        resolution = self.resolve_evidence_state(bundle, subject_id)
        return self._report_builder.build(bundle, resolution, subject_id, view)


__all__ = ("CareerEvidenceEngine",)
