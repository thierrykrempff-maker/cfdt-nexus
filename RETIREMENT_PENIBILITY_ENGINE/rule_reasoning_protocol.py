"""Declarative protocol for explainable, non-decisional reasoning."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleReasoningProtocolStep:
    """One ordered instruction without embedded legal reasoning."""

    ordinal: int
    step_id: str
    description: str


RULE_REASONING_PROTOCOL = (
    RuleReasoningProtocolStep(1, "identify_question", "Identify the synthetic employee question."),
    RuleReasoningProtocolStep(2, "select_events", "Select relevant career event identifiers."),
    RuleReasoningProtocolStep(3, "select_evidence", "Select relevant evidence references."),
    RuleReasoningProtocolStep(4, "build_document_context", "Reuse the pre-built document knowledge context."),
    RuleReasoningProtocolStep(5, "select_versions", "Select declared document versions applicable to the supplied date."),
    RuleReasoningProtocolStep(6, "select_candidate_rules", "Select synthetic candidate-rule metadata."),
    RuleReasoningProtocolStep(7, "verify_provenance", "Verify that rule and fact provenance is retained."),
    RuleReasoningProtocolStep(8, "separate_rule_and_fact", "Keep collective rules distinct from individual facts."),
    RuleReasoningProtocolStep(9, "evaluate_simple_conditions", "Evaluate only deterministic conditions over supplied values."),
    RuleReasoningProtocolStep(10, "retain_unknowns", "Retain every unknown condition without invention."),
    RuleReasoningProtocolStep(11, "retain_conflicts", "Retain every contradiction without arbitration."),
    RuleReasoningProtocolStep(12, "identify_schemes", "Identify generic schemes that may warrant examination."),
    RuleReasoningProtocolStep(13, "identify_missing_documents", "Identify missing documentary references."),
    RuleReasoningProtocolStep(14, "identify_official_validation", "Identify necessary official validation."),
    RuleReasoningProtocolStep(15, "qualify_outcome", "Qualify the result without confirming an entitlement."),
    RuleReasoningProtocolStep(16, "produce_explanation", "Produce structured factual traces only."),
    RuleReasoningProtocolStep(17, "produce_employee_view", "Produce a clear employee view without technical or sensitive details."),
    RuleReasoningProtocolStep(18, "produce_expert_view", "Produce a sourced expert view without secrets or hidden reasoning."),
)
