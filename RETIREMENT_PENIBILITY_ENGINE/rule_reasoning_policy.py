"""Prudential policies for architecture-only rule reasoning."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleReasoningPolicyRule:
    """One immutable reasoning safeguard."""

    rule_id: str
    description: str


RULE_REASONING_POLICY = (
    RuleReasoningPolicyRule("collective_rule_not_individual_confirmation", "A collective rule alone never confirms an individual situation."),
    RuleReasoningPolicyRule("valid_document_version_required", "An applicable rule must retain a valid documentary version."),
    RuleReasoningPolicyRule("unknown_remains_unknown", "An unknown condition remains UNKNOWN."),
    RuleReasoningPolicyRule("conflict_remains_visible", "A contradictory condition remains CONFLICTED."),
    RuleReasoningPolicyRule("missing_evidence_not_disproof", "Missing evidence does not prove absence of an entitlement."),
    RuleReasoningPolicyRule("partial_not_confirmed", "A partial result is never presented as confirmed."),
    RuleReasoningPolicyRule("official_notification_scope", "An official notification may confirm only an administrative finding already recognized."),
    RuleReasoningPolicyRule("employee_declaration_is_declarative", "Employee declarations remain explicitly declarative."),
    RuleReasoningPolicyRule("aggregate_not_individual", "Aggregated social-report data never confirms an individual situation."),
    RuleReasoningPolicyRule("medical_details_hidden", "Detailed medical information never appears in reports."),
    RuleReasoningPolicyRule("conclusion_explainable", "Every conclusion is supported by structured explainability."),
    RuleReasoningPolicyRule("rule_provenance_required", "Every rule retains provenance."),
    RuleReasoningPolicyRule("uncertainty_visible", "Every uncertainty remains visible."),
    RuleReasoningPolicyRule("administrative_validation_explicit", "Required administrative validation is explicitly reported."),
)
