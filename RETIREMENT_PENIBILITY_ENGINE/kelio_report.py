"""Employee and expert reports for synthetic Kelio exports."""

from .kelio_models import KelioReport, KelioReportView, KelioSummary


class KelioReportBuilder:
    """Create deterministic reports containing declared metadata only."""

    def build(self, export, validation, information, converted, view):
        summary = KelioSummary(
            export.metadata.export_id,
            validation.status,
            len(export.working_times),
            len(export.night_work),
            len(export.five_shift),
            len(validation.issues),
        )
        common = dict(
            view=view,
            summary=summary,
            recognized_periods=information.working_period_ids,
            detected_night_work=information.night_work_ids,
            detected_five_shift=information.five_shift_ids,
            absences=information.leave_ids,
            points_to_verify=tuple(item.description for item in validation.issues),
        )
        if view is KelioReportView.EMPLOYEE_VIEW:
            return KelioReport(**common)
        return KelioReport(
            **common,
            provenance=(export.metadata.source_reference,),
            schedules=information.schedule_labels,
            counters=information.counters,
            on_calls=information.on_call_ids + information.intervention_ids,
            documentary_consistency=("coherent" if validation.valid else "verification requise",),
            career_import_preparation=converted.converted_record_ids,
        )
