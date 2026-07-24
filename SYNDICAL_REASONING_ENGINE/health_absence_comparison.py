"""Document comparisons without payroll calculation or administrative decision."""

from __future__ import annotations

from .health_absence_models import CompetentActor, HealthDocumentComparison
from .models import ConfidenceLevel, SyndicalCaseInput


COMPARISONS = (
    ("leave_schedule", "sick_leave_notice", "schedule", CompetentActor.HR, "période d'absence à vérifier"),
    ("leave_payslip", "sick_leave_notice", "payslip", CompetentActor.PAYROLL, "retenue ou maintien à vérifier"),
    ("allowance_maintenance", "daily_allowance_statement", "payslip", CompetentActor.PAYROLL, "décalage, subrogation ou régularisation possible"),
    ("declared_event_payroll", "reported_event", "payslip", CompetentActor.PAYROLL, "rubrique de paie à vérifier"),
    ("agreement_treatment", "ineos_agreement", "payslip", CompetentActor.HR, "traitement conventionnel à vérifier"),
    ("absence_leave_counter", "sick_leave_notice", "leave_counter", CompetentActor.HR, "acquisition ou report à vérifier"),
    ("return_opinion", "occupational_health_opinion", "return_record", CompetentActor.OCCUPATIONAL_PHYSICIAN, "organisation de reprise à vérifier"),
    ("restriction_job", "occupational_health_opinion", "job_description", CompetentActor.EMPLOYER, "compatibilité du poste à examiner"),
    ("skills_redeployment", "career_profile", "redeployment_proposal", CompetentActor.EMPLOYER, "reclassement à examiner"),
    ("provident_event", "provident_notice", "reported_event", CompetentActor.PROVIDENT_BODY, "garantie potentielle à examiner"),
    ("cpam_employer", "cpam_decision", "employer_treatment", CompetentActor.HR, "effets administratifs et contractuels à vérifier"),
)


def compare_health_documents(case: SyndicalCaseInput) -> tuple[HealthDocumentComparison, ...]:
    present = {item.document_type for item in case.available_pieces}
    result = []
    for code, left, right, actor, impact in COMPARISONS:
        both = left in present and right in present
        result.append(
            HealthDocumentComparison(
                code,
                left,
                right,
                ("deux métadonnées disponibles",) if both else (),
                ("écart apparent à vérifier",) if both else (),
                ("décalage de période", "document non encore traité", "régularisation ultérieure", "règle différente"),
                tuple(item for item in (left, right) if item not in present),
                ConfidenceLevel.MODERATE if both else ConfidenceLevel.LOW,
                impact,
                actor,
                False,
            )
        )
    return tuple(result)
