"""Structural validation of injected synthetic payslip metadata."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from .payslip_models import Payslip, PayslipIssue, PayslipStatus, PayslipValidation, PayslipWarning


class PayslipValidator:
    """Check structure and coherence without payroll or legal validation."""

    def validate(self, payslip: Payslip) -> PayslipValidation:
        issues: list[PayslipIssue] = []
        warnings: list[PayslipWarning] = []
        if not payslip.metadata.payslip_id or not payslip.metadata.source_reference:
            issues.append(self._issue("metadata", "REQUIRED_FIELD", (), "Payslip identifier and source reference are required."))
        if not payslip.metadata.synthetic_only:
            issues.append(self._issue("synthetic", "REAL_PAYSLIP_PROHIBITED", (), "Only synthetic payslip metadata is accepted."))
        if not payslip.employee.anonymized or not payslip.employee.synthetic_employee_id:
            issues.append(self._issue("employee", "IDENTITY_PROHIBITED", (), "An anonymous synthetic employee reference is required."))
        if payslip.employer is None:
            issues.append(self._issue("employer", "MISSING_EMPLOYER", (), "A synthetic employer reference is required."))

        period_ids = {item.period_id for item in payslip.periods}
        classification_ids = {item.classification_id for item in payslip.classifications}
        self._check_duplicates(payslip, issues)
        for item in payslip.periods:
            if payslip.employer and item.employer_id != payslip.employer.employer_id:
                issues.append(self._issue(item.period_id, "EMPLOYER_MISMATCH", (item.period_id,), "Period employer does not match the payslip employer."))
            start, end = self._date(item.period_id, "start", item.start_date, issues), self._date(item.period_id, "end", item.end_date, issues)
            if start and end and start > end:
                issues.append(self._issue(item.period_id, "CHRONOLOGICAL_ORDER", (item.period_id,), "Period start date is after end date."))
        for item in payslip.classifications:
            self._require_period(item.classification_id, item.period_id, period_ids, issues)
            if not item.label:
                issues.append(self._issue(item.classification_id, "MISSING_CLASSIFICATION", (item.classification_id,), "Classification label is missing."))
        for item in payslip.coefficients:
            if item.classification_id not in classification_ids:
                issues.append(self._issue(item.coefficient_id, "UNKNOWN_CLASSIFICATION", (item.coefficient_id,), "Coefficient references an unknown classification."))
            if not item.value:
                issues.append(self._issue(item.coefficient_id, "MISSING_COEFFICIENT", (item.coefficient_id,), "Coefficient value is missing."))
        for collection in (payslip.working_times, payslip.night_work, payslip.five_shift, payslip.absences, payslip.overtime):
            for item in collection:
                self._require_period(self._identifier(item), item.period_id, period_ids, issues)
        for item in payslip.working_times:
            self._non_negative(item.working_time_id, item.declared_hours, "INVALID_WORKING_TIME", issues)
        for item in payslip.night_work:
            self._non_negative(item.night_work_id, item.declared_hours, "INVALID_NIGHT_WORK", issues)
        for item in payslip.overtime:
            self._non_negative(item.overtime_id, item.declared_hours, "INVALID_OVERTIME", issues)
        for item in payslip.salary_items:
            if not item.code and not item.label:
                issues.append(self._issue(item.item_id, "INVALID_PAYROLL_ITEM", (item.item_id,), "Salary item requires a code or label."))
        for item in payslip.contributions:
            if not item.code and not item.label:
                issues.append(self._issue(item.contribution_id, "INVALID_CONTRIBUTION", (item.contribution_id,), "Contribution requires a code or label."))
        if not payslip.periods:
            warnings.append(PayslipWarning("missing-period", "No payroll period was declared."))
        valid = not issues
        return PayslipValidation(valid, PayslipStatus.VALID if valid else PayslipStatus.INVALID, tuple(issues), tuple(warnings))

    def _check_duplicates(self, payslip, issues):
        collections = (
            payslip.periods, payslip.working_times, payslip.night_work, payslip.five_shift,
            payslip.classifications, payslip.coefficients, payslip.salary_items,
            payslip.contributions, payslip.absences, payslip.overtime, payslip.evidence,
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
            "working_time_id", "night_work_id", "five_shift_id", "coefficient_id",
            "item_id", "contribution_id", "absence_id", "overtime_id", "evidence_id",
            "classification_id", "period_id",
        ):
            if hasattr(item, name):
                return getattr(item, name)
        raise ValueError("Unsupported payslip item.")

    @staticmethod
    def _date(identifier, field, value, issues):
        if value is None:
            issues.append(PayslipValidator._issue(f"{identifier}:{field}", "MISSING_DATE", (identifier,), f"Period {field} date is missing."))
            return None
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            issues.append(PayslipValidator._issue(f"{identifier}:{field}", "INVALID_DATE", (identifier,), f"Period {field} date is invalid."))
            return None

    @staticmethod
    def _non_negative(identifier, value, issue_type, issues):
        if value is None:
            return
        try:
            if Decimal(value) < 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            issues.append(PayslipValidator._issue(identifier, issue_type, (identifier,), "Declared duration must be a non-negative decimal string."))

    @staticmethod
    def _require_period(identifier, period_id, known, issues):
        if period_id not in known:
            issues.append(PayslipValidator._issue(identifier, "UNKNOWN_PERIOD", (identifier, period_id), "Item references an unknown payroll period."))

    @staticmethod
    def _issue(issue_id, issue_type, subjects, description):
        return PayslipIssue(f"issue:{issue_id}", issue_type, tuple(subjects), description)
