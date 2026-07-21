"""Deterministic local engine for cautious synthetic rule evaluation."""

from __future__ import annotations

from dataclasses import replace

from .career_evidence_models import EvidenceSourceType
from .document_knowledge_models import DocumentValidity, KnowledgeContext
from .rule_condition_evaluator import RuleConditionEvaluator
from .rule_reasoning_models import (
    ApplicableScheme,
    ConditionEvaluationState,
    OfficialValidationRequirement,
    ReasoningConflict,
    ReasoningContext,
    ReasoningFact,
    ReasoningFinding,
    ReasoningGap,
    ReasoningOutcome,
    ReasoningReport,
    ReasoningReportView,
    ReasoningRequest,
    ReasoningRule,
    ReasoningTrace,
    ReasoningWarning,
    RuleEvaluation,
)
from .rule_reasoning_report import RuleReasoningReportBuilder


class RetirementRuleReasoningEngine:
    """Evaluate supplied synthetic rules without deciding an entitlement."""

    def __init__(
        self,
        evaluator: RuleConditionEvaluator | None = None,
        report_builder: RuleReasoningReportBuilder | None = None,
    ) -> None:
        self._evaluator = evaluator or RuleConditionEvaluator()
        self._report_builder = report_builder or RuleReasoningReportBuilder()

    def create_reasoning_context(
        self,
        context_id: str,
        request: ReasoningRequest,
        timeline,
        evidence_bundle,
        knowledge_context: KnowledgeContext,
        facts: tuple[ReasoningFact, ...] = (),
    ) -> ReasoningContext:
        return ReasoningContext(
            context_id, request, timeline, evidence_bundle, knowledge_context, facts
        )

    def register_rule(self, context: ReasoningContext, rule: ReasoningRule) -> ReasoningContext:
        existing = next((item for item in context.rules if item.rule_id == rule.rule_id), None)
        if existing is not None and existing != rule:
            raise ValueError(f"Rule identifier already exists: {rule.rule_id}")
        if existing is not None:
            return context
        return replace(context, rules=context.rules + (rule,))

    def evaluate_rule(self, context: ReasoningContext, rule: ReasoningRule) -> RuleEvaluation:
        conditions = tuple(self._evaluator.evaluate(condition, context) for condition in rule.conditions)
        state, reasons = self._rule_state(context, rule, conditions)
        trace = tuple(
            ReasoningTrace(
                step_id=f"evaluate:{rule.rule_id}:{evaluation.condition_id}",
                rule_id=rule.rule_id,
                condition_id=evaluation.condition_id,
                input_used=next(
                    condition.fact_key
                    for condition in rule.conditions
                    if condition.condition_id == evaluation.condition_id
                ),
                status=evaluation.state,
                provenance=evaluation.provenance,
                justification=evaluation.justification,
            )
            for evaluation in conditions
        )
        return RuleEvaluation(rule.rule_id, state, conditions, trace, reasons, rule.provenance)

    def evaluate_rules(self, context: ReasoningContext) -> ReasoningOutcome:
        evaluations = tuple(self.evaluate_rule(context, rule) for rule in context.rules)
        gaps = self.identify_missing_information(evaluations)
        conflicts = self.identify_conflicts(evaluations)
        schemes = self.identify_applicable_schemes(context.rules, evaluations)
        validations = tuple(
            OfficialValidationRequirement(
                f"validation:{rule.rule_id}",
                rule.scheme,
                "COMPETENT_OFFICIAL_AUTHORITY",
                "The analysis is non-decisional and requires official validation.",
            )
            for rule, evaluation in zip(context.rules, evaluations)
            if rule.official_validation_required
            or evaluation.state is ConditionEvaluationState.REQUIRES_OFFICIAL_VALIDATION
        )
        findings = tuple(
            ReasoningFinding(
                f"finding:{evaluation.rule_id}:{condition.condition_id}",
                evaluation.rule_id,
                condition.justification,
                condition.state,
                condition.provenance,
            )
            for evaluation in evaluations
            for condition in evaluation.conditions
        )
        trace = tuple(item for evaluation in evaluations for item in evaluation.trace)
        warnings = (
            ReasoningWarning("non_decisional", "This analysis is not an administrative or legal decision."),
            ReasoningWarning("no_calculation", "No retirement, quarter, pension or C2P calculation was performed."),
        )
        return ReasoningOutcome(
            evaluations, findings, gaps, conflicts, schemes, validations, warnings, trace
        )

    def identify_applicable_schemes(
        self,
        rules: tuple[ReasoningRule, ...],
        evaluations: tuple[RuleEvaluation, ...],
    ) -> tuple[ApplicableScheme, ...]:
        schemes: list[ApplicableScheme] = []
        for rule, evaluation in zip(rules, evaluations):
            if evaluation.state in {
                ConditionEvaluationState.NOT_SATISFIED,
                ConditionEvaluationState.NOT_APPLICABLE,
            }:
                continue
            schemes.append(
                ApplicableScheme(
                    rule.scheme,
                    (rule.rule_id,),
                    evaluation.state,
                    "Synthetic conditions indicate that this scheme may warrant examination.",
                )
            )
        return tuple(schemes)

    def identify_missing_information(
        self, evaluations: tuple[RuleEvaluation, ...]
    ) -> tuple[ReasoningGap, ...]:
        return tuple(
            ReasoningGap(
                f"gap:{evaluation.rule_id}:{condition.condition_id}",
                evaluation.rule_id,
                condition.condition_id,
                condition.justification,
                condition.condition_id
                if condition.state is ConditionEvaluationState.REQUIRES_DOCUMENT
                else None,
            )
            for evaluation in evaluations
            for condition in evaluation.conditions
            if condition.state
            in {
                ConditionEvaluationState.UNKNOWN,
                ConditionEvaluationState.REQUIRES_DOCUMENT,
                ConditionEvaluationState.REQUIRES_OFFICIAL_VALIDATION,
            }
        )

    def identify_conflicts(
        self, evaluations: tuple[RuleEvaluation, ...]
    ) -> tuple[ReasoningConflict, ...]:
        return tuple(
            ReasoningConflict(
                f"conflict:{evaluation.rule_id}:{condition.condition_id}",
                evaluation.rule_id,
                condition.condition_id,
                condition.justification,
                condition.provenance,
            )
            for evaluation in evaluations
            for condition in evaluation.conditions
            if condition.state is ConditionEvaluationState.CONFLICTED
        )

    def generate_reasoning_report(
        self,
        context: ReasoningContext,
        outcome: ReasoningOutcome,
        view: ReasoningReportView,
    ) -> ReasoningReport:
        return self._report_builder.build(context, outcome, view)

    @staticmethod
    def explain_reasoning(outcome: ReasoningOutcome) -> tuple[ReasoningTrace, ...]:
        return outcome.trace

    def _rule_state(self, context, rule, conditions):
        states = {condition.state for condition in conditions}
        if rule.document_version and rule.document_version.validity is DocumentValidity.REPEALED:
            return ConditionEvaluationState.NOT_APPLICABLE, ("The linked documentary version is repealed.",)
        if ConditionEvaluationState.CONFLICTED in states:
            return ConditionEvaluationState.CONFLICTED, ("At least one supplied condition is conflicted.",)
        if ConditionEvaluationState.NOT_SATISFIED in states:
            return ConditionEvaluationState.NOT_SATISFIED, ("At least one simple condition is not satisfied.",)
        if ConditionEvaluationState.REQUIRES_OFFICIAL_VALIDATION in states:
            return ConditionEvaluationState.REQUIRES_OFFICIAL_VALIDATION, ("An official notification is required.",)
        if ConditionEvaluationState.REQUIRES_DOCUMENT in states:
            return ConditionEvaluationState.REQUIRES_DOCUMENT, ("A required document reference is missing.",)
        if ConditionEvaluationState.UNKNOWN in states:
            state = ConditionEvaluationState.PARTIALLY_SATISFIED if ConditionEvaluationState.SATISFIED in states else ConditionEvaluationState.UNKNOWN
            return state, ("Unknown conditions remain visible.",)
        if rule.collective_rule and not self._has_individual_evidence(context):
            return ConditionEvaluationState.PARTIALLY_SATISFIED, ("A collective rule alone does not establish an individual fact.",)
        if self._declaration_only(context):
            return ConditionEvaluationState.REQUIRES_OFFICIAL_VALIDATION, ("An employee declaration alone requires validation.",)
        if rule.official_validation_required:
            return ConditionEvaluationState.REQUIRES_OFFICIAL_VALIDATION, ("Official validation remains mandatory.",)
        return ConditionEvaluationState.SATISFIED, ("All supplied simple conditions are satisfied.",)

    @staticmethod
    def _has_individual_evidence(context: ReasoningContext) -> bool:
        excluded = {
            EvidenceSourceType.INEOS_AGREEMENT,
            EvidenceSourceType.COLLECTIVE_AGREEMENT,
            EvidenceSourceType.EMPLOYEE_DECLARATION,
        }
        return any(
            item.reference.source_type not in excluded
            for item in context.evidence_bundle.evidence
        )

    @staticmethod
    def _declaration_only(context: ReasoningContext) -> bool:
        evidence = context.evidence_bundle.evidence
        return bool(evidence) and all(
            item.reference.source_type is EvidenceSourceType.EMPLOYEE_DECLARATION
            for item in evidence
        )
