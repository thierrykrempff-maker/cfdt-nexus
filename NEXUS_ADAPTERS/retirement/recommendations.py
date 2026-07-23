"""Explicit projection of existing Retirement actions; no advice is invented."""

from __future__ import annotations

from automation.contracts import ExpertReport
from RETIREMENT_PENIBILITY_ENGINE.retirement_models import RetirementReport
from NEXUS_CORE import (
    Recommendation, RecommendationId, RecommendationPriority, RecommendationStatus,
    RecommendationType,
)

from ._identity import stable_retirement_id
from .metadata import RetirementMetadataMapper


class RetirementRecommendationMapper:
    def __init__(self, metadata: RetirementMetadataMapper | None = None) -> None:
        self._metadata = metadata or RetirementMetadataMapper()

    def map(self, report: RetirementReport,
            expert_report: ExpertReport | None = None) -> tuple[Recommendation, ...]:
        recommendations = [
            Recommendation(
                RecommendationId(stable_retirement_id(
                    "recommendation", report.report_id, str(index)
                )),
                RecommendationType.VERIFY_INFORMATION,
                RecommendationPriority.NORMAL,
                RecommendationStatus.PROPOSED,
                "RETIREMENT_RECOMMENDATION_REPORTED",
                metadata=(self._metadata.metadata("retirement_action", value),),
            )
            for index, value in enumerate(report.recommended_actions)
        ]
        if expert_report is not None:
            for category, values, item_type, code in (
                ("expert_recommendation", expert_report.recommendations,
                 RecommendationType.VERIFY_INFORMATION, "RETIREMENT_EXPERT_RECOMMENDATION"),
                ("expert_action", expert_report.proposed_actions,
                 RecommendationType.MANUAL_REVIEW, "RETIREMENT_EXPERT_ACTION"),
            ):
                recommendations.extend(
                    Recommendation(
                        RecommendationId(stable_retirement_id(
                            "recommendation", expert_report.report_id, category, str(index)
                        )),
                        item_type, RecommendationPriority.NORMAL,
                        RecommendationStatus.PROPOSED, code,
                        metadata=(self._metadata.metadata("retirement_action", value),),
                    )
                    for index, value in enumerate(values)
                )
        return tuple(recommendations)
