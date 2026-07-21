"""Audience-specific reports for synthetic payslip imports."""

from .payslip_models import PayslipReport, PayslipReportView, PayslipSummary


class PayslipReportBuilder:
    """Render deterministic reports containing metadata only."""

    def build(self, payslip, validation, payroll, converted, view):
        payroll_items = len(payslip.salary_items) + len(payslip.contributions)
        summary = PayslipSummary(
            payslip.metadata.payslip_id,
            validation.status,
            len(payslip.periods),
            payroll_items,
            len(validation.issues),
        )
        missing = tuple(item.description for item in validation.issues)
        detected = (
            tuple(f"classification:{item}" for item in payroll.classification_labels)
            + tuple(f"schedule:{item}" for item in payroll.schedule_labels)
            + tuple(f"salary-item:{item}" for item in payroll.salary_item_codes)
        )
        common = dict(
            view=view,
            summary=summary,
            recognized_periods=payroll.period_ids,
            detected_information=detected,
            missing_information=missing,
            next_steps=("Faire verifier les metadonnees de paie avant leur integration.",),
        )
        if view is PayslipReportView.EMPLOYEE_VIEW:
            return PayslipReport(**common)
        return PayslipReport(
            **common,
            detected_items=payroll.salary_item_codes + payroll.contribution_codes,
            provenance=(payslip.metadata.source_reference,),
            classifications=payroll.classification_labels + payroll.coefficient_values,
            schedules=payroll.schedule_labels,
            night_work=payroll.night_work_ids,
            five_shift=payroll.five_shift_ids,
            validation=(validation.status.value,),
            career_import_preparation=converted.converted_record_ids,
        )
