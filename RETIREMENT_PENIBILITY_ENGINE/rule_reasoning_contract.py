"""Public contracts for the architecture-only retirement rule reasoning LOT."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .rule_reasoning_engine import RetirementRuleReasoningEngine
from .rule_reasoning_models import (
    ApplicableScheme,
    ReasoningConflict,
    ReasoningContext,
    ReasoningGap,
    ReasoningOutcome,
    ReasoningReport,
    ReasoningReportView,
    ReasoningRule,
    ReasoningTrace,
    RuleEvaluation,
)


@dataclass(frozen=True)
class RuleReasoningSafetyContract:
    """Safety declaration prohibiting calculation, decisions and I/O."""

    status: str = "ARCHITECTURE_ONLY"
    enabled: bool = False
    network_allowed: bool = False
    document_access_allowed: bool = False
    pdf_allowed: bool = False
    artificial_intelligence_allowed: bool = False
    legal_decision_allowed: bool = False
    administrative_validation_allowed: bool = False
    retirement_calculation_allowed: bool = False
    quarters_calculation_allowed: bool = False
    c2p_calculation_allowed: bool = False
    pension_amount_calculation_allowed: bool = False


RULE_REASONING_SAFETY_CONTRACT = RuleReasoningSafetyContract()


class RetirementRuleReasoningPort(Protocol):
    """Stable public operations implemented by RetirementRuleReasoningEngine."""

    def create_reasoning_context(self, *args, **kwargs) -> ReasoningContext: ...

    def register_rule(self, context: ReasoningContext, rule: ReasoningRule) -> ReasoningContext: ...

    def evaluate_rule(self, context: ReasoningContext, rule: ReasoningRule) -> RuleEvaluation: ...

    def evaluate_rules(self, context: ReasoningContext) -> ReasoningOutcome: ...

    def identify_applicable_schemes(self, rules, evaluations) -> tuple[ApplicableScheme, ...]: ...

    def identify_missing_information(self, evaluations) -> tuple[ReasoningGap, ...]: ...

    def identify_conflicts(self, evaluations) -> tuple[ReasoningConflict, ...]: ...

    def generate_reasoning_report(
        self, context: ReasoningContext, outcome: ReasoningOutcome, view: ReasoningReportView
    ) -> ReasoningReport: ...

    def explain_reasoning(self, outcome: ReasoningOutcome) -> tuple[ReasoningTrace, ...]: ...


__all__ = (
    "RetirementRuleReasoningEngine",
    "RetirementRuleReasoningPort",
    "RULE_REASONING_SAFETY_CONTRACT",
)
