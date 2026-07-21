"""Structural validation of injected synthetic Kelio metadata."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from .kelio_models import KelioExport, KelioIssue, KelioStatus, KelioValidation, KelioWarning


class KelioValidator:
    """Validate schedules and references without legal interpretation."""

    def validate(self, export: KelioExport) -> KelioValidation:
        issues: list[KelioIssue] = []
        warnings: list[KelioWarning] = []
        if not export.metadata.export_id or not export.metadata.source_reference:
            issues.append(self._issue("metadata", "REQUIRED_FIELD", (), "Export identifier and source reference are required."))
        if not export.metadata.synthetic_only:
            issues.append(self._issue("synthetic", "REAL_EXPORT_PROHIBITED", (), "Only synthetic Kelio metadata is accepted."))
        if not export.employee.anonymized or not export.employee.synthetic_employee_id:
            issues.append(self._issue("employee", "IDENTITY_PROHIBITED", (), "An anonymous synthetic employee reference is required."))
        self._duplicates(export, issues)
        schedule_ids = {item.schedule_id for item in export.schedules}
        day_ids = {item.working_day_id for item in export.working_days}
        shift_ids = {item.shift_id for item in export.shifts}
        on_call_ids = {item.on_call_id for item in export.on_calls}
        for schedule in export.schedules:
            if not schedule.label:
                issues.append(self._issue(schedule.schedule_id, "MISSING_SCHEDULE", (schedule.schedule_id,), "Schedule label is missing."))
            self._date(schedule.schedule_id, schedule.effective_date, issues)
        seen_dates = {}
        for day in export.working_days:
            parsed = self._date(day.working_day_id, day.date, issues)
            if day.schedule_id not in schedule_ids:
                issues.append(self._issue(day.working_day_id, "UNKNOWN_SCHEDULE", (day.working_day_id,), "Working day references an unknown schedule."))
            if parsed in seen_dates:
                issues.append(self._issue(day.working_day_id, "DUPLICATE_WORKING_DAY", (seen_dates[parsed], day.working_day_id), "Multiple working days share the same date."))
            elif parsed:
                seen_dates[parsed] = day.working_day_id
        shifts_by_day = {}
        for shift in export.shifts:
            if shift.working_day_id not in day_ids:
                issues.append(self._issue(shift.shift_id, "UNKNOWN_WORKING_DAY", (shift.shift_id,), "Shift references an unknown working day."))
            start, end = self._datetime(shift.shift_id, "start", shift.start_at, issues), self._datetime(shift.shift_id, "end", shift.end_at, issues)
            if start and end and start >= end:
                issues.append(self._issue(shift.shift_id, "INVALID_SHIFT_ORDER", (shift.shift_id,), "Shift start must precede its end."))
            shifts_by_day.setdefault(shift.working_day_id, []).append((start, end, shift.shift_id))
        for values in shifts_by_day.values():
            ordered = sorted((item for item in values if item[0] and item[1]), key=lambda item: item[0])
            for left, right in zip(ordered, ordered[1:]):
                if left[1] > right[0]:
                    issues.append(self._issue(right[2], "OVERLAPPING_SHIFT", (left[2], right[2]), "Declared shifts overlap."))
        for night in export.night_work:
            if night.shift_id not in shift_ids:
                issues.append(self._issue(night.night_work_id, "UNKNOWN_SHIFT", (night.night_work_id,), "Night work references an unknown shift."))
            self._non_negative(night.night_work_id, night.declared_duration, "INVALID_NIGHT_WORK", issues)
        for five in export.five_shift:
            if five.schedule_id not in schedule_ids:
                issues.append(self._issue(five.five_shift_id, "UNKNOWN_SCHEDULE", (five.five_shift_id,), "Five-shift period references an unknown schedule."))
            self._date_range(five.five_shift_id, five.start_date, five.end_date, issues)
        on_calls = {}
        for on_call in export.on_calls:
            start, end = self._datetime(on_call.on_call_id, "start", on_call.start_at, issues), self._datetime(on_call.on_call_id, "end", on_call.end_at, issues)
            if start and end and start >= end:
                issues.append(self._issue(on_call.on_call_id, "INVALID_ON_CALL", (on_call.on_call_id,), "On-call start must precede its end."))
            on_calls[on_call.on_call_id] = (start, end)
        for intervention in export.interventions:
            if intervention.on_call_id not in on_call_ids:
                issues.append(self._issue(intervention.intervention_id, "UNKNOWN_ON_CALL", (intervention.intervention_id,), "Intervention references an unknown on-call period."))
            start, end = self._datetime(intervention.intervention_id, "start", intervention.start_at, issues), self._datetime(intervention.intervention_id, "end", intervention.end_at, issues)
            if start and end and start >= end:
                issues.append(self._issue(intervention.intervention_id, "INVALID_INTERVENTION", (intervention.intervention_id,), "Intervention start must precede its end."))
            parent = on_calls.get(intervention.on_call_id)
            if parent and all(parent) and start and end and not (parent[0] <= start <= end <= parent[1]):
                issues.append(self._issue(intervention.intervention_id, "INTERVENTION_OUTSIDE_ON_CALL", (intervention.intervention_id,), "Intervention lies outside its on-call period."))
        for leave in export.leaves:
            self._date_range(leave.leave_id, leave.start_date, leave.end_date, issues)
            if not leave.leave_type:
                issues.append(self._issue(leave.leave_id, "MISSING_LEAVE_TYPE", (leave.leave_id,), "Leave type is missing."))
        for working_time in export.working_times:
            self._date_range(working_time.working_time_id, working_time.start_date, working_time.end_date, issues)
            self._non_negative(working_time.working_time_id, working_time.declared_hours, "INVALID_WORKING_TIME", issues)
        for counter in export.counters:
            self._non_negative(counter.counter_id, counter.declared_value, "INVALID_COUNTER", issues)
            self._date(counter.counter_id, counter.observed_at, issues)
            if not counter.label:
                issues.append(self._issue(counter.counter_id, "MISSING_COUNTER_LABEL", (counter.counter_id,), "Counter label is missing."))
        if not export.working_times:
            warnings.append(KelioWarning("missing-working-time", "No working-time period was declared."))
        valid = not issues
        return KelioValidation(valid, KelioStatus.VALID if valid else KelioStatus.INVALID, tuple(issues), tuple(warnings))

    def _duplicates(self, export, issues):
        collections = (
            export.schedules, export.working_days, export.shifts, export.night_work,
            export.five_shift, export.on_calls, export.interventions, export.leaves,
            export.working_times, export.counters, export.evidence,
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
            "night_work_id", "five_shift_id", "intervention_id",
            "leave_id", "working_time_id", "counter_id", "evidence_id", "shift_id",
            "working_day_id", "on_call_id", "schedule_id",
        ):
            if hasattr(item, name):
                return getattr(item, name)
        raise ValueError("Unsupported Kelio item.")

    def _date_range(self, identifier, start, end, issues):
        parsed_start, parsed_end = self._date(identifier, start, issues), self._date(identifier, end, issues)
        if parsed_start and parsed_end and parsed_start > parsed_end:
            issues.append(self._issue(identifier, "CHRONOLOGICAL_ORDER", (identifier,), "Start date is after end date."))

    @staticmethod
    def _date(identifier, value, issues):
        if value is None:
            issues.append(KelioValidator._issue(identifier, "MISSING_DATE", (identifier,), "Date is missing."))
            return None
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            issues.append(KelioValidator._issue(identifier, "INVALID_DATE", (identifier,), "Date is invalid."))
            return None

    @staticmethod
    def _datetime(identifier, field, value, issues):
        if value is None:
            issues.append(KelioValidator._issue(f"{identifier}:{field}", "MISSING_DATETIME", (identifier,), f"{field.title()} timestamp is missing."))
            return None
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            issues.append(KelioValidator._issue(f"{identifier}:{field}", "INVALID_DATETIME", (identifier,), f"{field.title()} timestamp is invalid."))
            return None

    @staticmethod
    def _non_negative(identifier, value, issue_type, issues):
        try:
            if value is None or Decimal(value) < 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            issues.append(KelioValidator._issue(identifier, issue_type, (identifier,), "Declared value must be a non-negative decimal string."))

    @staticmethod
    def _issue(issue_id, issue_type, subjects, description):
        return KelioIssue(f"issue:{issue_id}", issue_type, tuple(subjects), description)
