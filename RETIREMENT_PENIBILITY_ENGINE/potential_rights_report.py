"""Audience-safe Potential Rights reports with prudent wording."""

from __future__ import annotations

import re

from .potential_rights_models import (
    PotentialRightsAnalysis,
    PotentialRightsContext,
    PotentialRightsReport,
    PotentialRightsReportView,
    PotentialRightsSummary,
)


_FORBIDDEN_MARKERS = (
    "secret",
    "token",
    "password",
    "diagnosis",
    "medical detail",
    "social security number",
    "nir",
)


def _safe(value: str) -> str:
    lowered = value.lower()
    if any(marker in lowered for marker in _FORBIDDEN_MARKERS):
        return "[REDACTED]"
    if re.search(r"(?:^|\s)[a-zA-Z]:[\\/]", value) or value.startswith(("/", "\\\\")):
        return "[REDACTED]"
    return value.replace("Vous avez droit", "Ce dispositif semble devoir être examiné")


class PotentialRightsReportBuilder:
    """Build employee and expert views without legal conclusions."""

    def build(
        self,
        context: PotentialRightsContext,
        analysis: PotentialRightsAnalysis,
        view: PotentialRightsReportView,
    ) -> PotentialRightsReport:
        summary = PotentialRightsSummary(
            analysis.maturity.level,
            tuple(item.category for item in analysis.potential_rights),
            bool(analysis.missing_requirements),
            bool(analysis.official_validations),
            bool(context.reasoning_report.conflicts),
        )
        schemes = tuple(
            item.category.value.replace("_", " ").title()
            for item in analysis.potential_rights
        )
        reasons = tuple(
            _safe(reason.description)
            for item in analysis.potential_rights
            for reason in item.reasons
        )
        missing = tuple(_safe(item.description) for item in analysis.missing_requirements)
        organizations = tuple(
            dict.fromkeys(
                item.authority for item in analysis.official_validations if item.authority
            )
        )
        steps = tuple(_safe(item.action) for item in analysis.recommendations)
        warnings = (
            "Ce rapport identifie des dispositifs à examiner et n’attribue aucun droit.",
            "Le niveau de maturité concerne uniquement la qualité du dossier documentaire.",
            "Une validation officielle reste nécessaire lorsqu’elle est indiquée.",
        )
        if view is PotentialRightsReportView.EMPLOYEE_VIEW:
            return PotentialRightsReport(
                view,
                summary,
                schemes,
                reasons,
                missing,
                organizations,
                steps,
                analysis.maturity,
                warnings,
            )

        reasoning = context.reasoning_report
        evidence = tuple(
            _safe(
                f"{item.reference.source_type.value}: {item.reference.reference} "
                f"[{item.status.value}]"
            )
            for item in context.evidence_bundle.evidence
        )
        return PotentialRightsReport(
            view,
            summary,
            schemes,
            reasons,
            missing,
            organizations,
            steps,
            analysis.maturity,
            warnings,
            rules=tuple(_safe(item) for item in reasoning.examined_rules),
            evidence=evidence,
            document_versions=tuple(_safe(item) for item in reasoning.document_versions),
            conflicts=tuple(_safe(item) for item in reasoning.conflicts),
            detailed_indicators=tuple(
                _safe(
                    f"{item.indicator_type.value}: {item.state.value} — {item.explanation}"
                )
                for item in analysis.maturity.indicators
            ),
            score_justification=tuple(_safe(item) for item in analysis.maturity.justification),
            provenance=tuple(
                dict.fromkeys(
                    _safe(value)
                    for value in (
                        *reasoning.provenance,
                        *(item.reference.provenance for item in context.evidence_bundle.evidence),
                    )
                    if value
                )
            ),
        )
