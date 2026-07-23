"""Explicit documentary evidence mapping from Retirement to Nexus Core."""

from __future__ import annotations

from datetime import datetime

from automation.contracts import ExpertReport
from RETIREMENT_PENIBILITY_ENGINE.career_evidence_models import CareerEvidenceItem, EvidenceBundle
from RETIREMENT_PENIBILITY_ENGINE.retirement_models import EvidenceItem as FoundationEvidence
from NEXUS_CORE import (
    AcquisitionMethod, ConfidentialityLevel, CustomEvidenceValue, DocumentId,
    DocumentMetadata, DocumentReference, DocumentSource, EntityId, EntityReference,
    Evidence, EvidenceId, EvidenceQuality, Period, Provenance, SourceReference,
    SourceType, TextEvidenceValue, ValidationStatus,
)

from ._identity import stable_retirement_id
from .metadata import RetirementMetadataMapper


class RetirementEvidenceMapper:
    """Map references and metadata; never copy documentary content."""

    def __init__(self, metadata: RetirementMetadataMapper | None = None) -> None:
        self._metadata = metadata or RetirementMetadataMapper()

    def map_bundle(self, bundle: EvidenceBundle | None, subject: EntityReference,
                   produced_at: datetime) -> tuple[Evidence, ...]:
        if bundle is None:
            return ()
        return tuple(self._bundle_item(item, subject, produced_at) for item in bundle.evidence)

    def map_foundation(self, report_id: str, items: tuple[FoundationEvidence, ...],
                       subject: EntityReference, produced_at: datetime) -> tuple[Evidence, ...]:
        return tuple(
            Evidence(
                EvidenceId(stable_retirement_id("evidence", report_id, item.evidence_id)),
                subject,
                "retirement_documentary_reference",
                CustomEvidenceValue(
                    "retirement_documentary_reference",
                    (self._metadata.metadata("document_type", item.document_type),),
                ),
                None,
                None,
                self._provenance(item.source_id, produced_at, item.evidence_id),
                self._metadata.confidence_from_grade(item.grade),
                EvidenceQuality.CONSISTENT if item.official else EvidenceQuality.UNKNOWN,
                ValidationStatus.VALID if item.verified else ValidationStatus.PENDING,
                EntityId("adapter-retirement"),
                (),
                produced_at,
                ConfidentialityLevel.HIGHLY_CONFIDENTIAL,
            )
            for item in items
        )

    def map_documents(self, bundle: EvidenceBundle | None) -> tuple[DocumentReference, ...]:
        if bundle is None:
            return ()
        return tuple(self._document(item) for item in bundle.evidence)

    def map_expert(self, report: ExpertReport | None, subject: EntityReference,
                   produced_at: datetime) -> tuple[Evidence, ...]:
        if report is None:
            return ()
        values = tuple(report.findings) + tuple(report.contradictions)
        return tuple(
            Evidence(
                EvidenceId(stable_retirement_id("evidence", report.report_id, "expert", str(index))),
                subject,
                "retirement_expert_report",
                TextEvidenceValue(value),
                None,
                None,
                self._provenance(report.producer, produced_at, report.report_id),
                self._metadata.expert_confidence(report),
                self._metadata.expert_quality(report),
                self._metadata.expert_validation(report),
                EntityId(stable_retirement_id("producer", report.producer)),
                (
                    self._metadata.metadata("expert_status", report.status.value),
                    self._metadata.metadata("expert_schema_version", report.schema_version),
                ),
                produced_at,
                ConfidentialityLevel.HIGHLY_CONFIDENTIAL,
            )
            for index, value in enumerate(values)
        )

    @staticmethod
    def core_id(source_id: str) -> EvidenceId:
        return EvidenceId(stable_retirement_id("evidence", source_id))

    def _bundle_item(self, item: CareerEvidenceItem, subject: EntityReference,
                     produced_at: datetime) -> Evidence:
        start = self._metadata.parse_date(item.valid_from)
        end = self._metadata.parse_date(item.valid_to)
        period = Period(start, end) if start is not None else None
        return Evidence(
            self.core_id(str(item.reference.evidence_id)),
            subject,
            "retirement_career_evidence",
            CustomEvidenceValue(
                "retirement_career_evidence",
                (
                    self._metadata.metadata("source_type", item.reference.source_type.value),
                    self._metadata.metadata("evidence_status", item.status.value),
                ),
            ),
            period,
            self._document(item),
            self._provenance(item.reference.provenance, produced_at, str(item.reference.evidence_id)),
            self._metadata.evidence_confidence(item.confidence_level),
            self._metadata.quality(item.authority_level),
            self._metadata.validation(item.status),
            EntityId("adapter-retirement"),
            (),
            produced_at,
            ConfidentialityLevel.HIGHLY_CONFIDENTIAL,
        )

    def _document(self, item: CareerEvidenceItem) -> DocumentReference:
        source = SourceReference(
            EntityId(stable_retirement_id("source", item.reference.provenance)),
            self._metadata.source_type(item.reference.source_type),
            "RETIREMENT_EVIDENCE_SOURCE",
        )
        document_type = self._metadata.document_type(item.reference.source_type)
        return DocumentReference(
            DocumentId(stable_retirement_id("document", str(item.reference.evidence_id))),
            document_type,
            DocumentSource(source),
            DocumentMetadata(
                document_type,
                title="RETIREMENT_DOCUMENT_REFERENCE",
                entries=(self._metadata.metadata("source_type", item.reference.source_type.value),),
            ),
            ConfidentialityLevel.HIGHLY_CONFIDENTIAL,
        )

    @staticmethod
    def _provenance(source: str, produced_at: datetime, trace: str) -> Provenance:
        return Provenance(
            SourceReference(
                EntityId(stable_retirement_id("source", source)),
                SourceType.INTERNAL_REFERENTIAL,
                "RETIREMENT_ENGINE_SOURCE",
            ),
            AcquisitionMethod.GENERATED,
            produced_at,
            EntityId(stable_retirement_id("trace", trace)),
        )
