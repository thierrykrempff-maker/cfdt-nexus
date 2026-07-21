"""Local structural Career Import Engine with no file-reading capability."""

from __future__ import annotations

from .career_evidence_models import (
    CareerEvidenceItem,
    EvidenceAuthorityLevel,
    EvidenceBundle,
    EvidenceConfidenceLevel,
    EvidenceId,
    EvidenceReference,
    EvidenceSourceType,
    EvidenceStatus,
)
from .career_import_models import (
    ImportBatch,
    ImportConflict,
    ImportConflictType,
    ImportNormalization,
    ImportRecommendation,
    ImportReport,
    ImportReportView,
    ImportStatus,
    ImportSummary,
    ImportValidation,
    ImportedCareerRecord,
    ImportedClassification,
    ImportedEmploymentPeriod,
    ImportedEvidence,
    ImportedFiveShift,
    ImportedNightWork,
)
from .career_import_normalizer import CareerImportNormalizer
from .career_import_report import CareerImportReportBuilder
from .career_import_validator import CareerImportValidator
from .career_timeline_models import CareerEvent, CareerEventType, CareerTimeline, EvidenceLevel
from .privacy_gate import RetirementPrivacyGate, require_privacy_gate


class CareerImportEngine:
    """Prepare injected metadata for LOT 2 and LOT 3 without importing files."""

    def __init__(
        self,
        validator: CareerImportValidator | None = None,
        normalizer: CareerImportNormalizer | None = None,
        report_builder: CareerImportReportBuilder | None = None,
        privacy_gate=RetirementPrivacyGate(),
    ) -> None:
        self._validator = validator or CareerImportValidator()
        self._normalizer = normalizer or CareerImportNormalizer()
        self._report_builder = report_builder or CareerImportReportBuilder()
        self._privacy_gate = privacy_gate

    def create_import_batch(
        self, batch_id: str, documents=(), records=()
    ) -> ImportBatch:
        batch = ImportBatch(batch_id, tuple(documents), tuple(records))
        self._assert_private(batch)
        return batch

    def validate_batch(self, batch: ImportBatch) -> ImportValidation:
        self._assert_private(batch)
        return self._validator.validate(batch)

    def normalize_batch(self, batch: ImportBatch) -> tuple[ImportNormalization, ...]:
        self._assert_private(batch)
        return self._normalizer.normalize(batch)

    def detect_conflicts(self, batch: ImportBatch) -> tuple[ImportConflict, ...]:
        self._assert_private(batch)
        conflicts: list[ImportConflict] = []
        records = batch.records
        for index, left in enumerate(records):
            for right in records[index + 1 :]:
                conflict_type = self._record_conflict(left, right)
                if conflict_type is not None:
                    conflicts.append(
                        ImportConflict(
                            f"conflict:{left.record_id}:{right.record_id}:{conflict_type.value}",
                            conflict_type,
                            (left.record_id, right.record_id),
                            "Injected records contain incompatible metadata.",
                            (left.provenance.source_id, right.provenance.source_id),
                        )
                    )
        for index, left in enumerate(batch.documents):
            for right in batch.documents[index + 1 :]:
                if (
                    left.source.internal_document_id == right.source.internal_document_id
                    and left.source.version != right.source.version
                ):
                    conflicts.append(
                        ImportConflict(
                            f"conflict:versions:{left.document_id}:{right.document_id}",
                            ImportConflictType.DIFFERENT_VERSIONS,
                            (),
                            "Different versions of the same declared document are retained.",
                            (left.source.source_id, right.source.source_id),
                        )
                    )
                if set(left.declared_record_ids) & set(right.declared_record_ids) and left.document_id != right.document_id:
                    conflicts.append(
                        ImportConflict(
                            f"conflict:documents:{left.document_id}:{right.document_id}",
                            ImportConflictType.DIFFERENT_DOCUMENTS,
                            tuple(sorted(set(left.declared_record_ids) & set(right.declared_record_ids))),
                            "Different documents describe the same imported record.",
                            (left.source.source_id, right.source.source_id),
                        )
                    )
        return tuple(conflicts)

    def build_import_summary(
        self,
        batch: ImportBatch,
        validation: ImportValidation,
        normalizations: tuple[ImportNormalization, ...],
        conflicts: tuple[ImportConflict, ...],
    ) -> ImportSummary:
        self._assert_private(batch)
        if conflicts:
            status = ImportStatus.CONFLICTED
        elif validation.valid:
            status = ImportStatus.READY_FOR_REVIEW
        else:
            status = ImportStatus.REJECTED
        return ImportSummary(
            batch.batch_id,
            status,
            tuple(item.document_id for item in batch.documents),
            tuple(item.record_id for item in batch.records),
            tuple(item.issue_id for item in validation.issues),
            tuple(item.conflict_id for item in conflicts),
            tuple(item.record_id for item in normalizations),
        )

    def generate_report(
        self,
        batch: ImportBatch,
        validation: ImportValidation,
        normalizations: tuple[ImportNormalization, ...],
        conflicts: tuple[ImportConflict, ...],
        view: ImportReportView,
    ) -> ImportReport:
        self._assert_private(batch)
        summary = self.build_import_summary(batch, validation, normalizations, conflicts)
        recommendations = self._recommendations(validation, conflicts)
        return self._report_builder.build(
            batch, summary, validation, normalizations, conflicts, recommendations, view
        )

    def prepare_timeline_records(
        self,
        batch: ImportBatch,
        normalizations: tuple[ImportNormalization, ...],
    ) -> CareerTimeline:
        self._assert_private(batch)
        normalized = {item.record_id: dict(item.normalized_values) for item in normalizations}
        events: list[CareerEvent] = []
        for record in batch.records:
            if not isinstance(record, ImportedCareerRecord):
                continue
            try:
                event_type = CareerEventType(record.career_event_type)
            except ValueError:
                continue
            values = normalized.get(record.record_id, dict(record.original_values))
            events.append(
                CareerEvent(
                    record.record_id,
                    values.get("start_date"),
                    values.get("end_date"),
                    event_type,
                    values.get("description") or f"Imported {event_type.value} metadata",
                    record.provenance.source_id,
                    EvidenceLevel.UNKNOWN,
                    "Prepared for human review; no career fact was inferred.",
                )
            )
        return CareerTimeline(
            batch.batch_id,
            events=tuple(events),
            source_ids=tuple(dict.fromkeys(item.provenance.source_id for item in batch.records)),
            synthetic_only=batch.synthetic_only,
        )

    def prepare_evidence_records(self, batch: ImportBatch) -> EvidenceBundle:
        self._assert_private(batch)
        evidence_items: list[CareerEvidenceItem] = []
        confidence_map = {
            "UNKNOWN": EvidenceConfidenceLevel.UNKNOWN,
            "LOW": EvidenceConfidenceLevel.LOW,
            "MEDIUM": EvidenceConfidenceLevel.MEDIUM,
            "HIGH": EvidenceConfidenceLevel.HIGH,
        }
        for record in batch.records:
            if not isinstance(record, ImportedEvidence):
                continue
            try:
                source_type = EvidenceSourceType(record.source_type)
            except ValueError:
                source_type = EvidenceSourceType.OTHER_DOCUMENT
            try:
                status = EvidenceStatus(record.status)
            except ValueError:
                status = EvidenceStatus.UNVERIFIED
            evidence_items.append(
                CareerEvidenceItem(
                    EvidenceReference(
                        EvidenceId(record.evidence_id),
                        source_type,
                        "Imported evidence metadata",
                        record.reference,
                        record.provenance.origin,
                        version_date=record.provenance.imported_at,
                    ),
                    EvidenceAuthorityLevel.CONTEXTUAL,
                    confidence_map[record.provenance.confidence.value],
                    status,
                )
            )
        return EvidenceBundle(batch.batch_id, evidence=tuple(evidence_items), synthetic_only=batch.synthetic_only)

    @staticmethod
    def _record_conflict(left, right):
        if isinstance(left, ImportedEmploymentPeriod) and isinstance(right, ImportedEmploymentPeriod):
            if left.start_date == right.start_date and left.end_date == right.end_date and left.employer != right.employer:
                return ImportConflictType.INCOMPATIBLE_EMPLOYERS
            if left.employer == right.employer and (left.start_date, left.end_date) != (right.start_date, right.end_date):
                return ImportConflictType.INCOMPATIBLE_DATES
        if isinstance(left, ImportedClassification) and isinstance(right, ImportedClassification):
            if (left.start_date, left.end_date) == (right.start_date, right.end_date) and (left.classification, left.coefficient) != (right.classification, right.coefficient):
                return ImportConflictType.INCOMPATIBLE_CLASSIFICATIONS
        if isinstance(left, (ImportedNightWork, ImportedFiveShift)) and isinstance(right, type(left)):
            if (left.start_date, left.end_date) == (right.start_date, right.end_date) and left.schedule != right.schedule:
                return ImportConflictType.INCOMPATIBLE_SCHEDULES
        if isinstance(left, ImportedEvidence) and isinstance(right, ImportedEvidence):
            if left.evidence_id == right.evidence_id and (left.reference, left.status) != (right.reference, right.status):
                return ImportConflictType.CONTRADICTORY_EVIDENCE
        return None

    def _assert_private(self, batch: ImportBatch) -> None:
        require_privacy_gate(self._privacy_gate).assert_safe(batch)

    @staticmethod
    def _recommendations(validation, conflicts):
        recommendations = tuple(
            ImportRecommendation(f"recommendation:issue:{index}", "Review the reported structural issue without altering the original data.")
            for index, _ in enumerate(validation.issues, 1)
        )
        recommendations += tuple(
            ImportRecommendation(f"recommendation:conflict:{index}", "Review both conflicting sources; retain each provenance.")
            for index, _ in enumerate(conflicts, 1)
        )
        return recommendations or (
            ImportRecommendation("recommendation:review", "Perform human review before accepting prepared records."),
        )
