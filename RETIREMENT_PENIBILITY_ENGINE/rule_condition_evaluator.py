"""Prudent evaluator for simple, explicitly supplied condition values."""

from __future__ import annotations

from datetime import date

from .rule_reasoning_models import (
    ConditionEvaluation,
    ConditionEvaluationState,
    ConditionOperator,
    ReasoningContext,
    ReasoningFact,
    ReasoningFactStatus,
    RuleCondition,
    RuleConditionType,
)


class RuleConditionEvaluator:
    """Evaluate comparisons without deriving durations, points or legal facts."""

    def evaluate(self, condition: RuleCondition, context: ReasoningContext) -> ConditionEvaluation:
        if condition.operator is ConditionOperator.EVENT_PRESENT:
            present = any(
                event.event_type.value == condition.expected_value
                for event in context.timeline.events
            )
            return self._result(
                condition,
                ConditionEvaluationState.SATISFIED if present else ConditionEvaluationState.NOT_SATISFIED,
                present,
                condition.provenance,
                "Presence of the declared career event was checked.",
            )

        fact = next((item for item in context.facts if item.fact_key == condition.fact_key), None)
        if fact is None or fact.status is ReasoningFactStatus.UNKNOWN:
            return self._missing(condition)
        if fact.status is ReasoningFactStatus.CONFLICTED:
            return self._result(
                condition,
                ConditionEvaluationState.CONFLICTED,
                fact.value,
                fact.provenance,
                "The supplied fact is explicitly conflicted.",
            )
        return self._evaluate_known(condition, fact)

    def _missing(self, condition: RuleCondition) -> ConditionEvaluation:
        if condition.condition_type is RuleConditionType.DOCUMENT_REQUIRED:
            state = ConditionEvaluationState.REQUIRES_DOCUMENT
            reason = "The required document reference is missing."
        elif condition.condition_type is RuleConditionType.OFFICIAL_NOTIFICATION_REQUIRED:
            state = ConditionEvaluationState.REQUIRES_OFFICIAL_VALIDATION
            reason = "An official notification is required."
        else:
            state = ConditionEvaluationState.UNKNOWN
            reason = "No supplied value is available; no value was inferred."
        return self._result(condition, state, None, condition.provenance, reason)

    def _evaluate_known(
        self, condition: RuleCondition, fact: ReasoningFact
    ) -> ConditionEvaluation:
        observed = fact.value
        expected = condition.expected_value
        try:
            satisfied = self._compare(condition.operator, observed, expected)
        except (TypeError, ValueError):
            return self._result(
                condition,
                ConditionEvaluationState.UNKNOWN,
                observed,
                fact.provenance,
                "The supplied values are not deterministically comparable.",
            )
        return self._result(
            condition,
            ConditionEvaluationState.SATISFIED if satisfied else ConditionEvaluationState.NOT_SATISFIED,
            observed,
            fact.provenance,
            "The declared value was compared using the requested simple operator.",
        )

    @staticmethod
    def _compare(operator: ConditionOperator, observed, expected) -> bool:
        if operator is ConditionOperator.EQUALS:
            return observed == expected
        if operator is ConditionOperator.NOT_EQUALS:
            return observed != expected
        if operator is ConditionOperator.GREATER_THAN:
            return observed > expected
        if operator is ConditionOperator.GREATER_OR_EQUAL:
            return observed >= expected
        if operator is ConditionOperator.LESS_THAN:
            return observed < expected
        if operator is ConditionOperator.LESS_OR_EQUAL:
            return observed <= expected
        if operator is ConditionOperator.PRESENT:
            return observed not in (None, "", (), False)
        if operator is ConditionOperator.ABSENT:
            return observed in (None, "", (), False)
        if operator is ConditionOperator.STATUS_KNOWN:
            return observed not in (None, "", "UNKNOWN")
        if operator is ConditionOperator.IN_PERIOD:
            if not isinstance(observed, str) or not isinstance(expected, tuple) or len(expected) != 2:
                raise TypeError("IN_PERIOD expects one ISO date and a two-date tuple")
            target = date.fromisoformat(observed)
            start = date.fromisoformat(expected[0]) if expected[0] else date.min
            end = date.fromisoformat(expected[1]) if expected[1] else date.max
            return start <= target <= end
        raise ValueError(f"Unsupported operator: {operator}")

    @staticmethod
    def _result(
        condition: RuleCondition,
        state: ConditionEvaluationState,
        observed,
        provenance: str,
        justification: str,
    ) -> ConditionEvaluation:
        return ConditionEvaluation(
            condition.condition_id,
            state,
            observed,
            provenance,
            justification,
        )
