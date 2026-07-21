"""Audience-safe reports for structured rule reasoning outcomes."""

from __future__ import annotations

from dataclasses import replace
import re

from .rule_reasoning_models import (
    ConditionEvaluationState,
    ReasoningContext,
    ReasoningOutcome,
    ReasoningReport,
    ReasoningReportView,
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
    return value


class RuleReasoningReportBuilder:
    """Project an outcome without exposing internal IDs or sensitive values."""

    def build(
        self,
        context: ReasoningContext,
        outcome: ReasoningOutcome,
        view: ReasoningReportView,
    ) -> ReasoningReport:
        schemes = tuple(scheme.scheme.value.replace("_", " ").title() for scheme in outcome.schemes)
        reasons = tuple(
            _safe(reason)
            for evaluation in outcome.evaluations
            for reason in evaluation.reasons
        )
        confirmed = tuple(
            _safe(finding.description)
            for finding in outcome.findings
            if finding.state is ConditionEvaluationState.SATISFIED
        )
        verify = tuple(
            _safe(finding.description)
            for finding in outcome.findings
            if finding.state is not ConditionEvaluationState.SATISFIED
        )
        missing = tuple(_safe(gap.description) for gap in outcome.gaps)
        warnings = tuple(_safe(warning.message) for warning in outcome.warnings) + (
            "This report is not an administrative decision and confirms no entitlement.",
        )
        actions = tuple(
            dict.fromkeys(
                ("Provide the listed missing documentary references.",)
                + (("Request validation from the competent official authority.",) if outcome.official_validations else ())
            )
        )
        if view is ReasoningReportView.EMPLOYEE_VIEW:
            return ReasoningReport(
                view,
                schemes,
                reasons,
                confirmed,
                verify,
                missing,
                actions,
                bool(outcome.official_validations),
                warnings,
            )

        versions = tuple(
            _safe(f"{rule.document_version.label} ({rule.document_version.validity.value})")
            for rule in context.rules
            if rule.document_version is not None
        )
        evidence = tuple(
            _safe(
                f"{item.reference.source_type.value}: {item.reference.reference} "
                f"[{item.status.value}]"
            )
            for item in context.evidence_bundle.evidence
        )
        traces = tuple(
            replace(
                trace,
                input_used=_safe(trace.input_used),
                provenance=_safe(trace.provenance),
                justification=_safe(trace.justification),
            )
            for trace in outcome.trace
        )
        return ReasoningReport(
            view,
            schemes,
            reasons,
            confirmed,
            verify,
            missing,
            actions,
            bool(outcome.official_validations),
            warnings,
            examined_rules=tuple(_safe(rule.label) for rule in context.rules),
            document_versions=versions,
            conditions=tuple(
                _safe(f"{condition.condition_id}: {condition.state.value}")
                for evaluation in outcome.evaluations
                for condition in evaluation.conditions
            ),
            evidence_references=evidence,
            conflicts=tuple(_safe(conflict.description) for conflict in outcome.conflicts),
            provenance=tuple(
                dict.fromkeys(
                    _safe(value)
                    for value in (
                        *(rule.provenance for rule in context.rules),
                        *(finding.provenance for finding in outcome.findings),
                    )
                    if value
                )
            ),
            trace=traces,
        )
