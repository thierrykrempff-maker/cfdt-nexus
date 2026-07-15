#!/usr/bin/env python
"""LOT 4G - Deterministic reasoning protocol for the INEOS Payroll Expert.

This module describes how to analyse a payroll question.  It deliberately
does not import or call the payroll rule engine, an expert or an orchestrator.
It identifies evidence to retrieve and controls to perform; it never computes
a payroll result.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Iterable, Mapping, Sequence


class ReasoningStep(str, Enum):
    UNDERSTAND_REQUEST = "understand_request"
    IDENTIFY_POPULATION = "identify_population"
    IDENTIFY_PERIOD = "identify_period"
    IDENTIFY_REQUIRED_DOCUMENTS = "identify_required_documents"
    SEARCH_APPLICABLE_RULES = "search_applicable_rules"
    SEARCH_VARIABLES = "search_variables"
    SEARCH_KELIO_COUNTERS = "search_kelio_counters"
    SEARCH_NIBELIS_RUBRICS = "search_nibelis_rubrics"
    SEARCH_PARAMETERS = "search_parameters"
    IDENTIFY_MISSING_INFORMATION = "identify_missing_information"
    DETERMINE_CONFIDENCE = "determine_confidence"
    PRODUCE_RESPONSE = "produce_response"


PROTOCOL_STEPS: tuple[ReasoningStep, ...] = tuple(ReasoningStep)


class ConfidenceLevel(str, Enum):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class DocumentCategory(str, Enum):
    AGREEMENT = "agreement"
    COLLECTIVE_AGREEMENT = "collective_agreement"
    LABOUR_CODE = "labour_code"
    KELIO = "kelio"
    NIBELIS = "nibelis"
    PAYSLIP = "payslip"
    HR_LETTER = "hr_letter"
    MANAGER_DECISION = "manager_decision"
    OTHER = "other"


class QuestionScope(str, Enum):
    EMPLOYEE = "employee"
    COLLECTIVE = "collective"


class Audience(str, Enum):
    EMPLOYEE = "employee"
    EXPERT = "expert"


@dataclass(frozen=True)
class SubjectEvidence:
    required: tuple[DocumentCategory, ...]
    recommended: tuple[DocumentCategory, ...]
    sequence: tuple[str, ...]


SUBJECT_EVIDENCE: Mapping[str, SubjectEvidence] = {
    "heures_supplementaires": SubjectEvidence(
        required=(DocumentCategory.KELIO, DocumentCategory.PAYSLIP, DocumentCategory.AGREEMENT),
        recommended=(DocumentCategory.COLLECTIVE_AGREEMENT, DocumentCategory.MANAGER_DECISION),
        sequence=("planning", "Kelio", "bulletin", "accord"),
    ),
    "conges_payes": SubjectEvidence(
        required=(DocumentCategory.KELIO, DocumentCategory.PAYSLIP),
        recommended=(DocumentCategory.AGREEMENT, DocumentCategory.COLLECTIVE_AGREEMENT),
        sequence=("demande et validation de conge", "compteur Kelio", "bulletin", "accord"),
    ),
    "absence": SubjectEvidence(
        required=(DocumentCategory.KELIO, DocumentCategory.PAYSLIP),
        recommended=(DocumentCategory.HR_LETTER, DocumentCategory.AGREEMENT),
        sequence=("justificatif", "Kelio", "bulletin", "courrier RH"),
    ),
    "prime": SubjectEvidence(
        required=(DocumentCategory.PAYSLIP,),
        recommended=(DocumentCategory.AGREEMENT, DocumentCategory.MANAGER_DECISION, DocumentCategory.NIBELIS),
        sequence=("accord ou decision", "conditions d'attribution", "bulletin", "rubrique Nibelis"),
    ),
    "temps_de_travail": SubjectEvidence(
        required=(DocumentCategory.KELIO, DocumentCategory.AGREEMENT),
        recommended=(DocumentCategory.PAYSLIP, DocumentCategory.MANAGER_DECISION),
        sequence=("planning", "Kelio", "accord", "bulletin"),
    ),
    "general": SubjectEvidence(
        required=(),
        recommended=(DocumentCategory.AGREEMENT, DocumentCategory.COLLECTIVE_AGREEMENT, DocumentCategory.LABOUR_CODE),
        sequence=("question precise", "source applicable", "document de situation"),
    ),
}


@dataclass(frozen=True)
class PayrollQuestion:
    question: str
    question_type: str
    subject: str
    scope: QuestionScope
    population: str | None = None
    period: str | None = None
    payroll_period: str | None = None
    urgent: bool = False
    available_documents: frozenset[DocumentCategory] = frozenset()
    sources: tuple[str, ...] = ()
    rules: tuple[str, ...] = ()
    variables: tuple[str, ...] = ()
    kelio_counters: tuple[str, ...] = ()
    nibelis_rubrics: tuple[str, ...] = ()
    parameters: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    contradictory_documents: bool = False


@dataclass(frozen=True)
class Refusal:
    code: str
    reason: str
    requested_documents: tuple[DocumentCategory, ...] = ()


@dataclass(frozen=True)
class ProtocolAssessment:
    steps: tuple[str, ...]
    subject: str
    understanding: Mapping[str, str | bool | None]
    required_documents: tuple[str, ...]
    recommended_documents: tuple[str, ...]
    present_documents: tuple[str, ...]
    absent_documents: tuple[str, ...]
    indispensable_missing_documents: tuple[str, ...]
    retrieval: Mapping[str, tuple[str, ...]]
    controls: Mapping[str, tuple[str, ...]]
    missing_information: tuple[str, ...]
    confidence: ConfidenceLevel
    refusals: tuple[Refusal, ...]
    can_conclude: bool

    def as_dict(self) -> dict[str, object]:
        result = asdict(self)
        result["confidence"] = self.confidence.value
        return result


REFUSAL_POLICY: Mapping[str, str] = {
    "missing_period": "La periode concernee n'est pas renseignee.",
    "missing_population": "La population ou le salarie concerne n'est pas identifie.",
    "missing_source": "Aucune source applicable n'est disponible.",
    "missing_payslip": "Le bulletin indispensable au controle n'est pas disponible.",
    "missing_kelio": "Le compteur ou releve Kelio indispensable n'est pas disponible.",
    "missing_agreement": "L'accord indispensable a l'analyse n'est pas disponible.",
    "contradictory_documents": "Les documents disponibles sont contradictoires.",
}


def evidence_for(subject: str) -> SubjectEvidence:
    return SUBJECT_EVIDENCE.get(subject, SUBJECT_EVIDENCE["general"])


def _ordered_values(values: Iterable[DocumentCategory]) -> tuple[str, ...]:
    selected = set(values)
    return tuple(item.value for item in DocumentCategory if item in selected)


def apply_refusal_policy(question: PayrollQuestion, evidence: SubjectEvidence) -> tuple[Refusal, ...]:
    """Return every blocking reason; no payroll conclusion is inferred here."""
    refusals: list[Refusal] = []
    available = question.available_documents
    missing_required = set(evidence.required) - set(available)
    if not question.period:
        refusals.append(Refusal("missing_period", REFUSAL_POLICY["missing_period"]))
    if not question.population:
        refusals.append(Refusal("missing_population", REFUSAL_POLICY["missing_population"]))
    if not question.sources:
        refusals.append(Refusal("missing_source", REFUSAL_POLICY["missing_source"]))
    specific_missing = (
        (DocumentCategory.PAYSLIP, "missing_payslip"),
        (DocumentCategory.KELIO, "missing_kelio"),
        (DocumentCategory.AGREEMENT, "missing_agreement"),
    )
    for category, code in specific_missing:
        if category in missing_required:
            refusals.append(Refusal(code, REFUSAL_POLICY[code], (category,)))
    if question.contradictory_documents:
        refusals.append(Refusal("contradictory_documents", REFUSAL_POLICY["contradictory_documents"]))
    return tuple(refusals)


def determine_confidence(
    question: PayrollQuestion,
    evidence: SubjectEvidence,
    refusals: Sequence[Refusal],
) -> ConfidenceLevel:
    if not question.question.strip() or not question.subject.strip():
        return ConfidenceLevel.UNKNOWN
    if refusals:
        return ConfidenceLevel.LOW
    available = question.available_documents
    evidence_count = len(question.sources) + len(question.rules)
    referential_count = sum(
        bool(values)
        for values in (question.variables, question.kelio_counters, question.nibelis_rubrics, question.parameters)
    )
    if question.missing_information:
        return ConfidenceLevel.MEDIUM
    if set(evidence.required).issubset(available) and evidence_count >= 2 and referential_count >= 3:
        return ConfidenceLevel.VERY_HIGH
    if set(evidence.required).issubset(available) and evidence_count >= 1 and referential_count >= 1:
        return ConfidenceLevel.HIGH
    return ConfidenceLevel.MEDIUM


def assess(question: PayrollQuestion) -> ProtocolAssessment:
    """Apply the reasoning protocol without executing any payroll calculation."""
    evidence = evidence_for(question.subject)
    available = question.available_documents
    absent = set(DocumentCategory) - set(available)
    indispensable_missing = set(evidence.required) - set(available)
    refusals = apply_refusal_policy(question, evidence)
    confidence = determine_confidence(question, evidence, refusals)
    missing = list(question.missing_information)
    if not question.period:
        missing.append("periode")
    if not question.population:
        missing.append("population")
    missing = list(dict.fromkeys(missing))
    controls = {
        "coherences": ("periode entre documents", "population entre documents", "liens entre faits et sources"),
        "incoherences": (("documents contradictoires",) if question.contradictory_documents else ()),
        "missing_data": tuple(missing),
        "risks": tuple(refusal.reason for refusal in refusals),
    }
    retrieval = {
        "rules": question.rules,
        "variables": question.variables,
        "kelio_counters": question.kelio_counters,
        "nibelis_rubrics": question.nibelis_rubrics,
        "parameters": question.parameters,
    }
    return ProtocolAssessment(
        steps=tuple(step.value for step in PROTOCOL_STEPS),
        subject=question.subject,
        understanding={
            "question_type": question.question_type,
            "subject": question.subject,
            "scope": question.scope.value,
            "population": question.population,
            "period": question.period,
            "payroll_period": question.payroll_period,
            "urgent": question.urgent,
        },
        required_documents=_ordered_values(evidence.required),
        recommended_documents=_ordered_values(evidence.recommended),
        present_documents=_ordered_values(available),
        absent_documents=_ordered_values(absent),
        indispensable_missing_documents=_ordered_values(indispensable_missing),
        retrieval=retrieval,
        controls=controls,
        missing_information=tuple(missing),
        confidence=confidence,
        refusals=refusals,
        can_conclude=not refusals,
    )


def render_response(question: PayrollQuestion, assessment: ProtocolAssessment, audience: Audience) -> dict[str, object]:
    """Build audience-specific response instructions, never a calculated result."""
    conclusion = "Analyse possible sous reserve des limites indiquees."
    if not assessment.can_conclude:
        conclusion = "Impossible de conclure avec certitude."
    if audience is Audience.EMPLOYEE:
        return {
            "audience": audience.value,
            "message": conclusion,
            "explanation": "Les elements disponibles ont ete verifies avant de repondre.",
            "documents_to_provide": assessment.indispensable_missing_documents,
            "confidence": assessment.confidence.value,
        }
    return {
        "audience": audience.value,
        "conclusion": conclusion,
        "sources": question.sources,
        "retrieval": assessment.retrieval,
        "control_points": assessment.controls,
        "documents_to_verify": assessment.required_documents,
        "missing_information": assessment.missing_information,
        "limits": tuple(refusal.reason for refusal in assessment.refusals),
        "confidence": assessment.confidence.value,
    }


def requested_evidence_sequence(subject: str) -> tuple[str, ...]:
    """Return the human-readable collection order for a payroll subject."""
    return evidence_for(subject).sequence
