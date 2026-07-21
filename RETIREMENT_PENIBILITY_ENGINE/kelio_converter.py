"""Conversion from synthetic Kelio metadata to Career Import records."""

from .career_import_models import (
    ImportBatch,
    ImportConfidence,
    ImportDocumentType,
    ImportedEmploymentPeriod,
    ImportedEvidence,
    ImportedFiveShift,
    ImportedNightWork,
    ImportProvenance,
)
from .kelio_models import KelioConfidence, KelioExport, KelioImport
from .kelio_referential_models import KelioCounterResolution


class KelioReferentialResolutionError(ValueError):
    """Safe fail-closed error containing only a deterministic code."""


class KelioConverter:
    """Convert declared metadata without reading or parsing an export."""

    def __init__(self, referential_lookup) -> None:
        self._referential_lookup = referential_lookup

    def resolve_counters(
        self, export: KelioExport
    ) -> tuple[KelioCounterResolution, ...]:
        if self._referential_lookup is None:
            raise KelioReferentialResolutionError("KELIO_REFERENTIAL_REQUIRED")
        resolver = getattr(self._referential_lookup, "resolve_counter", None)
        if not callable(resolver):
            raise KelioReferentialResolutionError("KELIO_REFERENTIAL_INVALID")
        resolutions = []
        for counter in export.counters:
            try:
                resolution = resolver(counter.counter_id)
            except Exception:
                raise KelioReferentialResolutionError(
                    "KELIO_REFERENTIAL_LOOKUP_ERROR"
                ) from None
            if not isinstance(resolution, KelioCounterResolution):
                raise KelioReferentialResolutionError("KELIO_REFERENTIAL_INVALID")
            if not resolution.usable:
                raise KelioReferentialResolutionError(resolution.code)
            resolutions.append(resolution)
        return tuple(resolutions)

    def convert(self, export: KelioExport) -> KelioImport:
        resolutions = self.resolve_counters(export)
        provenance = self._provenance(export)
        records = [
            ImportedEmploymentPeriod(item.working_time_id, None, item.start_date, item.end_date, provenance)
            for item in export.working_times
        ]
        shifts = {item.shift_id: item for item in export.shifts}
        schedules_by_day = {
            item.working_day_id: next((schedule.label for schedule in export.schedules if schedule.schedule_id == item.schedule_id), None)
            for item in export.working_days
        }
        days_by_shift = {item.shift_id: item.working_day_id for item in export.shifts}
        for item in export.night_work:
            shift = shifts.get(item.shift_id)
            records.append(
                ImportedNightWork(
                    item.night_work_id,
                    shift.start_at.split("T", 1)[0] if shift else None,
                    shift.end_at.split("T", 1)[0] if shift else None,
                    schedules_by_day.get(days_by_shift.get(item.shift_id)),
                    provenance,
                )
            )
        schedules = {item.schedule_id: item.label for item in export.schedules}
        for item in export.five_shift:
            records.append(ImportedFiveShift(item.five_shift_id, item.start_date, item.end_date, schedules.get(item.schedule_id), provenance))
        for item in export.evidence:
            records.append(ImportedEvidence(item.evidence_id, "KELIO_EXPORT", "UNVERIFIED", item.opaque_reference, provenance))
        for resolution in resolutions:
            metadata = resolution.metadata
            records.append(
                ImportedEvidence(
                    f"kelio-counter:{metadata.canonical_counter_id}",
                    "KELIO_COUNTER",
                    "UNVERIFIED",
                    metadata.canonical_counter_id,
                    provenance,
                )
            )
        batch = ImportBatch(f"kelio:{export.metadata.export_id}", records=tuple(records), synthetic_only=True)
        return KelioImport(
            export.metadata.export_id,
            batch,
            tuple(item.record_id for item in records),
            resolutions,
        )

    @staticmethod
    def _provenance(export):
        confidence = {
            KelioConfidence.UNKNOWN: ImportConfidence.UNKNOWN,
            KelioConfidence.LOW: ImportConfidence.LOW,
            KelioConfidence.MEDIUM: ImportConfidence.MEDIUM,
            KelioConfidence.HIGH: ImportConfidence.HIGH,
        }[export.metadata.confidence]
        return ImportProvenance(
            f"kelio-source:{export.metadata.export_id}",
            ImportDocumentType.KELIO_EXPORT,
            export.metadata.source_reference,
            export.metadata.imported_at,
            export.metadata.version,
            "SYNTHETIC_KELIO_EXPORT",
            confidence,
        )


__all__ = ("KelioConverter", "KelioReferentialResolutionError")
