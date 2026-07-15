#!/usr/bin/env python
"""Deterministic, non-calculating employee-case pipeline (LOT 5A)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from automation.payroll import payroll_data_privacy_validator as privacy_validator

from .employee_case import (
    AvailabilityStatus,
    CaseStatus,
    ConfidentialityLevel,
    ControlStatus,
    DocumentType,
    EmployeeCase,
    EmployeeDocument,
    ExpertAnalysis,
    ExpertStatus,
    PipelineHistoryEntry,
    StepStatus,
)


PIPELINE_STEPS: tuple[str, ...] = (
    "validate_case",
    "validate_documents",
    "check_confidentiality",
    "classify_documents",
    "identify_themes",
    "determine_required_documents",
    "assess_document_completeness",
    "prepare_expert_contexts",
    "collect_expert_analyses",
    "aggregate_results",
    "detect_contradictions",
    "produce_diagnostic",
)

REQUIRED = "required"
RECOMMENDED = "recommended"
OPTIONAL = "optional"
NOT_RELEVANT = "not_relevant"

DOCUMENT_REQUIREMENTS: Mapping[str, Mapping[DocumentType, str]] = {
    "overtime": {
        DocumentType.PAYSLIP: REQUIRED,
        DocumentType.TIME_STATEMENT: REQUIRED,
        DocumentType.PLANNING: REQUIRED,
        DocumentType.COMPANY_AGREEMENT: REQUIRED,
        DocumentType.MANAGER_DECISION: OPTIONAL,
        DocumentType.IJSS_STATEMENT: NOT_RELEVANT,
    },
    "on_call": {
        DocumentType.PAYSLIP: REQUIRED,
        DocumentType.ON_CALL_STATEMENT: REQUIRED,
        DocumentType.INTERVENTION_STATEMENT: RECOMMENDED,
        DocumentType.PLANNING: REQUIRED,
        DocumentType.COMPANY_AGREEMENT: REQUIRED,
    },
    "sickness_maintenance": {
        DocumentType.PAYSLIP: REQUIRED,
        DocumentType.ANONYMIZED_ABSENCE_PROOF: REQUIRED,
        DocumentType.IJSS_STATEMENT: RECOMMENDED,
        DocumentType.APPLICABLE_RULE: REQUIRED,
    },
    "paid_leave": {
        DocumentType.PAYSLIP: REQUIRED,
        DocumentType.LEAVE_COUNTER: REQUIRED,
        DocumentType.LEAVE_REQUEST: REQUIRED,
        DocumentType.ACQUISITION_PERIOD: RECOMMENDED,
        DocumentType.APPLICABLE_RULE: REQUIRED,
        DocumentType.HR_CORRESPONDENCE: OPTIONAL,
    },
    "classification": {
        DocumentType.EMPLOYMENT_CONTRACT: REQUIRED,
        DocumentType.CONTRACT_AMENDMENT: RECOMMENDED,
        DocumentType.JOB_DESCRIPTION: REQUIRED,
        DocumentType.FUNCTIONS_STATEMENT: REQUIRED,
        DocumentType.COLLECTIVE_AGREEMENT: REQUIRED,
        DocumentType.COMPANY_AGREEMENT: RECOMMENDED,
    },
    "holidays_and_rest": {
        DocumentType.PLANNING: REQUIRED,
        DocumentType.TIME_STATEMENT: REQUIRED,
        DocumentType.PAYSLIP: REQUIRED,
        DocumentType.LEAVE_COUNTER: RECOMMENDED,
        DocumentType.COMPANY_AGREEMENT: REQUIRED,
    },
}

CONFIDENCE_ORDER = {"UNKNOWN": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "VERY_HIGH": 4}


@dataclass(frozen=True)
class StepResult:
    step: str
    status: StepStatus
    message: str
    data: Any = None


class PipelineBlocked(RuntimeError):
    """Raised internally when a blocking step must stop the pipeline."""


def _enum(enum_type: type[Any], value: Any) -> Any:
    return enum_type(str(value))


def document_from_dict(data: Mapping[str, Any]) -> EmployeeDocument:
    return EmployeeDocument(
        document_id=str(data.get("document_id", "")),
        document_type=_enum(DocumentType, data.get("document_type")),
        title=str(data.get("title", "")),
        period=str(data["period"]) if data.get("period") is not None else None,
        declared_source=str(data.get("declared_source", "")),
        file_format=str(data.get("file_format", "")),
        availability=_enum(AvailabilityStatus, data.get("availability", "present")),
        confidentiality=_enum(ConfidentialityLevel, data.get("confidentiality", "internal")),
        control_status=_enum(ControlStatus, data.get("control_status", "not_checked")),
        synthetic_summary=str(data["synthetic_summary"]) if data.get("synthetic_summary") is not None else None,
        metadata=dict(data.get("metadata") or {}),
        synthetic_only=data.get("synthetic_only") is True,
    )


def case_from_dict(data: Mapping[str, Any]) -> EmployeeCase:
    return EmployeeCase(
        case_id=str(data.get("case_id", "")),
        title=str(data.get("title", "")),
        main_question=str(data.get("main_question", "")),
        description=str(data.get("description", "")),
        period=str(data.get("period", "")),
        population=str(data.get("population", "")),
        detected_themes=[str(item) for item in data.get("detected_themes", [])],
        urgent=bool(data.get("urgent", False)),
        status=_enum(CaseStatus, data.get("status", "draft")),
        documents=[document_from_dict(item) for item in data.get("documents", []) if isinstance(item, dict)],
        missing_documents=[str(item) for item in data.get("missing_documents", [])],
        employee_information=dict(data.get("employee_information") or {}),
        assumptions=[str(item) for item in data.get("assumptions", [])],
        confidentiality=_enum(ConfidentialityLevel, data.get("confidentiality", "restricted")),
        synthetic_only=data.get("synthetic_only") is True,
        created_at=str(data.get("created_at", "2099-01-01T09:00:00Z")),
        privacy_probe=str(data["privacy_probe"]) if data.get("privacy_probe") else None,
    )


def load_fixture_cases(path: Path | str) -> list[EmployeeCase]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("cases"), list):
        raise ValueError("Employee case fixture must contain a cases array.")
    return [case_from_dict(item) for item in payload["cases"] if isinstance(item, dict)]


class EmployeeCasePipeline:
    def __init__(self) -> None:
        self.step_statuses = {step: StepStatus.NOT_STARTED for step in PIPELINE_STEPS}

    def _record(self, case: EmployeeCase, step: str, status: StepStatus, message: str, data: Any = None) -> StepResult:
        self.step_statuses[step] = status
        case.history.append(PipelineHistoryEntry(step, status, message))
        return StepResult(step, status, message, data)

    def validate_case(self, case: EmployeeCase) -> StepResult:
        required = (case.case_id, case.title, case.main_question, case.period, case.population)
        if not case.synthetic_only:
            raise PipelineBlocked("A non-synthetic employee case is forbidden.")
        if not all(value.strip() for value in required):
            raise PipelineBlocked("The employee case is missing a required field.")
        return self._record(case, "validate_case", StepStatus.COMPLETED, "Synthetic case structure is valid.")

    def validate_documents(self, case: EmployeeCase) -> StepResult:
        identifiers = [item.document_id for item in case.documents]
        if len(identifiers) != len(set(identifiers)):
            raise PipelineBlocked("Duplicate document identifier.")
        for document in case.documents:
            if not document.synthetic_only:
                raise PipelineBlocked("A non-synthetic document is forbidden.")
            if not document.document_id or not document.title or not document.declared_source:
                raise PipelineBlocked("A document is missing required metadata.")
        return self._record(case, "validate_documents", StepStatus.COMPLETED, "Document metadata is valid.")

    def _privacy_payload(self, case: EmployeeCase) -> dict[str, Any]:
        payload = case.as_dict()
        probe = payload.pop("privacy_probe", None)
        if probe == "synthetic_email_probe":
            payload["probe_value"] = "personne.alpha" + "@" + "entreprise.invalid"
        return payload

    def check_confidentiality(self, case: EmployeeCase) -> StepResult:
        report = privacy_validator.scan_object(self._privacy_payload(case))
        if report["blocked_count"]:
            raise PipelineBlocked("Confidentiality control rejected the employee case.")
        return self._record(case, "check_confidentiality", StepStatus.COMPLETED, "No blocking confidential data detected.", report)

    def classify_documents(self, case: EmployeeCase) -> StepResult:
        classified = {
            item.document_id: item.document_type.value
            for item in case.documents
            if item.availability is AvailabilityStatus.PRESENT
        }
        return self._record(case, "classify_documents", StepStatus.COMPLETED, "Documents classified.", classified)

    def identify_themes(self, case: EmployeeCase) -> StepResult:
        themes = list(dict.fromkeys(case.detected_themes))
        unknown = [item for item in themes if item not in DOCUMENT_REQUIREMENTS]
        status = StepStatus.WARNING if unknown else StepStatus.COMPLETED
        return self._record(case, "identify_themes", status, "Themes identified.", {"themes": themes, "unknown": unknown})

    def determine_required_documents(self, case: EmployeeCase) -> StepResult:
        requirements = {theme: dict(DOCUMENT_REQUIREMENTS.get(theme, {})) for theme in case.detected_themes}
        return self._record(case, "determine_required_documents", StepStatus.COMPLETED, "Document requirements determined.", requirements)

    def assess_document_completeness(self, case: EmployeeCase) -> StepResult:
        present = {item.document_type for item in case.documents if item.availability is AvailabilityStatus.PRESENT}
        themes: dict[str, Any] = {}
        all_missing: list[str] = []
        for theme in case.detected_themes:
            requirements = DOCUMENT_REQUIREMENTS.get(theme, {})
            required = {kind for kind, level in requirements.items() if level == REQUIRED}
            recommended = {kind for kind, level in requirements.items() if level == RECOMMENDED}
            missing_required = sorted(kind.value for kind in required - present)
            missing_recommended = sorted(kind.value for kind in recommended - present)
            all_missing.extend(missing_required)
            denominator = len(required) or 1
            score = (len(required & present) / denominator) * 100
            themes[theme] = {
                "status": "blocked" if missing_required else "complete",
                "score_percent": round(score, 2),
                "missing_required": missing_required,
                "missing_recommended": missing_recommended,
            }
        case.missing_documents = list(dict.fromkeys(all_missing))
        status = StepStatus.WARNING if case.missing_documents else StepStatus.COMPLETED
        return self._record(case, "assess_document_completeness", status, "Document completeness assessed without payroll calculation.", themes)

    def prepare_expert_contexts(self, case: EmployeeCase, completeness: Mapping[str, Any]) -> StepResult:
        present_documents = [item.document_type.value for item in case.documents if item.availability is AvailabilityStatus.PRESENT]
        base = {
            "question": case.main_question,
            "period": case.period,
            "population": case.population,
            "themes": list(case.detected_themes),
            "documents_present": present_documents,
            "documents_missing": list(case.missing_documents),
            "synthetic_facts": dict(case.employee_information),
            "document_references": [item.document_id for item in case.documents],
            "confidentiality_warnings": ["Synthetic case only; do not infer real personal or payroll values."],
            "theme_completeness": dict(completeness),
            "synthetic_only": True,
        }
        contexts = {
            "expert_paie": {**base, "requests": ["Identify control paths without calculating payroll."]},
            "juriste_travail": {**base, "requests": ["Identify applicable sources without issuing a definitive legal opinion."]},
            "future_experts": {
                "cse": "Interface not integrated in LOT 5A.",
                "security": "Interface not integrated in LOT 5A.",
            },
        }
        return self._record(case, "prepare_expert_contexts", StepStatus.COMPLETED, "Expert contexts prepared.", contexts)

    def collect_expert_analyses(self, case: EmployeeCase, analyses: Iterable[ExpertAnalysis] | None) -> StepResult:
        collected = list(analyses or [])
        if not collected:
            fallback = ExpertAnalysis(
                expert="experts",
                status=ExpertStatus.UNAVAILABLE,
                summary="No expert analysis supplied; safe fallback retained.",
                confidence="UNKNOWN",
                refusal_reason="Expert unavailable.",
            )
            collected = [fallback]
            return self._record(case, "collect_expert_analyses", StepStatus.WARNING, "Expert fallback created.", collected)
        return self._record(case, "collect_expert_analyses", StepStatus.COMPLETED, "Expert analyses received.", collected)

    def aggregate_results(self, case: EmployeeCase, analyses: list[ExpertAnalysis], completeness: Mapping[str, Any]) -> StepResult:
        blocked_themes = [theme for theme, item in completeness.items() if item.get("status") == "blocked"]
        refusals = [item.refusal_reason for item in analyses if item.refusal_reason]
        confidence_values = [item.confidence for item in analyses if item.confidence in CONFIDENCE_ORDER]
        global_confidence = min(confidence_values, key=CONFIDENCE_ORDER.get) if confidence_values else "UNKNOWN"
        aggregation = {
            "general_summary": "Structured aggregation of supplied expert analyses; no new conclusion generated.",
            "themes_analyzed": [theme for theme in case.detected_themes if theme not in blocked_themes],
            "themes_blocked": blocked_themes,
            "convergent_findings": self._convergent_findings(analyses),
            "contradictions": [],
            "missing_documents": list(case.missing_documents),
            "recommended_control_actions": list(dict.fromkeys(point for item in analyses for point in item.control_points)),
            "global_confidence": global_confidence,
            "limits": list(dict.fromkeys(limit for item in analyses for limit in item.limits)),
            "expert_refusals": refusals,
        }
        return self._record(case, "aggregate_results", StepStatus.COMPLETED, "Expert results aggregated without invention.", aggregation)

    @staticmethod
    def _convergent_findings(analyses: list[ExpertAnalysis]) -> list[str]:
        counts: dict[str, int] = {}
        for analysis in analyses:
            for finding in set(analysis.findings):
                counts[finding] = counts.get(finding, 0) + 1
        return sorted(item for item, count in counts.items() if count >= 2)

    def detect_contradictions(
        self,
        case: EmployeeCase,
        analyses: list[ExpertAnalysis],
        completeness: Mapping[str, Any],
        aggregation: dict[str, Any],
    ) -> StepResult:
        contradictions: list[str] = []
        periods = {item.period for item in analyses if item.period}
        if len(periods) > 1:
            contradictions.append("Experts cite different periods.")
        case_document_ids = {item.document_id for item in case.documents if item.availability is AvailabilityStatus.PRESENT}
        for analysis in analyses:
            unknown_documents = set(analysis.documents_used) - case_document_ids
            if unknown_documents:
                contradictions.append(f"{analysis.expert} cites documents absent from the case: {sorted(unknown_documents)}")
            if analysis.status is ExpertStatus.COMPLETED and any(
                item.get("status") == "blocked" for item in completeness.values()
            ) and not analysis.refusal_reason:
                contradictions.append(f"{analysis.expert} concludes despite a missing required document.")
        confidences = {item.confidence for item in analyses if item.confidence in CONFIDENCE_ORDER}
        if confidences and max(CONFIDENCE_ORDER[item] for item in confidences) - min(CONFIDENCE_ORDER[item] for item in confidences) >= 3:
            contradictions.append("Expert confidence levels are incompatible.")
        sources_by_expert = {item.expert: set(item.cited_rules_or_sources) for item in analyses if item.cited_rules_or_sources}
        if len(sources_by_expert) > 1 and not set.intersection(*sources_by_expert.values()):
            contradictions.append("Experts cite non-overlapping rules or sources requiring reconciliation.")
        facts: dict[str, str] = {}
        for document in case.documents:
            for key, value in document.metadata.get("asserted_facts", {}).items():
                if key in facts and facts[key] != str(value):
                    contradictions.append(f"Synthetic documents contradict each other on fact: {key}.")
                facts[key] = str(value)
        aggregation["contradictions"] = list(dict.fromkeys(contradictions))
        status = StepStatus.WARNING if contradictions else StepStatus.COMPLETED
        return self._record(case, "detect_contradictions", status, "Contradictions made visible.", aggregation["contradictions"])

    def produce_diagnostic(self, case: EmployeeCase, aggregation: dict[str, Any]) -> StepResult:
        if aggregation["contradictions"] or aggregation["themes_blocked"] or aggregation["expert_refusals"]:
            case.status = CaseStatus.PARTIAL
        else:
            case.status = CaseStatus.COMPLETED
        diagnostic = {**aggregation, "final_status": case.status.value, "calculation_performed": False, "legal_opinion_produced": False}
        return self._record(case, "produce_diagnostic", StepStatus.COMPLETED, "Structured case diagnostic produced.", diagnostic)

    def run(self, case: EmployeeCase, analyses: Iterable[ExpertAnalysis] | None = None) -> dict[str, Any]:
        self.step_statuses = {step: StepStatus.NOT_STARTED for step in PIPELINE_STEPS}
        results: dict[str, StepResult] = {}
        try:
            for step in PIPELINE_STEPS[:6]:
                self.step_statuses[step] = StepStatus.RUNNING
                results[step] = getattr(self, step)(case)
            self.step_statuses["assess_document_completeness"] = StepStatus.RUNNING
            results["assess_document_completeness"] = self.assess_document_completeness(case)
            completeness = results["assess_document_completeness"].data
            self.step_statuses["prepare_expert_contexts"] = StepStatus.RUNNING
            results["prepare_expert_contexts"] = self.prepare_expert_contexts(case, completeness)
            self.step_statuses["collect_expert_analyses"] = StepStatus.RUNNING
            results["collect_expert_analyses"] = self.collect_expert_analyses(case, analyses)
            expert_analyses = results["collect_expert_analyses"].data
            self.step_statuses["aggregate_results"] = StepStatus.RUNNING
            results["aggregate_results"] = self.aggregate_results(case, expert_analyses, completeness)
            aggregation = results["aggregate_results"].data
            self.step_statuses["detect_contradictions"] = StepStatus.RUNNING
            results["detect_contradictions"] = self.detect_contradictions(case, expert_analyses, completeness, aggregation)
            self.step_statuses["produce_diagnostic"] = StepStatus.RUNNING
            results["produce_diagnostic"] = self.produce_diagnostic(case, aggregation)
        except PipelineBlocked as exc:
            running = next((step for step, status in self.step_statuses.items() if status is StepStatus.RUNNING), "validate_case")
            self._record(case, running, StepStatus.BLOCKED, str(exc))
            case.status = CaseStatus.BLOCKED
            return {
                "case_id": case.case_id,
                "final_status": case.status.value,
                "blocked_at": running,
                "error": str(exc),
                "steps": {step: status.value for step, status in self.step_statuses.items()},
                "calculation_performed": False,
            }
        except Exception as exc:
            running = next((step for step, status in self.step_statuses.items() if status is StepStatus.RUNNING), "unknown")
            self._record(case, running, StepStatus.FAILED, str(exc))
            case.status = CaseStatus.FAILED
            return {
                "case_id": case.case_id,
                "final_status": case.status.value,
                "failed_at": running,
                "error": str(exc),
                "steps": {step: status.value for step, status in self.step_statuses.items()},
                "calculation_performed": False,
            }
        return {
            "case_id": case.case_id,
            "final_status": case.status.value,
            "steps": {step: status.value for step, status in self.step_statuses.items()},
            "contexts": results["prepare_expert_contexts"].data,
            "diagnostic": results["produce_diagnostic"].data,
            "history": [entry.message for entry in case.history],
        }
