"""Structural validation for synthetic career-statement metadata."""

from __future__ import annotations

from datetime import date

from .career_statement_models import (
    CareerStatement,
    CareerStatementConflict,
    CareerStatementIssue,
    CareerStatementPrecision,
    CareerStatementStatus,
    CareerStatementValidation,
    CareerStatementWarning,
)


class CareerStatementValidator:
    """Validate format and chronology without legal interpretation."""

    def validate(self, statement: CareerStatement) -> CareerStatementValidation:
        issues: list[CareerStatementIssue] = []
        warnings: list[CareerStatementWarning] = []
        conflicts: list[CareerStatementConflict] = []
        if not statement.metadata.statement_id:
            issues.append(self._issue("statement-id", "REQUIRED_FIELD", (), "Statement identifier is required."))
        if not statement.metadata.source_reference:
            issues.append(self._issue("source-reference", "MISSING_REFERENCE", (), "Source reference is required."))
        if not statement.metadata.imported_at:
            issues.append(self._issue("import-date", "REQUIRED_FIELD", (), "Import date is required."))
        if not statement.metadata.synthetic_only:
            issues.append(self._issue("synthetic", "REAL_DOCUMENT_PROHIBITED", (), "Only synthetic statements are accepted."))

        employer_ids = {item.employer_id for item in statement.employers}
        reference_ids = {item.reference_id for item in statement.references}
        self._duplicates("employer", (item.employer_id for item in statement.employers), conflicts)
        self._duplicates("employment", (item.employment_id for item in statement.employments), conflicts)
        self._duplicates("period", (item.period_id for item in statement.periods), conflicts)
        self._duplicates("reference", (item.reference_id for item in statement.references), conflicts)

        for item in statement.employments:
            if item.employer_id not in employer_ids:
                issues.append(self._issue(item.employment_id, "UNKNOWN_EMPLOYER", (item.employer_id,), "Employment references an unknown employer."))
            self._validate_period(item.employment_id, item.start_date, item.end_date, item.start_precision, item.end_precision, issues)
            self._validate_references(item.employment_id, item.reference_ids, reference_ids, issues)
        for item in statement.periods:
            if not item.period_type:
                issues.append(self._issue(item.period_id, "REQUIRED_FIELD", (item.period_id,), "Period type is required."))
            self._validate_period(item.period_id, item.start_date, item.end_date, item.start_precision, item.end_precision, issues)
            self._validate_references(item.period_id, item.reference_ids, reference_ids, issues)

        keys: dict[tuple[object, ...], str] = {}
        for item in statement.employments:
            key = (item.employer_id, item.start_date, item.end_date, item.start_precision, item.end_precision)
            if key in keys:
                conflicts.append(CareerStatementConflict(f"duplicate-employment:{keys[key]}:{item.employment_id}", "DUPLICATE", (keys[key], item.employment_id), "Possible duplicate employment retained."))
            else:
                keys[key] = item.employment_id

        if not statement.employments and not statement.periods:
            warnings.append(CareerStatementWarning("empty-periods", "Statement contains no declared career period."))
        valid = not issues and not conflicts
        status = CareerStatementStatus.VALID if valid else CareerStatementStatus.INVALID
        return CareerStatementValidation(valid, status, tuple(issues), tuple(warnings), tuple(conflicts))

    def _validate_period(self, identifier, start, end, start_precision, end_precision, issues):
        if start is None and end is None:
            issues.append(self._issue(identifier, "EMPTY_PERIOD", (identifier,), "Period has no declared date."))
            return
        parsed_start = self._validate_date(identifier, "start", start, start_precision, issues)
        parsed_end = self._validate_date(identifier, "end", end, end_precision, issues)
        if parsed_start and parsed_end and parsed_start > parsed_end:
            issues.append(self._issue(identifier, "CHRONOLOGICAL_ORDER", (identifier,), "Start date is after end date."))

    def _validate_date(self, identifier, field, value, precision, issues):
        if value is None or precision in {CareerStatementPrecision.UNKNOWN, CareerStatementPrecision.APPROXIMATE}:
            return None
        try:
            if precision is CareerStatementPrecision.EXACT:
                return date.fromisoformat(value)
            if precision is CareerStatementPrecision.MONTH_ONLY:
                if len(value) != 7:
                    raise ValueError
                return date.fromisoformat(value + "-01")
            if precision is CareerStatementPrecision.YEAR_ONLY:
                if len(value) != 4 or not value.isdigit():
                    raise ValueError
                return date(int(value), 1, 1)
        except (TypeError, ValueError):
            issues.append(self._issue(f"{identifier}:{field}", "INVALID_DATE_FORMAT", (identifier,), f"Invalid {field} date for declared precision."))
        return None

    @staticmethod
    def _validate_references(identifier, declared, known, issues):
        for reference_id in declared:
            if reference_id not in known:
                issues.append(CareerStatementValidator._issue(f"{identifier}:{reference_id}", "MISSING_REFERENCE", (identifier, reference_id), "Declared reference is missing."))

    @staticmethod
    def _duplicates(kind, identifiers, conflicts):
        seen = set()
        for identifier in identifiers:
            if identifier in seen:
                conflicts.append(CareerStatementConflict(f"duplicate-{kind}:{identifier}", "DUPLICATE_ID", (identifier,), f"Duplicate {kind} identifier retained."))
            seen.add(identifier)

    @staticmethod
    def _issue(issue_id, issue_type, subject_ids, description):
        return CareerStatementIssue(f"issue:{issue_id}", issue_type, tuple(subject_ids), description)
