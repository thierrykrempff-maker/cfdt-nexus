"""Structural validator using injected existing Nibelis referential IDs."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from .nibelis_models import NibelisExport, NibelisIssue, NibelisStatus, NibelisValidation, NibelisWarning


class NibelisValidator:
    """Validate export occurrences without reproducing the rubric taxonomy."""

    def __init__(self, referential_lookup=None):
        self._referential_lookup = referential_lookup

    def validate(self, export: NibelisExport) -> NibelisValidation:
        issues: list[NibelisIssue] = []
        warnings: list[NibelisWarning] = []
        if not export.metadata.export_id or not export.metadata.source_reference:
            issues.append(self._issue("metadata", "REQUIRED_FIELD", (), "Export identifier and source reference are required."))
        if not export.metadata.synthetic_only:
            issues.append(self._issue("synthetic", "REAL_EXPORT_PROHIBITED", (), "Only synthetic Nibelis metadata is accepted."))
        if export.employer is None:
            issues.append(self._issue("employer", "MISSING_EMPLOYER", (), "A synthetic employer reference is required."))
        self._duplicates(export, issues)
        period_ids = {item.period_id for item in export.periods}
        classification_ids = {item.classification_id for item in export.classifications}
        for period in export.periods:
            if export.employer and period.employer_id != export.employer.employer_id:
                issues.append(self._issue(period.period_id, "EMPLOYER_MISMATCH", (period.period_id,), "Payroll period references a different employer."))
            start, end = self._date(period.period_id, "start", period.start_date, issues), self._date(period.period_id, "end", period.end_date, issues)
            if start and end and start > end:
                issues.append(self._issue(period.period_id, "CHRONOLOGICAL_ORDER", (period.period_id,), "Payroll period start is after its end."))
        referential_items = export.salary_items + export.contributions
        if (referential_items or export.parameters) and self._referential_lookup is None:
            issues.append(self._issue("referential", "REFERENTIAL_LOOKUP_REQUIRED", (), "Existing Nibelis and payroll-parameter referentials must be injected."))
        for item in export.salary_items:
            self._period(item.item_id, item.period_id, period_ids, issues)
            self._rubric(item.item_id, item.referential_rubric_id, issues)
            self._numbers(item.item_id, (item.declared_amount, item.declared_base, item.declared_rate, item.declared_quantity), issues)
        for item in export.contributions:
            self._period(item.contribution_id, item.period_id, period_ids, issues)
            self._rubric(item.contribution_id, item.referential_rubric_id, issues)
            self._numbers(item.contribution_id, (item.declared_amount,), issues)
        for item in export.parameters:
            self._period(item.parameter_id, item.period_id, period_ids, issues)
            if not item.referential_parameter_id:
                issues.append(self._issue(item.parameter_id, "MISSING_PARAMETER_REFERENCE", (item.parameter_id,), "Payroll parameter reference is required."))
            elif self._referential_lookup and not self._referential_lookup.contains_parameter(item.referential_parameter_id):
                issues.append(self._issue(item.parameter_id, "UNKNOWN_PARAMETER_REFERENCE", (item.parameter_id,), "Payroll parameter is absent from the injected existing referential."))
        for item in export.classifications:
            self._period(item.classification_id, item.period_id, period_ids, issues)
            if not item.label:
                issues.append(self._issue(item.classification_id, "MISSING_CLASSIFICATION", (item.classification_id,), "Classification is missing."))
        for item in export.coefficients:
            if item.classification_id not in classification_ids:
                issues.append(self._issue(item.coefficient_id, "UNKNOWN_CLASSIFICATION", (item.coefficient_id,), "Coefficient references an unknown classification."))
            if not item.value:
                issues.append(self._issue(item.coefficient_id, "MISSING_COEFFICIENT", (item.coefficient_id,), "Coefficient is missing."))
        if not export.periods:
            warnings.append(NibelisWarning("missing-period", "No payroll period was declared."))
        valid = not issues
        return NibelisValidation(valid, NibelisStatus.VALID if valid else NibelisStatus.INVALID, tuple(issues), tuple(warnings))

    def _rubric(self, identifier, rubric_id, issues):
        if not rubric_id:
            issues.append(self._issue(identifier, "MISSING_RUBRIC_REFERENCE", (identifier,), "Existing Nibelis rubric identifier is required."))
        elif self._referential_lookup and not self._referential_lookup.contains_rubric(rubric_id):
            issues.append(self._issue(identifier, "UNKNOWN_RUBRIC_REFERENCE", (identifier,), "Rubric is absent from the injected existing Nibelis referential."))

    def _duplicates(self, export, issues):
        collections = (
            export.periods, export.salary_items, export.contributions, export.parameters,
            export.classifications, export.coefficients, export.evidence,
        )
        seen = set()
        for collection in collections:
            for item in collection:
                identifier = self._identifier(item)
                if identifier in seen:
                    issues.append(self._issue(identifier, "DUPLICATE", (identifier,), "Duplicate identifier retained for review."))
                seen.add(identifier)

    @staticmethod
    def _identifier(item):
        for name in (
            "item_id", "contribution_id", "parameter_id", "coefficient_id",
            "evidence_id", "classification_id", "period_id",
        ):
            if hasattr(item, name):
                return getattr(item, name)
        raise ValueError("Unsupported Nibelis item.")

    @staticmethod
    def _date(identifier, field, value, issues):
        if value is None:
            issues.append(NibelisValidator._issue(f"{identifier}:{field}", "MISSING_DATE", (identifier,), f"Payroll period {field} date is missing."))
            return None
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            issues.append(NibelisValidator._issue(f"{identifier}:{field}", "INVALID_DATE", (identifier,), f"Payroll period {field} date is invalid."))
            return None

    @staticmethod
    def _period(identifier, period_id, known, issues):
        if period_id not in known:
            issues.append(NibelisValidator._issue(identifier, "UNKNOWN_PERIOD", (identifier, period_id), "Payroll occurrence references an unknown period."))

    @staticmethod
    def _numbers(identifier, values, issues):
        for value in values:
            if value is None:
                continue
            try:
                Decimal(value)
            except (InvalidOperation, ValueError):
                issues.append(NibelisValidator._issue(identifier, "INVALID_DECLARED_VALUE", (identifier,), "Declared payroll value must be a decimal string."))
                return

    @staticmethod
    def _issue(issue_id, issue_type, subjects, description):
        return NibelisIssue(f"issue:{issue_id}", issue_type, tuple(subjects), description)
