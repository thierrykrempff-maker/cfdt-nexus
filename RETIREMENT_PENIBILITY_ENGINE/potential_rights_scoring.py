"""Deterministic qualitative scoring of documentary case maturity."""

from .potential_rights_models import (
    CaseMaturity,
    CaseMaturityIndicator,
    CaseMaturityIndicatorState,
    CaseMaturityLevel,
)


class CaseMaturityScorer:
    """Assign a qualitative level without percentage, AI or employee scoring."""

    def score(
        self,
        indicators: tuple[CaseMaturityIndicator, ...],
        has_case_material: bool,
    ) -> CaseMaturity:
        if not has_case_material:
            return CaseMaturity(
                CaseMaturityLevel.UNKNOWN,
                indicators,
                ("No substantive case material is available for maturity assessment.",),
            )
        evidence_indicator = next(
            (item for item in indicators if item.indicator_type.value == "EVIDENCE_AVAILABLE"),
            None,
        )
        if evidence_indicator and evidence_indicator.state is CaseMaturityIndicatorState.MISSING:
            return CaseMaturity(
                CaseMaturityLevel.INSUFFICIENT,
                indicators,
                ("Potential schemes are present but the case contains no supporting evidence reference.",),
            )
        favorable = sum(
            item.state in {CaseMaturityIndicatorState.AVAILABLE, CaseMaturityIndicatorState.COHERENT}
            for item in indicators
        )
        adverse = sum(
            item.state
            in {
                CaseMaturityIndicatorState.MISSING,
                CaseMaturityIndicatorState.CONFLICTED,
                CaseMaturityIndicatorState.REQUIRES_VALIDATION,
            }
            for item in indicators
        )
        if favorable >= 7 and adverse == 0:
            level = CaseMaturityLevel.COMPLETE
        elif favorable >= 6 and adverse <= 1:
            level = CaseMaturityLevel.MOSTLY_COMPLETE
        elif favorable >= 3:
            level = CaseMaturityLevel.PARTIALLY_COMPLETE
        else:
            level = CaseMaturityLevel.INSUFFICIENT
        justification = tuple(
            f"{item.indicator_type.value}: {item.state.value} — {item.explanation}"
            for item in indicators
        )
        return CaseMaturity(level, indicators, justification)
