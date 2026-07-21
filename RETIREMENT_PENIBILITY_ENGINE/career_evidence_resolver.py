"""Prudent evidence-state resolution without legal or retirement decisions."""

from __future__ import annotations

from .career_evidence_models import (
    CareerEvidenceItem,
    EvidenceAuthorityLevel,
    EvidenceBundle,
    EvidenceClaimType,
    EvidenceConflict,
    EvidenceResolution,
    EvidenceResolutionState,
    EvidenceSourceType,
    EvidenceStatus,
)


class CareerEvidenceResolver:
    """Classify retained evidence while keeping minority and replaced sources."""

    def resolve(self, bundle: EvidenceBundle, subject_id: str | None = None) -> EvidenceResolution:
        evidence = self._evidence_for_subject(bundle, subject_id)
        conflicts = tuple(bundle.conflicts) + self._detect_claim_conflicts(bundle, subject_id)
        ordered = tuple(sorted(evidence, key=self._ordering_key))
        reasons: list[str] = []

        if conflicts:
            state = EvidenceResolutionState.CONFLICTED
            reasons.append("Incompatible claims or evidence remain unresolved.")
        elif not evidence:
            state = EvidenceResolutionState.INSUFFICIENT_EVIDENCE
            reasons.append("No documentary reference supports the subject.")
        elif self._declaration_only(evidence):
            state = EvidenceResolutionState.REQUIRES_OFFICIAL_VALIDATION
            reasons.append("An employee declaration requires complementary validation.")
        elif self._has_verified_official(evidence):
            state = EvidenceResolutionState.CONFIRMED
            reasons.append("A verified official notification records an administrative finding.")
        elif any(item.status in {EvidenceStatus.PROVIDED, EvidenceStatus.VERIFIED} for item in evidence):
            state = EvidenceResolutionState.PARTIALLY_CONFIRMED
            reasons.append("Available references corroborate the subject without final legal determination.")
        else:
            state = EvidenceResolutionState.UNCONFIRMED
            reasons.append("Available references do not confirm the subject.")

        if any(item.status is EvidenceStatus.SUPERSEDED for item in evidence):
            reasons.append("Superseded evidence is retained for traceability.")
        return EvidenceResolution(state, ordered, conflicts, tuple(reasons))

    @staticmethod
    def classify_item(item: CareerEvidenceItem) -> str:
        """Distinguish collective rule, declaration, official and individual evidence."""

        source_type = item.reference.source_type
        if source_type in {EvidenceSourceType.INEOS_AGREEMENT, EvidenceSourceType.COLLECTIVE_AGREEMENT}:
            return "COLLECTIVE_RULE"
        if source_type is EvidenceSourceType.EMPLOYEE_DECLARATION:
            return "DECLARATION"
        if item.authority_level is EvidenceAuthorityLevel.AUTHORITATIVE_OFFICIAL:
            return "OFFICIAL_DOCUMENT"
        return "INDIVIDUAL_EVIDENCE"

    @staticmethod
    def newer_reference(left: CareerEvidenceItem, right: CareerEvidenceItem) -> CareerEvidenceItem | None:
        """Identify the more recent dated reference without declaring it more accurate."""

        if left.reference.version_date == right.reference.version_date:
            return None
        if left.reference.version_date is None:
            return right
        if right.reference.version_date is None:
            return left
        return max((left, right), key=lambda item: item.reference.version_date or "")

    @staticmethod
    def _ordering_key(item: CareerEvidenceItem) -> tuple[str, str]:
        return (item.reference.version_date or "", str(item.reference.evidence_id))

    @staticmethod
    def _declaration_only(evidence: tuple[CareerEvidenceItem, ...]) -> bool:
        return all(item.reference.source_type is EvidenceSourceType.EMPLOYEE_DECLARATION for item in evidence)

    @staticmethod
    def _has_verified_official(evidence: tuple[CareerEvidenceItem, ...]) -> bool:
        return any(
            item.authority_level is EvidenceAuthorityLevel.AUTHORITATIVE_OFFICIAL
            and item.status is EvidenceStatus.VERIFIED
            for item in evidence
        )

    @staticmethod
    def _evidence_for_subject(
        bundle: EvidenceBundle, subject_id: str | None
    ) -> tuple[CareerEvidenceItem, ...]:
        if subject_id is None:
            return bundle.evidence
        evidence_ids = {
            relation.source_id
            for relation in bundle.relations
            if relation.source_kind == "EVIDENCE" and relation.target_id == subject_id
        }
        return tuple(item for item in bundle.evidence if str(item.reference.evidence_id) in evidence_ids)

    @staticmethod
    def _detect_claim_conflicts(
        bundle: EvidenceBundle, subject_id: str | None
    ) -> tuple[EvidenceConflict, ...]:
        conflicts: list[EvidenceConflict] = []
        claims = tuple(claim for claim in bundle.claims if subject_id is None or claim.subject_id == subject_id)
        for index, left in enumerate(claims):
            for right in claims[index + 1 :]:
                if (
                    left.subject_id == right.subject_id
                    and left.claim_type is right.claim_type
                    and left.statement != right.statement
                ):
                    conflicts.append(
                        EvidenceConflict(
                            conflict_id=f"detected:{left.claim_id}:{right.claim_id}",
                            subject_id=left.subject_id,
                            evidence_ids=tuple(dict.fromkeys(left.evidence_ids + right.evidence_ids)),
                            claim_ids=(left.claim_id, right.claim_id),
                            reason="Incompatible sourced claims.",
                        )
                    )
        return tuple(conflicts)
