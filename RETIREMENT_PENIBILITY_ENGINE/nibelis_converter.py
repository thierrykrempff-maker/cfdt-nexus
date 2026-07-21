"""Conversion from synthetic Nibelis metadata to Career Import records."""

from .career_import_models import (
    ImportBatch,
    ImportConfidence,
    ImportDocumentType,
    ImportedCareerRecord,
    ImportedEmploymentPeriod,
    ImportedEvidence,
    ImportProvenance,
)
from .nibelis_models import NibelisConfidence, NibelisExport, NibelisImport


class NibelisConverter:
    """Convert occurrences while retaining existing referential identifiers."""

    def convert(self, export: NibelisExport) -> NibelisImport:
        provenance = self._provenance(export)
        employer = export.employer.label if export.employer else None
        records = [
            ImportedEmploymentPeriod(item.period_id, employer, item.start_date, item.end_date, provenance)
            for item in export.periods
        ]
        for item in export.classifications:
            coefficient = next((value.value for value in export.coefficients if value.classification_id == item.classification_id), None)
            records.append(self._record(item.classification_id, "CLASSIFICATION_CHANGE", (("classification", item.label), ("coefficient", coefficient)), provenance))
        for item in export.salary_items:
            records.append(self._record(item.item_id, "NIBELIS_SALARY_ITEM", (("referential_rubric_id", item.referential_rubric_id), ("declared_amount", item.declared_amount), ("declared_base", item.declared_base), ("declared_rate", item.declared_rate), ("declared_quantity", item.declared_quantity)), provenance))
        for item in export.contributions:
            records.append(self._record(item.contribution_id, "NIBELIS_CONTRIBUTION", (("referential_rubric_id", item.referential_rubric_id), ("declared_amount", item.declared_amount)), provenance))
        for item in export.parameters:
            records.append(self._record(item.parameter_id, "NIBELIS_PARAMETER", (("referential_parameter_id", item.referential_parameter_id), ("declared_value", item.declared_value)), provenance))
        for item in export.evidence:
            records.append(ImportedEvidence(item.evidence_id, "NIBELIS_EXPORT", "UNVERIFIED", item.opaque_reference, provenance))
        batch = ImportBatch(f"nibelis:{export.metadata.export_id}", records=tuple(records), synthetic_only=True)
        return NibelisImport(export.metadata.export_id, batch, tuple(item.record_id for item in records))

    @staticmethod
    def _record(identifier, event_type, values, provenance):
        return ImportedCareerRecord(identifier, event_type, tuple(values), provenance)

    @staticmethod
    def _provenance(export):
        confidence = {
            NibelisConfidence.UNKNOWN: ImportConfidence.UNKNOWN,
            NibelisConfidence.LOW: ImportConfidence.LOW,
            NibelisConfidence.MEDIUM: ImportConfidence.MEDIUM,
            NibelisConfidence.HIGH: ImportConfidence.HIGH,
        }[export.metadata.confidence]
        return ImportProvenance(
            f"nibelis-source:{export.metadata.export_id}",
            ImportDocumentType.NIBELIS_EXPORT,
            export.metadata.source_reference,
            export.metadata.imported_at,
            export.metadata.version,
            "SYNTHETIC_NIBELIS_EXPORT",
            confidence,
        )
