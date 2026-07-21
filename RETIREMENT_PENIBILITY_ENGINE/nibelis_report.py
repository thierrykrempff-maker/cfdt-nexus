"""Employee and expert reports for synthetic Nibelis exports."""

from .nibelis_models import NibelisReport, NibelisReportView, NibelisSummary


class NibelisReportBuilder:
    """Render deterministic reports using referential identifiers only."""

    def build(self, export, validation, information, converted, view):
        summary = NibelisSummary(
            export.metadata.export_id,
            validation.status,
            len(export.periods),
            len(export.salary_items),
            len(export.contributions),
            len(validation.issues),
        )
        common = dict(
            view=view,
            summary=summary,
            recognized_periods=information.period_ids,
            detected_rubrics=information.rubric_ids,
            remuneration_elements=information.salary_item_ids,
            points_to_verify=tuple(item.description for item in validation.issues),
        )
        if view is NibelisReportView.EMPLOYEE_VIEW:
            return NibelisReport(**common)
        return NibelisReport(
            **common,
            provenance=(export.metadata.source_reference,),
            rubrics=information.rubric_ids,
            contributions=information.contribution_ids,
            classifications=information.classifications + information.coefficients,
            parameters=information.parameter_ids,
            career_import_preparation=converted.converted_record_ids,
        )
