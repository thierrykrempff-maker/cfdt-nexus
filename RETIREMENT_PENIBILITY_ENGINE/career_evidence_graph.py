"""Controlled immutable graph operations for career evidence."""

from __future__ import annotations

from dataclasses import replace

from .career_evidence_models import (
    CareerEvidenceItem,
    DocumentPassageReference,
    EvidenceBundle,
    EvidenceClaim,
    EvidenceConflict,
    EvidenceGap,
    EvidenceId,
    EvidenceRelation,
    EvidenceRelationType,
    EvidenceStatus,
)


class CareerEvidenceGraph:
    """Return new graph states while preserving provenance and contradictions."""

    @staticmethod
    def create_empty(bundle_id: str) -> EvidenceBundle:
        return EvidenceBundle(bundle_id=bundle_id)

    @staticmethod
    def add_evidence(bundle: EvidenceBundle, evidence: CareerEvidenceItem) -> EvidenceBundle:
        evidence_id = evidence.reference.evidence_id
        existing = next(
            (item for item in bundle.evidence if item.reference.evidence_id == evidence_id),
            None,
        )
        if existing is not None and existing != evidence:
            raise ValueError(f"Evidence identifier already exists: {evidence_id}")
        if existing is not None:
            return bundle
        return replace(bundle, evidence=bundle.evidence + (evidence,))

    @staticmethod
    def attach_to_subject(
        bundle: EvidenceBundle,
        subject_kind: str,
        subject_id: str,
        evidence: CareerEvidenceItem,
        relation_type: EvidenceRelationType,
    ) -> EvidenceBundle:
        updated = CareerEvidenceGraph.add_evidence(bundle, evidence)
        evidence_id = str(evidence.reference.evidence_id)
        relation = EvidenceRelation(
            relation_id=f"relation:{evidence_id}:{subject_kind}:{subject_id}:{relation_type.value}",
            source_kind="EVIDENCE",
            source_id=evidence_id,
            target_kind=subject_kind,
            target_id=subject_id,
            relation_type=relation_type,
        )
        if relation in updated.relations:
            return updated
        return replace(updated, relations=updated.relations + (relation,))

    @staticmethod
    def attach_passage(
        bundle: EvidenceBundle,
        evidence_id: EvidenceId,
        passage: DocumentPassageReference,
    ) -> EvidenceBundle:
        CareerEvidenceGraph._require_evidence(bundle, evidence_id)
        passages = bundle.passages if passage in bundle.passages else bundle.passages + (passage,)
        relation = EvidenceRelation(
            relation_id=f"relation:{evidence_id}:passage:{passage.passage_id}",
            source_kind="EVIDENCE",
            source_id=str(evidence_id),
            target_kind="DOCUMENT_PASSAGE",
            target_id=passage.passage_id,
            relation_type=EvidenceRelationType.DERIVED_FROM,
        )
        relations = bundle.relations if relation in bundle.relations else bundle.relations + (relation,)
        return replace(bundle, passages=passages, relations=relations)

    @staticmethod
    def mark_removed(bundle: EvidenceBundle, evidence_id: EvidenceId) -> EvidenceBundle:
        """Retain the reference and mark it rejected instead of deleting history."""

        CareerEvidenceGraph._require_evidence(bundle, evidence_id)
        evidence = tuple(
            replace(item, status=EvidenceStatus.REJECTED)
            if item.reference.evidence_id == evidence_id
            else item
            for item in bundle.evidence
        )
        return replace(bundle, evidence=evidence)

    @staticmethod
    def add_claim(bundle: EvidenceBundle, claim: EvidenceClaim) -> EvidenceBundle:
        if any(item.claim_id == claim.claim_id and item != claim for item in bundle.claims):
            raise ValueError(f"Claim identifier already exists: {claim.claim_id}")
        if claim in bundle.claims:
            return bundle
        for evidence_id in claim.evidence_ids:
            CareerEvidenceGraph._require_evidence(bundle, evidence_id)
        return replace(bundle, claims=bundle.claims + (claim,))

    @staticmethod
    def add_conflict(bundle: EvidenceBundle, conflict: EvidenceConflict) -> EvidenceBundle:
        for evidence_id in conflict.evidence_ids:
            CareerEvidenceGraph._require_evidence(bundle, evidence_id)
        if conflict in bundle.conflicts:
            return bundle
        return replace(bundle, conflicts=bundle.conflicts + (conflict,))

    @staticmethod
    def add_gap(bundle: EvidenceBundle, gap: EvidenceGap) -> EvidenceBundle:
        if gap in bundle.gaps:
            return bundle
        relation = EvidenceRelation(
            relation_id=f"relation:{gap.gap_id}:{gap.subject_kind}:{gap.subject_id}",
            source_kind="EVIDENCE_GAP",
            source_id=gap.gap_id,
            target_kind=gap.subject_kind,
            target_id=gap.subject_id,
            relation_type=EvidenceRelationType.MISSING_FOR,
        )
        return replace(bundle, gaps=bundle.gaps + (gap,), relations=bundle.relations + (relation,))

    @staticmethod
    def _require_evidence(bundle: EvidenceBundle, evidence_id: EvidenceId) -> None:
        if not any(item.reference.evidence_id == evidence_id for item in bundle.evidence):
            raise KeyError(f"Unknown evidence identifier: {evidence_id}")
