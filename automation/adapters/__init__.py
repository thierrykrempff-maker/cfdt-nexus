"""Retrocompatible adapters between legacy Nexus payloads and common contracts."""

from .payroll import (
    ADAPTER_VERSION,
    expert_report_to_legacy_payroll,
    expert_report_to_legacy_payroll_result,
    expert_request_to_legacy_payroll,
    expert_request_to_legacy_payroll_request,
    expert_request_to_payroll_question,
    legacy_confidence_to_confidence_assessment,
    legacy_evidence_to_source_evidence,
    legacy_missing_information_to_contract,
    legacy_payroll_report_to_expert_report,
    legacy_payroll_request_to_expert_request,
    legacy_payroll_result_to_expert_report,
    legacy_risk_to_risk_assessment,
    legacy_source_to_knowledge_source,
    legacy_payroll_source_to_contracts,
    payroll_question_to_expert_request,
)

__all__ = (
    "ADAPTER_VERSION",
    "expert_report_to_legacy_payroll",
    "expert_report_to_legacy_payroll_result",
    "expert_request_to_legacy_payroll",
    "expert_request_to_legacy_payroll_request",
    "expert_request_to_payroll_question",
    "legacy_confidence_to_confidence_assessment",
    "legacy_evidence_to_source_evidence",
    "legacy_missing_information_to_contract",
    "legacy_payroll_report_to_expert_report",
    "legacy_payroll_request_to_expert_request",
    "legacy_payroll_result_to_expert_report",
    "legacy_risk_to_risk_assessment",
    "legacy_source_to_knowledge_source",
    "legacy_payroll_source_to_contracts",
    "payroll_question_to_expert_request",
)
