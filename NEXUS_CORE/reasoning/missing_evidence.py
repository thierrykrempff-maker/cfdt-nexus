"""Explicit requirement checks that never invent missing evidence."""

from __future__ import annotations

from ..entities import EntityReference
from ..periods import Period
from ._identity import stable_reasoning_id
from .models import FactCollection, FactType, MissingEvidence, MissingEvidenceReason


class MissingEvidenceEngine:
    def identify(
        self,
        facts: FactCollection,
        subject: EntityReference,
        required_fact_types: tuple[FactType, ...],
        required_period: Period | None = None,
    ) -> tuple[MissingEvidence, ...]:
        missing = []
        for fact_type in sorted(set(required_fact_types), key=lambda item: item.code):
            matching = tuple(
                fact
                for fact in facts.facts
                if fact.subject_reference == subject and fact.fact_type == fact_type
            )
            reason = None
            if not matching:
                reason = MissingEvidenceReason.REQUIRED_FACT_ABSENT
            elif required_period is not None and not any(
                fact.period is not None and fact.period.contains(required_period)
                for fact in matching
            ):
                reason = MissingEvidenceReason.REQUIRED_PERIOD_NOT_COVERED
            if reason is not None:
                missing.append(
                    MissingEvidence(
                        missing_id=stable_reasoning_id(
                            "missing-evidence",
                            (
                                subject.entity_id.value,
                                fact_type.code,
                                reason.value,
                            ),
                        ),
                        subject_reference=subject,
                        expected_fact_type=fact_type,
                        reason=reason,
                        required_period=required_period,
                    )
                )
        return tuple(missing)
