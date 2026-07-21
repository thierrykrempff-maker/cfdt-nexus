"""Employee and expert reports for synthetic employment contracts."""

from .employment_contract_models import EmploymentReport, EmploymentReportView, EmploymentSummary


class EmploymentContractReportBuilder:
    """Create deterministic metadata-only contract reports."""

    def build(self, contract, validation, information, converted, view):
        summary = EmploymentSummary(
            contract.metadata.contract_id,
            validation.status,
            1,
            len(contract.amendments),
            len(contract.periods),
            len(validation.issues),
        )
        common = dict(
            view=view,
            summary=summary,
            detected_contracts=(contract.metadata.contract_id,),
            detected_amendments=information.amendment_ids,
            recognized_periods=information.period_ids,
            missing_information=tuple(item.description for item in validation.issues),
            next_steps=("Faire verifier le contrat, ses versions et ses avenants avant integration.",),
        )
        if view is EmploymentReportView.EMPLOYEE_VIEW:
            return EmploymentReport(**common)
        return EmploymentReport(
            **common,
            provenance=(contract.metadata.source_reference,),
            classifications=information.classifications,
            coefficients=information.coefficients,
            schedules=information.schedules + information.working_times,
            amendments=information.amendment_ids,
            history=tuple(f"{item.version}:{item.effective_date or '?'}" for item in contract.amendments),
            documentary_consistency=("coherent" if validation.valid else "verification requise",),
            career_import_preparation=converted.converted_record_ids,
        )
