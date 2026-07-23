"""Explicit mapping of payroll recommendations without adding advice."""

from __future__ import annotations

from automation.contracts import ExpertReport
from NEXUS_CORE import (
    Recommendation,
    RecommendationId,
    RecommendationPriority,
    RecommendationStatus,
    RecommendationType,
)

from ._identity import stable_payroll_id
from .metadata import PayrollMetadataMapper


class PayrollRecommendationMapper:
    def __init__(self, metadata: PayrollMetadataMapper | None = None) -> None:
        self._metadata = metadata or PayrollMetadataMapper()

    def map(self, report: ExpertReport) -> tuple[Recommendation, ...]:
        recommendations = []
        for index, value in enumerate(report.recommendations):
            recommendations.append(
                self._recommendation(
                    report,
                    "recommendation",
                    index,
                    value,
                    RecommendationType.VERIFY_INFORMATION,
                    "PAYROLL_RECOMMENDATION_REPORTED",
                )
            )
        for index, value in enumerate(report.proposed_actions):
            recommendations.append(
                self._recommendation(
                    report,
                    "proposed_action",
                    index,
                    value,
                    RecommendationType.MANUAL_REVIEW,
                    "PAYROLL_ACTION_REPORTED",
                )
            )
        return tuple(recommendations)

    def _recommendation(self, report, category, index, value, item_type, code):
        return Recommendation(
            RecommendationId(
                stable_payroll_id("recommendation", report.report_id, category, str(index))
            ),
            item_type,
            RecommendationPriority.NORMAL,
            RecommendationStatus.PROPOSED,
            code,
            metadata=(self._metadata.sensitive_text("payroll_text", value),),
        )
