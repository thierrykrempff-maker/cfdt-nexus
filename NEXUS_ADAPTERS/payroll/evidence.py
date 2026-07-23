"""Explicit Expert Paie to Nexus Core evidence and document mapping."""

from __future__ import annotations

from datetime import datetime

from automation.contracts import ExpertReport, KnowledgeSource
from NEXUS_CORE import (
    AcquisitionMethod,
    ConfidentialityLevel,
    CustomEvidenceValue,
    DocumentId,
    DocumentMetadata,
    DocumentReference,
    DocumentSource,
    EntityId,
    EntityReference,
    Evidence,
    EvidenceId,
    Period,
    Provenance,
    SourceReference,
    SourceType,
    TextEvidenceValue,
)

from ._identity import stable_payroll_id
from .metadata import PayrollMetadataMapper


class PayrollEvidenceMapper:
    def __init__(self, metadata: PayrollMetadataMapper | None = None) -> None:
        self._metadata = metadata or PayrollMetadataMapper()

    def map_documents(self, report: ExpertReport) -> tuple[DocumentReference, ...]:
        return tuple(self._document(source) for source in report.sources)

    def map(
        self,
        report: ExpertReport,
        subject: EntityReference,
        produced_at: datetime,
        period: Period | None = None,
    ) -> tuple[Evidence, ...]:
        documents = {
            source.source_id: document
            for source, document in zip(report.sources, self.map_documents(report))
        }
        items = []
        for index, value in enumerate(report.findings):
            items.append(self._narrative(report, subject, produced_at, period, "finding", index, value))
        for index, value in enumerate(report.contradictions):
            items.append(self._narrative(report, subject, produced_at, period, "contradiction", index, value))
        for index, value in enumerate(report.missing_information):
            items.append(self._narrative(report, subject, produced_at, period, "missing", index, value.description))
        for index, value in enumerate(report.risks):
            items.append(self._narrative(report, subject, produced_at, period, "risk", index, value.description))
        sources = {source.source_id: source for source in report.sources}
        for index, source_evidence in enumerate(report.source_evidence):
            source = sources.get(source_evidence.source_id)
            provenance = self._provenance(source, produced_at, source_evidence.evidence_id)
            items.append(
                Evidence(
                    EvidenceId(stable_payroll_id("evidence", report.report_id, "source", str(index))),
                    subject,
                    "payroll_source_consultation",
                    CustomEvidenceValue(
                        "payroll_source_consultation",
                        (
                            self._metadata.sensitive_text(
                                "consultation_status", source_evidence.consultation_status.value
                            ),
                        ),
                    ),
                    period,
                    documents.get(source_evidence.source_id),
                    provenance,
                    self._metadata.confidence(report),
                    self._metadata.quality(report),
                    self._metadata.validation(report),
                    self._producer(report),
                    (),
                    source_evidence.occurred_at or produced_at,
                    ConfidentialityLevel.INTERNAL,
                )
            )
        return tuple(items)

    def evidence_id(self, report: ExpertReport, category: str, index: int) -> EvidenceId:
        return EvidenceId(stable_payroll_id("evidence", report.report_id, category, str(index)))

    def _narrative(self, report, subject, produced_at, period, category, index, value):
        return Evidence(
            self.evidence_id(report, category, index),
            subject,
            f"payroll_{category}",
            TextEvidenceValue(value),
            period,
            None,
            self._provenance(None, produced_at, report.report_id),
            self._metadata.confidence(report),
            self._metadata.quality(report),
            self._metadata.validation(report),
            self._producer(report),
            (),
            produced_at,
            ConfidentialityLevel.HIGHLY_CONFIDENTIAL,
        )

    def _document(self, source: KnowledgeSource) -> DocumentReference:
        source_reference = SourceReference(
            EntityId(stable_payroll_id("source", source.source_id)),
            self._metadata.source_type(source.category, source.source_type),
            "PAYROLL_SOURCE",
        )
        document_type = self._metadata.document_type(source.source_type)
        return DocumentReference(
            DocumentId(stable_payroll_id("document", source.source_id, source.reference or "none")),
            document_type,
            DocumentSource(source_reference),
            DocumentMetadata(
                document_type,
                source.name,
                source.published_on,
                entries=(self._metadata.sensitive_text("publisher", source.publisher),),
            ),
            self._metadata.confidentiality(source.confidentiality),
        )

    def _provenance(self, source, produced_at, trace):
        if source is None:
            source_reference = SourceReference(
                EntityId("engine-payroll-expert"),
                SourceType.INTERNAL_REFERENTIAL,
                "PAYROLL_EXPERT",
            )
            acquired_at = produced_at
        else:
            source_reference = SourceReference(
                EntityId(stable_payroll_id("source", source.source_id)),
                self._metadata.source_type(source.category, source.source_type),
                "PAYROLL_SOURCE",
            )
            acquired_at = source.consulted_at or produced_at
        return Provenance(
            source_reference,
            AcquisitionMethod.GENERATED,
            acquired_at,
            EntityId(stable_payroll_id("trace", trace)),
        )

    @staticmethod
    def _producer(report: ExpertReport) -> EntityId:
        return EntityId(stable_payroll_id("producer", report.producer))
