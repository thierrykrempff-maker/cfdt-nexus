"""Conversion of synthetic contract metadata into Career Import records."""

from .career_import_models import (
    ImportBatch,
    ImportConfidence,
    ImportDocumentType,
    ImportedCareerRecord,
    ImportedEmploymentPeriod,
    ImportedEvidence,
    ImportProvenance,
)
from .employment_contract_models import EmploymentConfidence, EmploymentContract, EmploymentImport


class EmploymentContractConverter:
    """Convert injected structured metadata without document access."""

    def convert(self, contract: EmploymentContract) -> EmploymentImport:
        provenance = self._provenance(contract)
        employer = contract.employer.label if contract.employer else None
        records = [
            ImportedEmploymentPeriod(item.period_id, employer, item.start_date, item.end_date, provenance)
            for item in contract.periods
        ]
        for item in contract.positions:
            records.append(self._record(item.position_id, "JOB_CHANGE", (("position", item.label), ("start_date", item.effective_date)), provenance))
        for item in contract.classifications:
            coefficient = next((value.value for value in contract.coefficients if value.classification_id == item.classification_id), None)
            records.append(self._record(item.classification_id, "CLASSIFICATION_CHANGE", (("classification", item.label), ("coefficient", coefficient), ("start_date", item.effective_date)), provenance))
        for item in contract.schedules:
            hours = next((value.declared_hours for value in contract.working_times if value.schedule_id == item.schedule_id), None)
            records.append(self._record(item.schedule_id, "SHIFT_WORK", (("schedule", item.label), ("declared_hours", hours), ("start_date", item.effective_date)), provenance))
        for item in contract.five_shift:
            records.append(self._record(item.five_shift_id, "FIVE_SHIFT", (("schedule_id", item.schedule_id), ("declared", str(item.declared))), provenance))
        for item in contract.night_work:
            records.append(self._record(item.night_work_id, "NIGHT_WORK", (("schedule", item.schedule_reference), ("declared", str(item.declared))), provenance))
        for item in contract.amendments:
            records.append(self._record(item.amendment_id, "CONTRACT_AMENDMENT", (("version", item.version), ("start_date", item.effective_date), ("changes", ",".join(item.change_types))), provenance))
        for item in contract.evidence:
            records.append(ImportedEvidence(item.evidence_id, "EMPLOYMENT_CONTRACT", "UNVERIFIED", item.opaque_reference, provenance))
        batch = ImportBatch(f"employment-contract:{contract.metadata.contract_id}", records=tuple(records), synthetic_only=True)
        return EmploymentImport(contract.metadata.contract_id, batch, tuple(item.record_id for item in records))

    @staticmethod
    def _record(identifier, event_type, values, provenance):
        return ImportedCareerRecord(identifier, event_type, tuple(values), provenance)

    @staticmethod
    def _provenance(contract):
        confidence = {
            EmploymentConfidence.UNKNOWN: ImportConfidence.UNKNOWN,
            EmploymentConfidence.LOW: ImportConfidence.LOW,
            EmploymentConfidence.MEDIUM: ImportConfidence.MEDIUM,
            EmploymentConfidence.HIGH: ImportConfidence.HIGH,
        }[contract.metadata.confidence]
        return ImportProvenance(
            f"employment-contract-source:{contract.metadata.contract_id}",
            ImportDocumentType.EMPLOYMENT_CONTRACT,
            contract.metadata.source_reference,
            contract.metadata.imported_at,
            contract.metadata.version,
            "SYNTHETIC_EMPLOYMENT_CONTRACT",
            confidence,
        )
