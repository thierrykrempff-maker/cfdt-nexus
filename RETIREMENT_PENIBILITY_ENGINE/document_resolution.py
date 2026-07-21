"""Central deterministic document ordering for career reconstruction."""

from __future__ import annotations

from .career_import_models import ImportConfidence, ImportDocumentType
from .career_reconstruction_models import DatePrecision, ReconstructionDate, ReconstructionRecord


DOCUMENT_TYPE_PRIORITY = {
    ImportDocumentType.EMPLOYMENT_CONTRACT: 0,
    ImportDocumentType.EMPLOYMENT_AMENDMENT: 0,
    ImportDocumentType.CAREER_STATEMENT: 1,
    ImportDocumentType.PAYSLIP: 2,
    ImportDocumentType.KELIO_EXPORT: 3,
}

_CONFIDENCE_PRIORITY = {
    ImportConfidence.HIGH: 0,
    ImportConfidence.MEDIUM: 1,
    ImportConfidence.LOW: 2,
    ImportConfidence.UNKNOWN: 3,
}


class DocumentResolutionStrategy:
    """Order evidence metadata without discarding conflicts or provenance."""

    def order(
        self, records: tuple[ReconstructionRecord, ...]
    ) -> tuple[ReconstructionRecord, ...]:
        return tuple(sorted(records, key=self.priority_key))

    def priority_key(self, record: ReconstructionRecord):
        provenance = record.provenance
        document_priority = min(
            (
                DOCUMENT_TYPE_PRIORITY.get(item.document_type, 4)
                for item in provenance
            ),
            default=5,
        )
        confidence_priority = min(
            (_CONFIDENCE_PRIORITY.get(item.confidence, 4) for item in provenance),
            default=5,
        )
        values = dict(record.values)
        coverage_priority = self._coverage_priority(
            values.get("start_date"), values.get("end_date")
        )
        provenance_key = tuple(
            sorted(
                (
                    item.source_id,
                    item.internal_document_id,
                    item.version,
                    item.origin,
                )
                for item in provenance
            )
        )
        return (
            document_priority,
            confidence_priority,
            coverage_priority,
            provenance_key,
            record.record_id,
        )

    @classmethod
    def preferred_values(
        cls, records: tuple[ReconstructionRecord, ...]
    ) -> tuple[tuple[str, object], ...]:
        keys = tuple(dict.fromkeys(key for record in records for key, _ in record.values))
        selected = []
        for key in keys:
            value = next(
                (
                    dict(record.values).get(key)
                    for record in records
                    if not cls._unknown(dict(record.values).get(key))
                ),
                None,
            )
            selected.append((key, value))
        return tuple(selected)

    @classmethod
    def _coverage_priority(cls, start, end):
        known_start = not cls._unknown(start)
        known_end = not cls._unknown(end)
        if known_start and known_end:
            return 0
        if known_start or known_end:
            return 1
        return 2

    @staticmethod
    def _unknown(value):
        return value is None or (
            isinstance(value, ReconstructionDate)
            and value.precision is DatePrecision.UNKNOWN
        )


__all__ = ("DOCUMENT_TYPE_PRIORITY", "DocumentResolutionStrategy")
