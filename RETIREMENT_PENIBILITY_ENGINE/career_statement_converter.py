"""Conversion of synthetic career-statement metadata into Career Import models."""

from __future__ import annotations

from .career_import_models import (
    ImportBatch,
    ImportConfidence,
    ImportDocumentType,
    ImportedCareerRecord,
    ImportedEmploymentPeriod,
    ImportedEvidence,
    ImportProvenance,
)
from .career_statement_models import (
    CareerStatement,
    CareerStatementConfidence,
    CareerStatementConversion,
)


class CareerStatementConverter:
    """Build immutable import metadata without reading or parsing documents."""

    def convert(self, statement: CareerStatement) -> CareerStatementConversion:
        provenance = self._provenance(statement)
        employers = {item.employer_id: item.label for item in statement.employers}
        records = []
        for item in statement.employments:
            records.append(ImportedEmploymentPeriod(item.employment_id, employers.get(item.employer_id), item.start_date, item.end_date, provenance))
        for item in statement.periods:
            records.append(
                ImportedCareerRecord(
                    item.period_id,
                    item.period_type,
                    (
                        ("start_date", item.start_date),
                        ("end_date", item.end_date),
                        ("start_precision", item.start_precision.value),
                        ("end_precision", item.end_precision.value),
                        ("description", item.description),
                    ),
                    provenance,
                )
            )
        for item in statement.references:
            records.append(ImportedEvidence(item.reference_id, "OFFICIAL_RETIREMENT_RECORD", "UNVERIFIED", item.opaque_reference, provenance))
        batch = ImportBatch(f"career-statement:{statement.metadata.statement_id}", records=tuple(records), synthetic_only=True)
        return CareerStatementConversion(statement.metadata.statement_id, batch, tuple(item.record_id for item in records))

    @staticmethod
    def _provenance(statement: CareerStatement) -> ImportProvenance:
        confidence = {
            CareerStatementConfidence.UNKNOWN: ImportConfidence.UNKNOWN,
            CareerStatementConfidence.LOW: ImportConfidence.LOW,
            CareerStatementConfidence.MEDIUM: ImportConfidence.MEDIUM,
            CareerStatementConfidence.HIGH: ImportConfidence.HIGH,
        }[statement.metadata.confidence]
        return ImportProvenance(
            f"career-statement-source:{statement.metadata.statement_id}",
            ImportDocumentType.CAREER_STATEMENT,
            statement.metadata.source_reference,
            statement.metadata.imported_at,
            statement.metadata.version,
            statement.metadata.source.value,
            confidence,
        )
