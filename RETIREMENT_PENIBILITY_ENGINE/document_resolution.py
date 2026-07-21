"""Central fact-aware documentary resolution for Career Reconstruction."""

from __future__ import annotations

from collections import Counter

from .career_import_models import ImportConfidence, ImportDocumentType
from .career_reconstruction_models import DatePrecision, ReconstructionDate, ReconstructionRecord
from .document_resolution_models import (
    DocumentRole,
    FactFamily,
    FactResolution,
    FactResolutionStatus,
)


# Compatibility map retained for callers of A6. A7 does not use it as a
# universal decision rule; each fact family has its own priority below.
DOCUMENT_TYPE_PRIORITY = {
    ImportDocumentType.EMPLOYMENT_CONTRACT: 0,
    ImportDocumentType.EMPLOYMENT_AMENDMENT: 0,
    ImportDocumentType.CAREER_STATEMENT: 1,
    ImportDocumentType.PAYSLIP: 2,
    ImportDocumentType.KELIO_EXPORT: 3,
}

DOCUMENT_ROLES = {
    ImportDocumentType.EMPLOYMENT_CONTRACT: DocumentRole.EMPLOYMENT_CONTRACT,
    ImportDocumentType.EMPLOYMENT_AMENDMENT: DocumentRole.EMPLOYMENT_AMENDMENT,
    ImportDocumentType.CAREER_STATEMENT: DocumentRole.CAREER_STATEMENT,
    ImportDocumentType.PAYSLIP: DocumentRole.PAYSLIP,
    ImportDocumentType.KELIO_EXPORT: DocumentRole.KELIO,
    ImportDocumentType.NIBELIS_EXPORT: DocumentRole.NIBELIS,
}

