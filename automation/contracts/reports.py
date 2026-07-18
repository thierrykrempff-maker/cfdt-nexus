"""Normalized report contract produced by future Nexus experts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .assessments import MissingInformation, RiskAssessment
from .confidence import ConfidenceAssessment
from .enums import ConsultationStatus, ReportStatus, StatementKind
from .requests import ExpertRequest
from .serialization import contract_to_dict, freeze_metadata, reject_unknown_fields, require_text
from .sources import KnowledgeSource, SourceEvidence
from .statements import Statement


@dataclass(frozen=True)
class ExpertReport:
    report_id: str
    request_id: str
    producer: str
    findings: tuple[str, ...] = ()
    conclusions: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()
    proposed_actions: tuple[str, ...] = ()
    questions_to_ask: tuple[str, ...] = ()
    missing_information: tuple[MissingInformation, ...] = ()
    risks: tuple[RiskAssessment, ...] = ()
    sources: tuple[KnowledgeSource, ...] = ()
    source_evidence: tuple[SourceEvidence, ...] = ()
    contradictions: tuple[str, ...] = ()
    assumptions: tuple[Statement, ...] = ()
    scenarios: tuple[Statement, ...] = ()
    confidence_assessments: tuple[ConfidenceAssessment, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    status: ReportStatus = ReportStatus.DRAFT
    schema_version: str = "1.0"
    metadata: Mapping[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        for name in ("report_id", "request_id", "producer"):
            object.__setattr__(self, name, require_text(getattr(self, name), name))
        object.__setattr__(self, "schema_version", require_text(self.schema_version, "schema_version"))
        if not isinstance(self.status, ReportStatus):
            raise TypeError("status must be a ReportStatus")
        for name in (
            "findings", "conclusions", "recommendations", "proposed_actions", "questions_to_ask",
            "contradictions", "warnings", "errors",
        ):
            object.__setattr__(self, name, tuple(require_text(item, name) for item in getattr(self, name)))
        for name, expected in (
            ("missing_information", MissingInformation), ("risks", RiskAssessment), ("sources", KnowledgeSource),
            ("source_evidence", SourceEvidence), ("confidence_assessments", ConfidenceAssessment),
        ):
            values = tuple(getattr(self, name))
            if any(not isinstance(item, expected) for item in values):
                raise TypeError(f"{name} must contain {expected.__name__} objects")
            object.__setattr__(self, name, values)
        dimensions = [item.dimension for item in self.confidence_assessments]
        if len(dimensions) != len(set(dimensions)):
            raise ValueError("confidence_assessments must contain at most one assessment per dimension")
        assumptions = tuple(self.assumptions)
        scenarios = tuple(self.scenarios)
        if any(not isinstance(item, Statement) or item.kind is not StatementKind.ASSUMPTION for item in assumptions):
            raise ValueError("assumptions may contain only ASSUMPTION statements")
        if any(not isinstance(item, Statement) or item.kind is not StatementKind.SCENARIO for item in scenarios):
            raise ValueError("scenarios may contain only SCENARIO statements")
        object.__setattr__(self, "assumptions", assumptions)
        object.__setattr__(self, "scenarios", scenarios)
        self._validate_source_links()
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))

    def _validate_source_links(self) -> None:
        source_ids = [item.source_id for item in self.sources]
        evidence_ids = [item.evidence_id for item in self.source_evidence]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("sources must have unique source_id values")
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("source_evidence must have unique evidence_id values")
        source_id_set = set(source_ids)
        if any(item.source_id not in source_id_set for item in self.source_evidence):
            raise ValueError("every SourceEvidence must reference a source included in the report")
        evidence_by_id = {item.evidence_id: item for item in self.source_evidence}
        for source in self.sources:
            if source.retrieval_evidence_id:
                evidence = evidence_by_id.get(source.retrieval_evidence_id)
                if evidence is None or evidence.source_id != source.source_id:
                    raise ValueError("KnowledgeSource retrieval_evidence_id must reference matching SourceEvidence")
                if evidence.consultation_status not in {ConsultationStatus.SUCCEEDED, ConsultationStatus.CACHE_HIT}:
                    raise ValueError("consulted KnowledgeSource requires successful or cached SourceEvidence")

    def validate_for_request(self, request: ExpertRequest) -> None:
        if not isinstance(request, ExpertRequest):
            raise TypeError("request must be an ExpertRequest")
        if self.request_id != request.request_id:
            raise ValueError("report request_id does not match ExpertRequest request_id")

    def to_dict(self) -> dict[str, Any]:
        return contract_to_dict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ExpertReport":
        allowed = {
            "report_id", "request_id", "producer", "findings", "conclusions", "recommendations",
            "proposed_actions", "questions_to_ask", "missing_information", "risks", "sources", "source_evidence",
            "contradictions", "assumptions", "scenarios", "confidence_assessments", "warnings", "errors", "status", "schema_version", "metadata",
        }
        reject_unknown_fields(value, allowed, "ExpertReport")
        return cls(
            report_id=str(value.get("report_id", "")), request_id=str(value.get("request_id", "")),
            producer=str(value.get("producer", "")), findings=tuple(value.get("findings") or ()),
            conclusions=tuple(value.get("conclusions") or ()), recommendations=tuple(value.get("recommendations") or ()),
            proposed_actions=tuple(value.get("proposed_actions") or ()), questions_to_ask=tuple(value.get("questions_to_ask") or ()),
            missing_information=tuple(MissingInformation.from_dict(item) for item in value.get("missing_information") or ()),
            risks=tuple(RiskAssessment.from_dict(item) for item in value.get("risks") or ()),
            sources=tuple(KnowledgeSource.from_dict(item) for item in value.get("sources") or ()),
            source_evidence=tuple(SourceEvidence.from_dict(item) for item in value.get("source_evidence") or ()),
            contradictions=tuple(value.get("contradictions") or ()),
            assumptions=tuple(Statement.from_dict(item) for item in value.get("assumptions") or ()),
            scenarios=tuple(Statement.from_dict(item) for item in value.get("scenarios") or ()),
            confidence_assessments=tuple(ConfidenceAssessment.from_dict(item) for item in value.get("confidence_assessments") or ()),
            warnings=tuple(value.get("warnings") or ()), errors=tuple(value.get("errors") or ()),
            status=ReportStatus(value.get("status", "DRAFT")), schema_version=str(value.get("schema_version", "1.0")),
            metadata=value.get("metadata") or {},
        )
