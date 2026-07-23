"""Decision mapping controlled only by the explicitly declared translation role."""

from __future__ import annotations

from NEXUS_CORE import (
    Finding, FindingId, FindingSeverity, FindingStatus, FindingType,
    Recommendation, RecommendationId, RecommendationPriority, RecommendationStatus,
    RecommendationType,
)

from ._identity import stable_cse_id
from .metadata import CSEMetadataMapper
from .models import CSEDecisionRole, CSEDecisionSnapshot


class CSEDecisionMapper:
    def __init__(self, metadata: CSEMetadataMapper | None = None) -> None:
        self._metadata = metadata or CSEMetadataMapper()

    def map(self, decision: CSEDecisionSnapshot) -> tuple[
        tuple[Finding, ...], tuple[Recommendation, ...]
    ]:
        finding = Finding(
            FindingId(stable_cse_id("finding", "decision", decision.decision_id)),
            FindingType.OBSERVATION,
            FindingSeverity.INFO,
            FindingStatus.OPEN,
            "CSE_DECISION_RECORDED",
            metadata=(
                self._metadata.sensitive("decision_code", decision.decision_code),
                self._metadata.sensitive("decision_description", decision.description),
            ),
        )
        recommendation = Recommendation(
            RecommendationId(stable_cse_id("recommendation", decision.decision_id)),
            RecommendationType.MANUAL_REVIEW,
            RecommendationPriority.NORMAL,
            RecommendationStatus.PROPOSED,
            "CSE_DECISION_ACTION_REPORTED",
            metadata=(
                self._metadata.sensitive("decision_code", decision.decision_code),
                self._metadata.sensitive("decision_description", decision.description),
            ),
        )
        findings = (finding,) if decision.role in {
            CSEDecisionRole.FINDING, CSEDecisionRole.FINDING_AND_RECOMMENDATION
        } else ()
        recommendations = (recommendation,) if decision.role in {
            CSEDecisionRole.RECOMMENDATION, CSEDecisionRole.FINDING_AND_RECOMMENDATION
        } else ()
        return findings, recommendations
