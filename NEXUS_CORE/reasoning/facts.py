"""Faithful one-to-one conversion of Evidence objects into Facts."""

from __future__ import annotations

from ..evidence import Evidence
from ._identity import stable_reasoning_id
from .models import Fact, FactCollection, FactType


class FactExtractor:
    """Extract facts without inference, normalization or value transformation."""

    def extract(self, evidence: tuple[Evidence, ...]) -> FactCollection:
        by_evidence = {}
        for item in evidence:
            existing = by_evidence.get(item.evidence_id)
            if existing is not None and existing != item:
                raise ValueError("one evidence identifier refers to different objects")
            by_evidence[item.evidence_id] = item

        facts = tuple(
            self._from_evidence(item)
            for item in sorted(by_evidence.values(), key=lambda value: value.evidence_id.value)
        )
        return FactCollection(facts)

    @staticmethod
    def _from_evidence(evidence: Evidence) -> Fact:
        return Fact(
            fact_id=stable_reasoning_id("fact", (evidence.evidence_id.value,)),
            source_evidence=evidence.evidence_id,
            subject_reference=evidence.subject_reference,
            fact_type=FactType(evidence.fact_type),
            value=evidence.value,
            period=evidence.period,
            provenance=evidence.provenance,
            confidence=evidence.confidence,
            quality=evidence.quality,
            validation_status=evidence.validation_status,
        )
