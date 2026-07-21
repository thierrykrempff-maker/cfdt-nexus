"""Public contract for the architecture-only Potential Rights Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .potential_rights_models import (
    CaseMaturity,
    MissingRequirement,
    OfficialValidation,
    PotentialRight,
    PotentialRightRecommendation,
    PotentialRightsAnalysis,
    PotentialRightsContext,
    PotentialRightsReport,
    PotentialRightsReportView,
)


@dataclass(frozen=True)
class PotentialRightsSafetyContract:
    """Safety constraints prohibiting attribution, calculation and I/O."""

    status: str = "ARCHITECTURE_ONLY"
    enabled: bool = False
    entitlement_attribution_allowed: bool = False
    legal_decision_allowed: bool = False
    network_allowed: bool = False
    document_access_allowed: bool = False
    retirement_calculation_allowed: bool = False
    c2p_calculation_allowed: bool = False
    pension_amount_calculation_allowed: bool = False
    percentage_scoring_allowed: bool = False
    artificial_intelligence_allowed: bool = False


POTENTIAL_RIGHTS_SAFETY_CONTRACT = PotentialRightsSafetyContract()


class PotentialRightsPort(Protocol):
    """Stable public methods implemented by PotentialRightsEngine."""

    def create_context(self, *args, **kwargs) -> PotentialRightsContext: ...

    def identify_potential_rights(
        self, context: PotentialRightsContext
    ) -> tuple[PotentialRight, ...]: ...

    def calculate_case_maturity(self, context: PotentialRightsContext) -> CaseMaturity: ...

    def identify_missing_requirements(
        self, context: PotentialRightsContext
    ) -> tuple[MissingRequirement, ...]: ...

    def identify_official_validations(
        self, context: PotentialRightsContext
    ) -> tuple[OfficialValidation, ...]: ...

    def generate_recommendations(
        self,
        missing: tuple[MissingRequirement, ...],
        validations: tuple[OfficialValidation, ...],
    ) -> tuple[PotentialRightRecommendation, ...]: ...

    def analyze(self, context: PotentialRightsContext) -> PotentialRightsAnalysis: ...

    def generate_report(
        self,
        context: PotentialRightsContext,
        analysis: PotentialRightsAnalysis,
        view: PotentialRightsReportView,
    ) -> PotentialRightsReport: ...


__all__ = (
    "PotentialRightsPort",
    "POTENTIAL_RIGHTS_SAFETY_CONTRACT",
)
