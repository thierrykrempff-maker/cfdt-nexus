"""Independent and balanced positions for disciplinary cases."""

from __future__ import annotations

from .contract_change_models import PositionAnalysis
from .disciplinary_models import (
    DisciplinaryQualification,
    DisciplinaryQualificationCandidate,
)
from .models import SyndicalCaseInput


def analyze_disciplinary_positions(
    case: SyndicalCaseInput,
    candidates: tuple[DisciplinaryQualificationCandidate, ...],
) -> tuple[PositionAnalysis, PositionAnalysis]:
    qualifications = {item.qualification for item in candidates}
    employee_arguments = [
        "Les faits, leur date, leur matérialité et leur imputabilité doivent être vérifiés.",
        "La procédure, la motivation et la proportionnalité peuvent être discutées.",
    ]
    employee_irregularities = [
        "délai, convocation, entretien, assistance et notification à contrôler",
        "règlement intérieur et garanties conventionnelles à vérifier",
    ]
    employee_weaknesses = [
        "faits contestés ou incomplets à documenter",
        "comparaisons avec d'autres situations à établir objectivement",
    ]
    employer_arguments = [
        "L'employeur peut invoquer des faits précis affectant le fonctionnement ou les obligations professionnelles.",
        "Il peut soutenir que la mesure est prévue et proportionnée au contexte établi.",
    ]
    employer_foundations = [
        "faits matériellement vérifiables",
        "règles internes et obligations applicables",
    ]
    employer_to_prove = [
        "chronologie et connaissance des faits",
        "respect de la procédure et motivation",
        "proportionnalité de la mesure",
    ]
    if qualifications.intersection(
        {
            DisciplinaryQualification.PROFESSIONAL_INSUFFICIENCY,
            DisciplinaryQualification.INSUFFICIENT_RESULTS,
        }
    ):
        employee_arguments.append("L'insuffisance alléguée peut dépendre des objectifs, moyens, formation ou organisation.")
        employer_to_prove.append("objectifs réalistes, moyens fournis et insuffisance objectivée")
    if DisciplinaryQualification.PROTECTED_EMPLOYEE in qualifications:
        employee_irregularities.append("protection et autorisation administrative éventuelle à vérifier")
        employer_to_prove.append("respect intégral de la procédure propre au salarié protégé")
    if not case.available_sources:
        employee_weaknesses.append("sources officielles et jurisprudence comparable non encore vérifiées")
        employer_to_prove.append("fondements juridiques et conventionnels à documenter")
    return (
        PositionAnalysis(tuple(employee_arguments), tuple(employee_irregularities), tuple(employee_weaknesses)),
        PositionAnalysis(tuple(employer_arguments), tuple(employer_foundations), tuple(employer_to_prove)),
    )
