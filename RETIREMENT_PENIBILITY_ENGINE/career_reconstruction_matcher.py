"""Deterministic qualitative matcher for structured reconstruction records."""

from __future__ import annotations

from datetime import date, timedelta

from .career_reconstruction_models import (
    DatePrecision,
    ReconstructionConfidence,
    ReconstructionDate,
    ReconstructionMatch,
    ReconstructionMatchType,
    ReconstructionRecord,
)


_COMPARABLE = (
    "employer", "start_date", "end_date", "position", "classification",
    "coefficient", "schedule", "night_work", "five_shift", "exposure_type",
)


class CareerReconstructionMatcher:
    """Compare explicit values without inference, weighting or AI."""

    def match(self, left: ReconstructionRecord, right: ReconstructionRecord) -> ReconstructionMatch:
        left_values, right_values = dict(left.values), dict(right.values)
        matching: list[str] = []
        divergent: list[str] = []
        unknown: list[str] = []
        for key in _COMPARABLE:
            left_value, right_value = left_values.get(key), right_values.get(key)
            if self._unknown(left_value) or self._unknown(right_value):
                unknown.append(key)
            elif left_value == right_value:
                matching.append(key)
            else:
                divergent.append(key)
        if self._same_source_reference(left, right):
            matching.append("source_reference")
        overlap, adjacent = self._period_relation(left_values, right_values)
        if overlap:
            matching.append("overlapping_period")
        if adjacent:
            matching.append("adjacent_period")
        match_type = self._match_type(matching, divergent, left, right)
        confidence = (
            ReconstructionConfidence.HIGH if len(matching) >= 4 and not divergent
            else ReconstructionConfidence.MEDIUM if len(matching) >= 2
            else ReconstructionConfidence.LOW if matching or divergent
            else ReconstructionConfidence.UNKNOWN
        )
        return ReconstructionMatch(
            f"match:{left.record_id}:{right.record_id}",
            (left.record_id, right.record_id),
            tuple(matching),
            tuple(divergent),
            tuple(unknown),
            match_type,
            confidence,
            "Compared explicit structured values; unknown and divergent criteria were retained.",
        )

    @staticmethod
    def _unknown(value):
        return value is None or (
            isinstance(value, ReconstructionDate)
            and value.precision is DatePrecision.UNKNOWN
        )

    @staticmethod
    def _same_source_reference(left, right):
        return bool(left.provenance and right.provenance) and any(
            a.internal_document_id == b.internal_document_id
            for a in left.provenance
            for b in right.provenance
        )

    @staticmethod
    def _period_relation(left, right):
        def exact(value):
            if isinstance(value, ReconstructionDate):
                if value.precision is not DatePrecision.EXACT or not value.value:
                    return None
                value = value.value
            if not isinstance(value, str):
                return None
            try:
                return date.fromisoformat(value)
            except ValueError:
                return None
        ls, le = exact(left.get("start_date")), exact(left.get("end_date"))
        rs, re = exact(right.get("start_date")), exact(right.get("end_date"))
        if None in (ls, le, rs, re):
            return False, False
        return ls <= re and rs <= le, le + timedelta(days=1) == rs or re + timedelta(days=1) == ls

    @staticmethod
    def _match_type(matching, divergent, left, right):
        if divergent:
            return ReconstructionMatchType.CONTRADICTORY_SOURCE
        if set(dict(left.values).items()) == set(dict(right.values).items()):
            return ReconstructionMatchType.POSSIBLE_DUPLICATE
        if "start_date" in matching and "end_date" in matching:
            return ReconstructionMatchType.SAME_PERIOD
        if "overlapping_period" in matching:
            return ReconstructionMatchType.OVERLAPPING_PERIOD
        if "adjacent_period" in matching:
            return ReconstructionMatchType.ADJACENT_PERIOD
        for criterion, match_type in (
            ("employer", ReconstructionMatchType.SAME_EMPLOYER),
            ("position", ReconstructionMatchType.SAME_POSITION),
            ("classification", ReconstructionMatchType.SAME_CLASSIFICATION),
            ("schedule", ReconstructionMatchType.SAME_SCHEDULE),
            ("source_reference", ReconstructionMatchType.SAME_SOURCE_REFERENCE),
        ):
            if criterion in matching:
                return match_type
        if left.provenance != right.provenance and matching:
            return ReconstructionMatchType.CORROBORATING_SOURCE
        return ReconstructionMatchType.NO_MATCH
