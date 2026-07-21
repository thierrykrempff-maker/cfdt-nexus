"""Conversion from synthetic payslip metadata to Career Import records."""

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
from .payslip_models import Payslip, PayslipConfidence, PayslipImport


class PayslipConverter:
    """Convert declared metadata without reading a payslip or computing values."""

    def convert(self, payslip: Payslip) -> PayslipImport:
        provenance = self._provenance(payslip)
        employer = payslip.employer.label if payslip.employer else None
        records = [
            ImportedEmploymentPeriod(item.period_id, employer, item.start_date, item.end_date, provenance)
            for item in payslip.periods
        ]
        for item in payslip.classifications:
            coefficient = next((value.value for value in payslip.coefficients if value.classification_id == item.classification_id), None)
            records.append(self._record(item.classification_id, "CLASSIFICATION_CHANGE", (("classification", item.label), ("coefficient", coefficient)), provenance))
        for item in payslip.working_times:
            records.append(self._record(item.working_time_id, "SHIFT_WORK", (("schedule", item.schedule_label), ("declared_hours", item.declared_hours)), provenance))
        for item in payslip.night_work:
            records.append(self._record(item.night_work_id, "NIGHT_WORK", (("declared_hours", item.declared_hours), ("declared", str(item.declared))), provenance))
        for item in payslip.five_shift:
            records.append(self._record(item.five_shift_id, "FIVE_SHIFT", (("schedule", item.schedule_label), ("declared", str(item.declared))), provenance))
        for item in payslip.absences:
            records.append(self._record(item.absence_id, "ABSENCE", (("absence_type", item.absence_type), ("declared_duration", item.declared_duration)), provenance))
        for item in payslip.overtime:
            records.append(self._record(item.overtime_id, "OVERTIME", (("declared_hours", item.declared_hours), ("rate_label", item.rate_label)), provenance))
        for item in payslip.evidence:
            records.append(ImportedEvidence(item.evidence_id, "PAYSLIP", "UNVERIFIED", item.opaque_reference, provenance))
        batch = ImportBatch(f"payslip:{payslip.metadata.payslip_id}", records=tuple(records), synthetic_only=True)
        return PayslipImport(payslip.metadata.payslip_id, batch, tuple(item.record_id for item in records))

    @staticmethod
    def _record(identifier, event_type, values, provenance):
        return ImportedCareerRecord(identifier, event_type, tuple(values), provenance)

    @staticmethod
    def _provenance(payslip):
        confidence = {
            PayslipConfidence.UNKNOWN: ImportConfidence.UNKNOWN,
            PayslipConfidence.LOW: ImportConfidence.LOW,
            PayslipConfidence.MEDIUM: ImportConfidence.MEDIUM,
            PayslipConfidence.HIGH: ImportConfidence.HIGH,
        }[payslip.metadata.confidence]
        return ImportProvenance(
            f"payslip-source:{payslip.metadata.payslip_id}",
            ImportDocumentType.PAYSLIP,
            payslip.metadata.source_reference,
            payslip.metadata.imported_at,
            payslip.metadata.version,
            "SYNTHETIC_PAYSLIP",
            confidence,
        )