_DEFAULT_ROLES = tuple(DocumentRole)
_PRIORITY_BY_FACT = {
    FactFamily.EVENT_TYPE: _DEFAULT_ROLES,
    FactFamily.EMPLOYMENT_PERIOD: (
        DocumentRole.CAREER_STATEMENT,
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.PAYSLIP,
        DocumentRole.NIBELIS,
        DocumentRole.KELIO,
        DocumentRole.OTHER_EVIDENCE,
    ),
    FactFamily.CAREER_PERIOD: (
        DocumentRole.CAREER_STATEMENT,
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.PAYSLIP,
        DocumentRole.NIBELIS,
        DocumentRole.KELIO,
        DocumentRole.OTHER_EVIDENCE,
    ),
    FactFamily.EMPLOYER: (
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.CAREER_STATEMENT,
        DocumentRole.PAYSLIP,
        DocumentRole.NIBELIS,
        DocumentRole.KELIO,
        DocumentRole.OTHER_EVIDENCE,
    ),
    FactFamily.POSITION: (
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.PAYSLIP,
        DocumentRole.NIBELIS,
        DocumentRole.CAREER_STATEMENT,
        DocumentRole.KELIO,
        DocumentRole.OTHER_EVIDENCE,
    ),
    FactFamily.CLASSIFICATION: (
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.PAYSLIP,
        DocumentRole.NIBELIS,
        DocumentRole.CAREER_STATEMENT,
        DocumentRole.KELIO,
        DocumentRole.OTHER_EVIDENCE,
    ),
    FactFamily.CONTRACTUAL_CLASSIFICATION: (
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.PAYSLIP,
        DocumentRole.NIBELIS,
        DocumentRole.CAREER_STATEMENT,
        DocumentRole.KELIO,
        DocumentRole.OTHER_EVIDENCE,
    ),
    FactFamily.APPLIED_CLASSIFICATION: (
        DocumentRole.PAYSLIP,
        DocumentRole.NIBELIS,
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.CAREER_STATEMENT,
        DocumentRole.KELIO,
        DocumentRole.OTHER_EVIDENCE,
    ),
    FactFamily.COEFFICIENT: (
        DocumentRole.PAYSLIP,
        DocumentRole.NIBELIS,
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.CAREER_STATEMENT,
        DocumentRole.KELIO,
        DocumentRole.OTHER_EVIDENCE,
    ),
    FactFamily.WORKING_TIME: (
        DocumentRole.PAYSLIP,
        DocumentRole.KELIO,
        DocumentRole.NIBELIS,
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.CAREER_STATEMENT,
        DocumentRole.OTHER_EVIDENCE,
    ),
    FactFamily.RECORDED_WORKING_TIME: (
        DocumentRole.KELIO,
        DocumentRole.PAYSLIP,
        DocumentRole.NIBELIS,
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.CAREER_STATEMENT,
        DocumentRole.OTHER_EVIDENCE,
    ),
    FactFamily.NIGHT_WORK: (
        DocumentRole.KELIO,
        DocumentRole.PAYSLIP,
        DocumentRole.NIBELIS,
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.CAREER_STATEMENT,
        DocumentRole.OTHER_EVIDENCE,
    ),
    FactFamily.FIVE_SHIFT: (
        DocumentRole.KELIO,
        DocumentRole.PAYSLIP,
        DocumentRole.NIBELIS,
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.CAREER_STATEMENT,
        DocumentRole.OTHER_EVIDENCE,
    ),
    FactFamily.ON_CALL: (
        DocumentRole.KELIO,
        DocumentRole.PAYSLIP,
        DocumentRole.NIBELIS,
        DocumentRole.OTHER_EVIDENCE,
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.CAREER_STATEMENT,
    ),
    FactFamily.INTERVENTION: (
        DocumentRole.KELIO,
        DocumentRole.PAYSLIP,
        DocumentRole.NIBELIS,
        DocumentRole.OTHER_EVIDENCE,
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.CAREER_STATEMENT,
    ),
    FactFamily.LEAVE: (
        DocumentRole.KELIO,
        DocumentRole.PAYSLIP,
        DocumentRole.NIBELIS,
        DocumentRole.OTHER_EVIDENCE,
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.CAREER_STATEMENT,
    ),
    FactFamily.SALARY_ITEM: (
        DocumentRole.NIBELIS,
        DocumentRole.PAYSLIP,
        DocumentRole.OTHER_EVIDENCE,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.CAREER_STATEMENT,
        DocumentRole.KELIO,
    ),
    FactFamily.CONTRIBUTION: (
        DocumentRole.NIBELIS,
        DocumentRole.PAYSLIP,
        DocumentRole.OTHER_EVIDENCE,
        DocumentRole.EMPLOYMENT_CONTRACT,
        DocumentRole.EMPLOYMENT_AMENDMENT,
        DocumentRole.CAREER_STATEMENT,
        DocumentRole.KELIO,
    ),
    FactFamily.OTHER: _DEFAULT_ROLES,
}

_CONFIDENCE_PRIORITY = {
    ImportConfidence.HIGH: 0,
    ImportConfidence.MEDIUM: 1,
    ImportConfidence.LOW: 2,
    ImportConfidence.UNKNOWN: 3,
}

_FIELD_FAMILIES = {
    "career_event_type": FactFamily.EVENT_TYPE,
    "employer": FactFamily.EMPLOYER,
    "position": FactFamily.POSITION,
    "classification": FactFamily.CLASSIFICATION,
    "coefficient": FactFamily.COEFFICIENT,
    "schedule": FactFamily.WORKING_TIME,
    "declared_hours": FactFamily.WORKING_TIME,
    "night_work": FactFamily.NIGHT_WORK,
    "five_shift": FactFamily.FIVE_SHIFT,
    "on_call": FactFamily.ON_CALL,
    "intervention": FactFamily.INTERVENTION,
    "absence_type": FactFamily.LEAVE,
    "leave": FactFamily.LEAVE,
    "salary_item": FactFamily.SALARY_ITEM,
    "referential_rubric_id": FactFamily.SALARY_ITEM,
    "contribution": FactFamily.CONTRIBUTION,
}


