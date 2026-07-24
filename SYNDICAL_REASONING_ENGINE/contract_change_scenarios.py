"""Five fully synthetic R1A scenarios."""

from __future__ import annotations

from .models import CaseFact, SyndicalCaseInput, UrgencyLevel


def _case(question: str, facts: tuple[str, ...], domains: tuple[str, ...]) -> SyndicalCaseInput:
    return SyndicalCaseInput(
        question,
        declared_facts=tuple(CaseFact(item) for item in facts),
        person_capacity="salarié accompagné par un représentant syndical",
        workplace_context="établissement synthétique",
        suspected_domains=domains,
        urgency=UrgencyLevel.PROMPT,
        desired_outcome="qualifier le changement et préparer une démarche graduée",
        missing_information=(
            "décision écrite",
            "clauses contractuelles applicables",
            "sources conventionnelles vérifiées",
        ),
    )


def contract_change_scenarios() -> dict[str, SyndicalCaseInput]:
    return {
        "day_to_shift": _case(
            "Passage annoncé d'un horaire de jour vers une équipe postée.",
            ("Le salarié déclare travailler de jour.", "Un passage en équipe postée est annoncé."),
            ("employment_contract", "working_time", "payroll", "cse_consultation"),
        ),
        "position_removal": _case(
            "Le poste du salarié serait supprimé dans une réorganisation.",
            ("Une suppression de poste est annoncée.",),
            ("employment_contract", "cse_consultation"),
        ),
        "major_hours_change": _case(
            "Modification importante des horaires et du planning habituel.",
            ("Les horaires habituels changeraient durablement.",),
            ("working_time", "employment_contract"),
        ),
        "internal_transfer": _case(
            "Mutation interne vers un nouveau poste et une nouvelle équipe.",
            ("Une mutation interne est proposée.", "Les missions pourraient changer."),
            ("employment_contract", "classification_carriere"),
        ),
        "collective_reorganization": _case(
            "Réorganisation d'un service touchant plusieurs salariés.",
            ("Plusieurs salariés seraient concernés.", "Le service serait restructuré."),
            ("employment_contract", "cse_consultation"),
        ),
    }
