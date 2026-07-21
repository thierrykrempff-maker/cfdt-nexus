"""Structural validation for synthetic career-import batches."""

from __future__ import annotations

from dataclasses import fields
from datetime import date

from .career_import_models import (
    ImportBatch,
    ImportIssue,
    ImportIssueType,
    ImportValidation,
    ImportedEmploymentPeriod,
)


class CareerImportValidator:
    """Detect format and structural issues without business validation."""

    def validate(self, batch: ImportBatch) -> ImportValidation:
        issues: list[ImportIssue] = []
        seen_ids: set[str] = set()
        seen_signatures: dict[str, str] = {}
        dated_records: list[tuple[str, date]] = []

        for document in batch.documents:
            if not document.document_id or not document.source.source_id:
                issues.append(self._issue("document-required", ImportIssueType.REQUIRED_FIELD, (), "A document identifier and source are required."))
            if not document.complete:
                issues.append(self._issue(f"incomplete:{document.document_id}", ImportIssueType.INCOMPLETE_DOCUMENT, (), "The document metadata is incomplete."))

        for record in batch.records:
            record_id = getattr(record, "record_id", "")
            if not record_id:
                issues.append(self._issue("record-required", ImportIssueType.REQUIRED_FIELD, (), "A record identifier is required."))
            if record_id in seen_ids:
                issues.append(self._issue(f"duplicate-id:{record_id}", ImportIssueType.DUPLICATE, (record_id,), "Duplicate record identifier."))
            seen_ids.add(record_id)
            signature = repr(tuple((field.name, getattr(record, field.name)) for field in fields(record) if field.name != "record_id"))
            previous = seen_signatures.get(signature)
            if previous is not None:
                issues.append(self._issue(f"duplicate:{previous}:{record_id}", ImportIssueType.DUPLICATE, (previous, record_id), "Duplicate imported record."))
            else:
                seen_signatures[signature] = record_id
            parsed = self._validate_record_dates(record, issues)
            if parsed[0] is not None:
                dated_records.append((record_id, parsed[0]))
            for field in fields(record):
                value = getattr(record, field.name)
                if isinstance(value, str) and value.strip().upper() == "UNKNOWN":
                    issues.append(self._issue(f"unknown:{record_id}:{field.name}", ImportIssueType.UNKNOWN_VALUE, (record_id,), f"Unknown value for {field.name}."))

        if dated_records != sorted(dated_records, key=lambda item: item[1]):
            issues.append(self._issue("chronological-order", ImportIssueType.CHRONOLOGICAL_ORDER, tuple(item[0] for item in dated_records), "Records are not in chronological order."))
        self._detect_overlaps(batch, issues)
        return ImportValidation(not issues, tuple(issues))

    def _validate_record_dates(self, record, issues):
        parsed: dict[str, date] = {}
        for field in fields(record):
            value = getattr(record, field.name)
            if field.name.endswith("_date") and value:
                try:
                    parsed[field.name] = date.fromisoformat(value)
                except ValueError:
                    issues.append(self._issue(f"date:{record.record_id}:{field.name}", ImportIssueType.INVALID_DATE_FORMAT, (record.record_id,), f"Invalid ISO date in {field.name}."))
        start, end = parsed.get("start_date"), parsed.get("end_date")
        if start and end and end < start:
            issues.append(self._issue(f"period:{record.record_id}", ImportIssueType.INCOHERENT_PERIOD, (record.record_id,), "End date precedes start date."))
        return start, end

    def _detect_overlaps(self, batch: ImportBatch, issues: list[ImportIssue]) -> None:
        periods = tuple(item for item in batch.records if isinstance(item, ImportedEmploymentPeriod))
        for index, left in enumerate(periods):
            if not left.start_date or not left.end_date:
                continue
            try:
                left_start, left_end = date.fromisoformat(left.start_date), date.fromisoformat(left.end_date)
            except ValueError:
                continue
            for right in periods[index + 1 :]:
                if left.employer != right.employer or not right.start_date or not right.end_date:
                    continue
                try:
                    right_start, right_end = date.fromisoformat(right.start_date), date.fromisoformat(right.end_date)
                except ValueError:
                    continue
                if left_start <= right_end and right_start <= left_end:
                    issues.append(self._issue(f"overlap:{left.record_id}:{right.record_id}", ImportIssueType.OVERLAP, (left.record_id, right.record_id), "Employment periods overlap."))

    @staticmethod
    def _issue(issue_id, issue_type, record_ids, description):
        return ImportIssue(issue_id, issue_type, record_ids, description)