class DocumentResolutionStrategy:
    """Resolve each fact with its own documentary role priorities."""

    def order(
        self,
        records: tuple[ReconstructionRecord, ...],
        fact_family: FactFamily | None = None,
    ) -> tuple[ReconstructionRecord, ...]:
        if fact_family is None:
            return tuple(sorted(records, key=self._legacy_priority_key))
        return tuple(sorted(records, key=lambda record: self.priority_key(record, fact_family)))

    def resolve(
        self,
        field_name: str,
        records: tuple[ReconstructionRecord, ...],
    ) -> FactResolution:
        family = self.fact_family(field_name, records)
        candidates = tuple(
            record
            for record in records
            if not self._unknown(dict(record.values).get(field_name))
        )
        candidate_values = tuple(
            dict(record.values)[field_name] for record in candidates
        )
        ordered = tuple(
            sorted(
                candidates,
                key=lambda record: self.resolution_rank(
                    record, family, field_name, candidate_values
                )
                + (self._provenance_key(record), record.record_id),
            )
        )
        provenance = tuple(
            dict.fromkeys(item for record in ordered for item in record.provenance)
        )
        roles = tuple(dict.fromkeys(self.document_role(item.document_type) for item in provenance))
        confidences = tuple(dict.fromkeys(item.confidence for item in provenance))
        if not ordered:
            return FactResolution(
                field_name,
                family,
                FactResolutionStatus.INSUFFICIENT_EVIDENCE,
                None,
                None,
                (),
                roles,
                confidences,
                provenance,
                "No explicit value is available.",
            )

        values = tuple(dict(record.values)[field_name] for record in ordered)
        unique = tuple(dict.fromkeys(values))
        if family is FactFamily.EVENT_TYPE and len(unique) > 1:
            return self._result(
                field_name,
                family,
                FactResolutionStatus.CONFLICT,
                None,
                ordered,
                provenance,
                "Different career event types cannot be merged.",
            )
        if family is FactFamily.OTHER and len(unique) > 1:
            return self._result(
                field_name,
                family,
                FactResolutionStatus.UNSUPPORTED_FACT_TYPE,
                None,
                ordered,
                provenance,
                "The fact type has no explicit documentary resolution policy.",
            )
        if len(unique) == 1:
            return self._result(
                field_name,
                family,
                FactResolutionStatus.RESOLVED,
                unique[0],
                ordered,
                provenance,
                "All explicit evidence agrees.",
            )

        competing = next(
            record
            for record in ordered[1:]
            if dict(record.values)[field_name] != values[0]
        )
        first_rank = self.resolution_rank(ordered[0], family, field_name, values)
        second_rank = self.resolution_rank(competing, family, field_name, values)
        if first_rank < second_rank:
            return self._result(
                field_name,
                family,
                FactResolutionStatus.RESOLVED_WITH_WARNINGS,
                values[0],
                ordered,
                provenance,
                "A fact-specific priority selects one value; alternatives require review.",
            )
        return self._result(
            field_name,
            family,
            FactResolutionStatus.CONFLICT,
            None,
            ordered,
            provenance,
            "Evidence has equal resolution rank and remains contradictory.",
        )

    def fact_family(
        self,
        field_name: str,
        records: tuple[ReconstructionRecord, ...],
    ) -> FactFamily:
        if field_name == "classification":
            nature = {
                str(dict(record.values).get("classification_nature") or "").upper()
                for record in records
            }
            if "CONTRACTUAL" in nature:
                return FactFamily.CONTRACTUAL_CLASSIFICATION
            if "APPLIED" in nature:
                return FactFamily.APPLIED_CLASSIFICATION
        if field_name in {"schedule", "declared_hours"}:
            nature = {
                str(dict(record.values).get("working_time_nature") or "").upper()
                for record in records
            }
            if "RECORDED" in nature:
                return FactFamily.RECORDED_WORKING_TIME
        if field_name in {"start_date", "end_date"}:
            if any(record.record_type == "ImportedEmploymentPeriod" for record in records):
                return FactFamily.EMPLOYMENT_PERIOD
            if any(
                self.document_role(item.document_type) is DocumentRole.CAREER_STATEMENT
                for record in records
                for item in record.provenance
            ):
                return FactFamily.CAREER_PERIOD
            return FactFamily.EMPLOYMENT_PERIOD
        return _FIELD_FAMILIES.get(field_name, FactFamily.OTHER)

    def priority_key(self, record: ReconstructionRecord, family: FactFamily):
        rank = self.resolution_rank(record, family, None, ())
        return rank + (self._provenance_key(record), record.record_id)

    def resolution_rank(
        self,
        record: ReconstructionRecord,
        family: FactFamily,
        field_name: str | None,
        values: tuple[object, ...],
    ) -> tuple[int, int, int, int]:
        roles = _PRIORITY_BY_FACT.get(family, _DEFAULT_ROLES)
        role_rank = {role: index for index, role in enumerate(roles)}
        document_priority = min(
            (
                role_rank.get(self.document_role(item.document_type), len(roles))
                for item in record.provenance
            ),
            default=len(roles) + 1,
        )
        confidence_priority = min(
            (_CONFIDENCE_PRIORITY.get(item.confidence, 4) for item in record.provenance),
            default=5,
        )
        value = dict(record.values).get(field_name) if field_name else None
        precision_priority = self._precision_priority(value)
        coverage_priority = self._coverage_priority(
            dict(record.values).get("start_date"),
            dict(record.values).get("end_date"),
        )
        corroboration = -Counter(values).get(value, 0) if field_name else 0
        return (
            document_priority,
            confidence_priority,
            precision_priority,
            coverage_priority + corroboration,
        )

    def _legacy_priority_key(self, record: ReconstructionRecord):
        provenance = record.provenance
        document_priority = min(
            (DOCUMENT_TYPE_PRIORITY.get(item.document_type, 4) for item in provenance),
            default=5,
        )
        confidence_priority = min(
            (_CONFIDENCE_PRIORITY.get(item.confidence, 4) for item in provenance),
            default=5,
        )
        values = dict(record.values)
        return (
            document_priority,
            confidence_priority,
            self._coverage_priority(values.get("start_date"), values.get("end_date")),
            self._provenance_key(record),
            record.record_id,
        )

    @classmethod
    def preferred_values(
        cls, records: tuple[ReconstructionRecord, ...]
    ) -> tuple[tuple[str, object], ...]:
        strategy = cls()
        keys = tuple(dict.fromkeys(key for record in records for key, _ in record.values))
        return tuple((key, strategy.resolve(key, records).selected_value) for key in keys)

    @staticmethod
    def document_role(document_type: ImportDocumentType) -> DocumentRole:
        return DOCUMENT_ROLES.get(document_type, DocumentRole.OTHER_EVIDENCE)

    @staticmethod
    def _result(field_name, family, status, value, ordered, provenance, explanation):
        return FactResolution(
            field_name,
            family,
            status,
            value,
            ordered[0].record_id if value is not None else None,
            tuple(record.record_id for record in ordered),
            tuple(
                dict.fromkeys(
                    DocumentResolutionStrategy.document_role(item.document_type)
                    for item in provenance
                )
            ),
            tuple(dict.fromkeys(item.confidence for item in provenance)),
            provenance,
            explanation,
        )

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
    def _precision_priority(value):
        if isinstance(value, ReconstructionDate):
            return {
                DatePrecision.EXACT: 0,
                DatePrecision.MONTH_ONLY: 1,
                DatePrecision.YEAR_ONLY: 2,
                DatePrecision.APPROXIMATE: 3,
                DatePrecision.UNKNOWN: 4,
            }[value.precision]
        return 0

    @staticmethod
    def _provenance_key(record):
        return tuple(
            sorted(
                (item.source_id, item.internal_document_id, item.version, item.origin)
                for item in record.provenance
            )
        )

    @staticmethod
    def _unknown(value):
        return value is None or (
            isinstance(value, ReconstructionDate)
            and value.precision is DatePrecision.UNKNOWN
        )


__all__ = (
    "DOCUMENT_ROLES",
    "DOCUMENT_TYPE_PRIORITY",
    "DocumentResolutionStrategy",
)
