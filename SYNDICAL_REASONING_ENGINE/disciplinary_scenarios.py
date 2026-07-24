"""Seven fully synthetic R1B scenarios."""

from __future__ import annotations

from .models import CaseFact, SyndicalCaseInput, UrgencyLevel


def _case(question: str, facts: tuple[str, ...], domains: tuple[str, ...] = ("disciplinary_procedure",)) -> SyndicalCaseInput:
    return SyndicalCaseInput(
        question,
        declared_facts=tuple(CaseFact(item) for item in facts),
        person_capacity="salarié accompagné par un représentant syndical",
        workplace_context="établissement synthétique",
        suspected_domains=domains,
        urgency=UrgencyLevel.PROMPT,
        desired_outcome="analyser la procédure et préparer une stratégie graduée",
        missing_information=("dates exactes", "pièces de procédure", "sources vérifiées"),
    )


def disciplinary_scenarios() -> dict[str, SyndicalCaseInput]:
    return {
        "contested_warning": _case("Un avertissement est contesté par le salarié.", ("Le salarié conteste les faits reprochés.",)),
        "disciplinary_suspension": _case("Une mise à pied disciplinaire est notifiée.", ("La durée et la notification doivent être vérifiées.",)),
        "gross_misconduct_dismissal": _case("Un licenciement pour faute grave est envisagé.", ("La qualification et les preuves restent à vérifier.",)),
        "professional_insufficiency": _case("L'employeur invoque une insuffisance professionnelle.", ("Les objectifs, moyens et formations ne sont pas documentés.",)),
        "protected_employee": _case("Une sanction vise un salarié protégé titulaire d'un mandat.", ("Le mandat et sa période de protection doivent être vérifiés.",), ("disciplinary_procedure", "employee_protection")),
        "irregular_procedure": _case("Une sanction aurait été notifiée sans convocation préalable.", ("La chronologie de la procédure est incomplète.",)),
        "admitted_fault_disproportionate_measure": _case("Le salarié reconnaît une faute mais estime la sanction disproportionnée.", ("Le fait est reconnu sans accord sur sa gravité ni sur la mesure.",)),
    }
