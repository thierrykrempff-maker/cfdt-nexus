"""Employee and expert reports for synthetic career statements."""

from .career_statement_models import (
    CareerStatement,
    CareerStatementConversion,
    CareerStatementReport,
    CareerStatementReportView,
    CareerStatementSummary,
    CareerStatementValidation,
)


class CareerStatementReportBuilder:
    """Create deterministic metadata-only reports."""

    def build(self, statement, validation, conversion, view):
        summary = CareerStatementSummary(
            statement.metadata.statement_id,
            validation.status,
            len(statement.employers),
            len(statement.employments),
            len(statement.periods),
            len(statement.references),
            len(validation.issues) + len(validation.conflicts),
        )
        incomplete = tuple(
            item.employment_id for item in statement.employments if item.start_date is None or item.end_date is None
        ) + tuple(item.period_id for item in statement.periods if item.start_date is None or item.end_date is None)
        common = dict(
            view=view,
            summary=summary,
            imported_documents=("Releve synthetique declare",),
            recognized_periods=tuple(item.employment_id for item in statement.employments) + tuple(item.period_id for item in statement.periods),
            incomplete_periods=incomplete,
            points_to_verify=tuple(item.description for item in validation.issues) + tuple(item.description for item in validation.conflicts),
            next_steps=("Verifier les metadonnees et leur provenance avant toute integration.",),
        )
        if view is CareerStatementReportView.EMPLOYEE_VIEW:
            return CareerStatementReport(**common)
        return CareerStatementReport(
            **common,
            metadata=(f"source={statement.metadata.source.value}", f"version={statement.metadata.version}"),
            provenance=(statement.metadata.source_reference,),
            consistency=("coherent" if validation.valid else "verification requise",),
            quality=(f"confidence={statement.metadata.confidence.value}",),
            validation=(validation.status.value,),
            import_preparation=tuple(conversion.converted_record_ids),
        )
