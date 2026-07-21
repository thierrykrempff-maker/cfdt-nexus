"""Structural validator for synthetic contracts and amendments."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from .employment_contract_models import (
    EmploymentContract,
    EmploymentIssue,
    EmploymentStatus,
    EmploymentValidation,
    EmploymentWarning,
)


class EmploymentContractValidator:
    """Validate declared structure without interpreting employment law."""

    def validate(self, contract: EmploymentContract) -> EmploymentValidation:
        issues: list[EmploymentIssue] = []
        warnings: list[EmploymentWarning] = []
        if not contract.metadata.contract_id or not contract.metadata.source_reference or not contract.metadata.version:
            issues.append(self._issue("metadata", "REQUIRED_FIELD", (), "Contract identifier, source reference and version are required."))
        if not contract.metadata.synthetic_only:
            issues.append(self._issue("synthetic", "REAL_DOCUMENT_PROHIBITED", (), "Only synthetic contract metadata is accepted."))
        if contract.employer is None:
            issues.append(self._issue("employer", "MISSING_EMPLOYER", (), "A synthetic employer reference is required."))
        self._duplicates(contract, issues)

        site_ids = {item.site_id for item in contract.sites}
        period_ids = {item.period_id for item in contract.periods}
        classification_ids = {item.classification_id for item in contract.classifications}
        schedule_ids = {item.schedule_id for item in contract.schedules}
        evidence_ids = {item.evidence_id for item in contract.evidence}
        for site in contract.sites:
            if contract.employer and site.employer_id != contract.employer.employer_id:
                issues.append(self._issue(site.site_id, "EMPLOYER_MISMATCH", (site.site_id,), "Site references a different employer."))
        for period in contract.periods:
            if contract.employer and period.employer_id != contract.employer.employer_id:
                issues.append(self._issue(period.period_id, "EMPLOYER_MISMATCH", (period.period_id,), "Period references a different employer."))
            if period.site_id is not None and period.site_id not in site_ids:
                issues.append(self._issue(period.period_id, "UNKNOWN_SITE", (period.period_id,), "Period references an unknown site."))
            start = self._date(period.period_id, "start", period.start_date, issues)
            end = self._date(period.period_id, "end", period.end_date, issues)
            if start and end and start > end:
                issues.append(self._issue(period.period_id, "CHRONOLOGICAL_ORDER", (period.period_id,), "Period start date is after end date."))
        for position in contract.positions:
            self._period(position.position_id, position.period_id, period_ids, issues)
            self._required_label(position.position_id, position.label, "MISSING_POSITION", issues)
            self._date(position.position_id, "effective", position.effective_date, issues)
        for classification in contract.classifications:
            self._period(classification.classification_id, classification.period_id, period_ids, issues)
            self._required_label(classification.classification_id, classification.label, "MISSING_CLASSIFICATION", issues)
            self._date(classification.classification_id, "effective", classification.effective_date, issues)
        for coefficient in contract.coefficients:
            if coefficient.classification_id not in classification_ids:
                issues.append(self._issue(coefficient.coefficient_id, "UNKNOWN_CLASSIFICATION", (coefficient.coefficient_id,), "Coefficient references an unknown classification."))
            self._required_label(coefficient.coefficient_id, coefficient.value, "MISSING_COEFFICIENT", issues)
            self._date(coefficient.coefficient_id, "effective", coefficient.effective_date, issues)
        for schedule in contract.schedules:
            self._period(schedule.schedule_id, schedule.period_id, period_ids, issues)
            self._required_label(schedule.schedule_id, schedule.label, "MISSING_SCHEDULE", issues)
            self._date(schedule.schedule_id, "effective", schedule.effective_date, issues)
        for working_time in contract.working_times:
            if working_time.schedule_id not in schedule_ids:
                issues.append(self._issue(working_time.working_time_id, "UNKNOWN_SCHEDULE", (working_time.working_time_id,), "Working time references an unknown schedule."))
            self._non_negative(working_time.working_time_id, working_time.declared_hours, issues)
        for five_shift in contract.five_shift:
            if five_shift.schedule_id not in schedule_ids:
                issues.append(self._issue(five_shift.five_shift_id, "UNKNOWN_SCHEDULE", (five_shift.five_shift_id,), "Five-shift declaration references an unknown schedule."))
        for night_work in contract.night_work:
            self._period(night_work.night_work_id, night_work.period_id, period_ids, issues)
        self._amendments(contract, evidence_ids, issues)
        if not contract.periods:
            warnings.append(EmploymentWarning("missing-period", "No employment period was declared."))
        valid = not issues
        return EmploymentValidation(valid, EmploymentStatus.VALID if valid else EmploymentStatus.INVALID, tuple(issues), tuple(warnings))

    def _amendments(self, contract, evidence_ids, issues):
        known_versions = {contract.metadata.version}
        previous_version = contract.metadata.version
        previous_date = None
        for amendment in contract.amendments:
            if amendment.version in known_versions:
                issues.append(self._issue(amendment.amendment_id, "DUPLICATE_VERSION", (amendment.amendment_id,), "Amendment version is duplicated."))
            if amendment.supersedes_version != previous_version:
                issues.append(self._issue(amendment.amendment_id, "INVALID_VERSION_CHAIN", (amendment.amendment_id,), "Amendment does not supersede the preceding version."))
            effective = self._date(amendment.amendment_id, "effective", amendment.effective_date, issues)
            if previous_date and effective and effective < previous_date:
                issues.append(self._issue(amendment.amendment_id, "AMENDMENT_ORDER", (amendment.amendment_id,), "Amendments are not in chronological order."))
            for evidence_id in amendment.evidence_ids:
                if evidence_id not in evidence_ids:
                    issues.append(self._issue(amendment.amendment_id, "MISSING_EVIDENCE", (amendment.amendment_id, evidence_id), "Amendment evidence reference is missing."))
            if not amendment.change_types:
                issues.append(self._issue(amendment.amendment_id, "EMPTY_AMENDMENT", (amendment.amendment_id,), "Amendment declares no change type."))
            known_versions.add(amendment.version)
            previous_version = amendment.version
            previous_date = effective or previous_date

    def _duplicates(self, contract, issues):
        collections = (
            contract.sites, contract.periods, contract.positions, contract.classifications,
            contract.coefficients, contract.schedules, contract.working_times,
            contract.five_shift, contract.night_work, contract.amendments, contract.evidence,
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
            "position_id", "coefficient_id", "working_time_id", "five_shift_id",
            "night_work_id", "amendment_id", "evidence_id", "classification_id",
            "schedule_id", "period_id", "site_id",
        ):
            if hasattr(item, name):
                return getattr(item, name)
        raise ValueError("Unsupported employment-contract item.")

    @staticmethod
    def _date(identifier, field, value, issues):
        if value is None:
            issues.append(EmploymentContractValidator._issue(f"{identifier}:{field}", "MISSING_DATE", (identifier,), f"{field.title()} date is missing."))
            return None
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            issues.append(EmploymentContractValidator._issue(f"{identifier}:{field}", "INVALID_DATE", (identifier,), f"{field.title()} date is invalid."))
            return None

    @staticmethod
    def _period(identifier, period_id, known, issues):
        if period_id not in known:
            issues.append(EmploymentContractValidator._issue(identifier, "UNKNOWN_PERIOD", (identifier, period_id), "Item references an unknown employment period."))

    @staticmethod
    def _required_label(identifier, value, issue_type, issues):
        if not value:
            issues.append(EmploymentContractValidator._issue(identifier, issue_type, (identifier,), "Required declared value is missing."))

    @staticmethod
    def _non_negative(identifier, value, issues):
        try:
            if value is None or Decimal(value) < 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            issues.append(EmploymentContractValidator._issue(identifier, "INVALID_WORKING_TIME", (identifier,), "Working time must be a non-negative decimal string."))

    @staticmethod
    def _issue(issue_id, issue_type, subjects, description):
        return EmploymentIssue(f"issue:{issue_id}", issue_type, tuple(subjects), description)
