"""Explicit mappings from historical Juriste/Paie payloads to existing contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
from typing import Any

from automation.adapters import legacy_payroll_report_to_expert_report
from automation.contracts import ExpertReport, ExpertRequest, ReportStatus
from automation.expert_facades.payroll import PAYROLL_EXPERT_ID
from NEXUS_CORE import (
    AcquisitionMethod,
    ConfidentialityLevel,
    DocumentId,
    DocumentMetadata,
    DocumentReference,
    DocumentSource,
    DocumentType,
    EntityId,
    EntityReference,
    Evidence,
    EvidenceId,
    EvidenceQuality,
    Finding,
    FindingId,
    FindingSeverity,
    FindingStatus,
    FindingType,
    Provenance,
    Recommendation,
    RecommendationId,
    RecommendationPriority,
    RecommendationStatus,
    RecommendationType,
    SourceReference,
    SourceType,
    TextEvidenceValue,
    ValidationStatus,
)
from NEXUS_CORE.quality import ConfidenceLevel, ConfidenceScore


def _stable(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:24]
    return f"runtime-{prefix}-{digest}"


def _strings(value: object, *, limit: int = 20) -> tuple[str, ...]:
    if isinstance(value, str):
        cleaned = value.strip()
        return (cleaned,) if cleaned else ()
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        return ()
    result = []
    for item in value:
        if isinstance(item, str) and item.strip() and item.strip() not in result:
            result.append(item.strip())
        if len(result) >= limit:
            break
    return tuple(result)


def _confidence(value: object) -> ConfidenceScore:
    normalized = str(value or "").strip().lower()
    values = {
        "fort": (0.8, ConfidenceLevel.HIGH),
        "high": (0.8, ConfidenceLevel.HIGH),
        "moyen": (0.5, ConfidenceLevel.MEDIUM),
        "medium": (0.5, ConfidenceLevel.MEDIUM),
        "faible": (0.2, ConfidenceLevel.LOW),
        "low": (0.2, ConfidenceLevel.LOW),
    }
    score, level = values.get(normalized, (0.0, ConfidenceLevel.UNKNOWN))
    return ConfidenceScore(score, level)


@dataclass(frozen=True, slots=True)
class RuntimeCoreArtifacts:
    evidence: tuple[Evidence, ...] = ()
    findings: tuple[Finding, ...] = ()
    recommendations: tuple[Recommendation, ...] = ()
    documents: tuple[DocumentReference, ...] = ()


@dataclass(frozen=True, slots=True)
class MappedLegalPayload:
    report: ExpertReport
    artifacts: RuntimeCoreArtifacts


class RuntimeExpertPayloadMapper:
    """Map only fields already emitted by the historical experts."""

    def build_request(self, answer: Mapping[str, Any]) -> ExpertRequest:
        question = str(answer.get("query") or "").strip()
        if not question:
            raise ValueError("RUNTIME_QUESTION_MISSING")
        route = answer.get("route") if isinstance(answer.get("route"), Mapping) else {}
        domains = tuple(str(item) for item in route.get("domains") or ())
        request_id = _stable("request", question)
        return ExpertRequest(
            request_id=request_id,
            question_text=question,
            requested_domain=str(route.get("main_domain") or "runtime"),
            context={"route_domains": list(domains)},
            metadata={"runtime_bridge": {"source": "historical_runtime", "version": "1.0"}},
        )

    def map_payroll(self, payload: object, request_id: str) -> ExpertReport | None:
        if payload is None:
            return None
        if not isinstance(payload, Mapping):
            raise ValueError("RUNTIME_PAYROLL_PAYLOAD_MALFORMED")
        if payload.get("active") is False:
            return None
        report = legacy_payroll_report_to_expert_report(payload, request_id)
        metadata = report.to_dict().get("metadata", {})
        metadata["runtime_original_producer"] = report.producer
        return replace(report, producer=PAYROLL_EXPERT_ID, metadata=metadata)

    def map_legal(
        self,
        payload: object,
        answer: Mapping[str, Any],
        request_id: str,
        subject: EntityReference,
        produced_at: datetime | None = None,
    ) -> MappedLegalPayload | None:
        if payload is None:
            return None
        if not isinstance(payload, Mapping):
            raise ValueError("RUNTIME_LEGAL_PAYLOAD_MALFORMED")
        if payload.get("active") is False:
            return None
        timestamp = produced_at or datetime.now(timezone.utc)
        findings = _strings(payload.get("ce_qui_est_certain")) or _strings(payload.get("faits_connus"))
        risks = _strings(payload.get("risques_points_vigilance"))
        recommendations = _strings(payload.get("strategie_action_ordonnee")) or _strings(payload.get("plan_action"))
        questions = _strings(payload.get("questions_a_poser_direction"))
        warnings = _strings(payload.get("limites"))
        conclusion = payload.get("conclusion_provisoire_juridique")
        conclusions = ()
        if isinstance(conclusion, Mapping):
            conclusions = _strings(conclusion.get("position"))
        elif conclusion is not None:
            conclusions = _strings(conclusion)
        report = ExpertReport(
            report_id=_stable("legal-report", request_id),
            request_id=request_id,
            producer="juriste_travail",
            findings=findings + risks,
            conclusions=conclusions,
            recommendations=recommendations,
            questions_to_ask=questions,
            warnings=warnings,
            status=ReportStatus.PARTIAL if warnings else ReportStatus.COMPLETED,
            metadata={"runtime_mapper": "minimal_legal_v1"},
        )
        artifacts = self._legal_artifacts(report, answer, subject, timestamp, payload.get("niveau_de_confiance"))
        return MappedLegalPayload(report, artifacts)

    def _legal_artifacts(
        self,
        report: ExpertReport,
        answer: Mapping[str, Any],
        subject: EntityReference,
        timestamp: datetime,
        confidence_value: object,
    ) -> RuntimeCoreArtifacts:
        producer = EntityId("runtime-legal-mapper")
        source = SourceReference(producer, SourceType.INTERNAL_REFERENTIAL, "RUNTIME_LEGAL_EXPERT")
        provenance = Provenance(source, AcquisitionMethod.GENERATED, timestamp)
        confidence = _confidence(confidence_value or answer.get("confidence"))
        evidence = []
        findings = []
        for index, text in enumerate(report.findings):
            evidence_id = EvidenceId(_stable("legal-evidence", report.report_id, str(index)))
            evidence.append(Evidence(
                evidence_id, subject, "legal_observation", TextEvidenceValue(text), None, None,
                provenance, confidence, EvidenceQuality.CONSISTENT, ValidationStatus.NOT_VALIDATED,
                producer, (), timestamp, ConfidentialityLevel.HIGHLY_CONFIDENTIAL,
            ))
            findings.append(Finding(
                FindingId(_stable("legal-finding", report.report_id, str(index))),
                FindingType.OBSERVATION, FindingSeverity.INFO, FindingStatus.OPEN,
                "RUNTIME_LEGAL_OBSERVATION", (evidence_id,),
            ))
        recommendations = tuple(
            Recommendation(
                RecommendationId(_stable("legal-recommendation", report.report_id, str(index))),
                RecommendationType.MANUAL_REVIEW, RecommendationPriority.NORMAL,
                RecommendationStatus.PROPOSED, "RUNTIME_LEGAL_RECOMMENDATION",
            )
            for index, _ in enumerate(report.recommendations)
        )
        documents = self._documents(answer)
        return RuntimeCoreArtifacts(tuple(evidence), tuple(findings), recommendations, documents)

    def _documents(self, answer: Mapping[str, Any]) -> tuple[DocumentReference, ...]:
        result = []
        raw_sources = answer.get("sources")
        if not isinstance(raw_sources, Sequence) or isinstance(raw_sources, (str, bytes, bytearray)):
            return ()
        for index, item in enumerate(raw_sources[:20]):
            if not isinstance(item, Mapping):
                continue
            origin = str(item.get("origin") or item.get("source_layer") or "unknown")
            title = str(item.get("document") or item.get("title") or "").strip() or None
            document_type = self._document_type(str(item.get("source_layer") or ""))
            source_reference = SourceReference(
                EntityId(_stable("legal-source", origin, str(index))),
                SourceType.LEGAL_DATABASE if "legifrance" in origin or "judilibre" in origin else SourceType.INTERNAL_REFERENTIAL,
                "RUNTIME_LEGAL_SOURCE",
            )
            result.append(DocumentReference(
                DocumentId(_stable("legal-document", origin, str(index), title or "untitled")),
                document_type,
                DocumentSource(source_reference),
                DocumentMetadata(document_type, title),
                ConfidentialityLevel.INTERNAL,
            ))
        return tuple(result)

    @staticmethod
    def _document_type(layer: str) -> DocumentType:
        normalized = layer.lower()
        if normalized == "accord_entreprise":
            return DocumentType.COLLECTIVE_AGREEMENT
        if normalized == "jurisprudence":
            return DocumentType.CASE_LAW
        if normalized in {"code_travail", "convention_collective"}:
            return DocumentType.LEGAL_TEXT
        return DocumentType.OTHER
