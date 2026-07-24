"""Ten synthetic and anonymous R1C scenarios."""

from __future__ import annotations

from .models import AvailablePiece, CaseFact, SyndicalCaseInput, UrgencyLevel


def _piece(piece_id: str, document_type: str, title: str) -> AvailablePiece:
    return AvailablePiece(piece_id, document_type, f"{title} — fixture synthétique", verified=True)


def _case(question: str, facts: tuple[str, ...], pieces: tuple[AvailablePiece, ...] = (), domains: tuple[str, ...] = ("temps_travail",)) -> SyndicalCaseInput:
    return SyndicalCaseInput(
        question,
        declared_facts=tuple(CaseFact(item) for item in facts),
        person_capacity="salarié synthétique accompagné par un représentant",
        workplace_context="organisation entièrement fictive",
        suspected_domains=domains,
        available_pieces=pieces,
        urgency=UrgencyLevel.PROMPT,
        desired_outcome="qualifier prudemment et préparer une vérification",
        missing_information=("règle applicable", "période exacte"),
    )


def working_time_scenarios() -> dict[str, SyndicalCaseInput]:
    schedule = _piece("synthetic-schedule", "official_schedule", "Planning")
    timeclock = _piece("synthetic-timeclock", "timeclock", "Badgeages")
    kelio = _piece("synthetic-kelio", "kelio_statement", "Relevé Kelio")
    payslip = _piece("synthetic-payslip", "payslip", "Bulletin Nibelis")
    return {
        "daily_rest_recall": _case("Un salarié posté termine puis est rappelé pendant la nuit : repos quotidien et intervention à vérifier.", ("Un rappel nocturne est déclaré.",), (schedule,),),
        "contested_overtime": _case("Des heures supplémentaires du planning et des badgeages ne sont pas retrouvées dans Kelio.", ("Un écart de compteur est déclaré.",), (schedule, timeclock, kelio)),
        "night_work": _case("Des heures de nuit sont régulièrement effectuées et les contreparties sont inconnues.", ("La répétition reste à documenter.",), (schedule,)),
        "on_call_intervention": _case("Une astreinte avec intervention et trajet d'intervention a interrompu le repos suivant.", ("Une intervention est déclarée.",), (_piece("synthetic-on-call", "on_call_record", "Astreinte"), _piece("synthetic-intervention", "intervention_sheet", "Intervention"))),
        "five_shift": _case("Organisation 5x8 : cycle, pauses, repos, jours fériés, nuit, Kelio et prime de poste à vérifier.", ("Le régime 5x8 est déclaré.",), (schedule, kelio)),
        "apparently_missing_bonus": _case("Un événement figure dans Kelio mais la prime correspondante semble absente du bulletin Nibelis.", ("Une anomalie apparente est déclarée.",), (kelio, payslip)),
        "kelio_nibelis_gap": _case("Écart Kelio / Nibelis à expliquer sans conclure à une erreur de paie.", ("Les périodes de clôture sont inconnues.",), (kelio, payslip)),
        "collective_organization": _case("Une nouvelle organisation d'horaires concerne plusieurs salariés.", ("Un changement collectif est annoncé.",), (schedule,), ("temps_travail", "contrat_travail", "cse")),
        "interrupted_break": _case("Un salarié reste joignable et intervient régulièrement pendant sa pause interrompue.", ("La liberté pendant la pause est inconnue.",), (timeclock,)),
        "cse_meeting_on_rest": _case("Un élu posté participe à une réunion CSE sur son jour de repos : réunion, trajet, délégation et repos sont à distinguer.", ("La réunion sur repos est déclarée.",), (schedule,), ("temps_travail", "cse")),
    }
