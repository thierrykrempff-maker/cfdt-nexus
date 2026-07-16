"""Territorial screening without presuming that locality alone proves application."""
from __future__ import annotations
from .alsace_moselle_models import ApplicabilityAssessment, EmploymentContext, LOCAL_DEPARTMENTS

def _local(value: str|None) -> bool:
    return bool(value and value.strip().casefold() in LOCAL_DEPARTMENTS)

def assess_applicability(context: EmploymentContext) -> ApplicabilityAssessment:
    facts=[]; missing=[]; warnings=[]; assumptions=[]
    if context.habitual_work_department:
        facts.append("habitual_work_department")
        if _local(context.habitual_work_department):
            status="applicable" if not (context.telework or context.multiple_work_departments or context.temporary_assignment) else "probably_applicable"
        else: status="not_applicable"
    elif context.multiple_work_departments:
        facts.append("multiple_work_departments")
        status="applicability_uncertain" if any(_local(x) for x in context.multiple_work_departments) else "not_applicable"
        if status=="applicability_uncertain": missing.append("habitual_place_and_work_distribution")
    elif _local(context.establishment_department):
        facts.append("establishment_department"); status="probably_applicable"; missing.append("habitual_work_department")
    else:
        status="insufficient_information"; missing.append("habitual_work_department")
        if context.employer_head_office_department: facts.append("employer_head_office_department")
    if _local(context.employer_head_office_department) and status!="applicable":
        warnings.append("employer_head_office_alone_is_not_sufficient")
    if context.telework: warnings.append("telework_requires_place_of_work_analysis")
    if context.temporary_assignment: warnings.append("temporary_assignment_requires_duration_and_usual_place")
    confidence={"applicable":"high","not_applicable":"high","probably_applicable":"medium","applicability_uncertain":"low","insufficient_information":"very_low"}[status]
    return ApplicabilityAssessment(status,tuple(facts),tuple(assumptions),tuple(dict.fromkeys(missing)),tuple(warnings),confidence)
