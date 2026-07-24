"""R1B reasoning projection for disciplinary procedures."""

from __future__ import annotations

import unicodedata

from .disciplinary_arguments import analyze_disciplinary_positions
from .disciplinary_evidence import disciplinary_evidence
from .disciplinary_models import (
    DisciplinaryAnalysis,
    DisciplinaryQualification,
    DisciplinaryQualificationCandidate,
    ProtectedEmployeeAnalysis,
)
from .disciplinary_questions import build_disciplinary_questions
from .disciplinary_strategies import build_disciplinary_strategies
from .engine import SyndicalReasoningEngine
from .models import SyndicalCaseInput


QUALIFICATION_MARKERS = {
    DisciplinaryQualification.INFORMAL_REMINDER: ("rappel a l ordre", "recadrage"),
    DisciplinaryQualification.WARNING: ("avertissement",),
    DisciplinaryQualification.REPRIMAND: ("blame",),
    DisciplinaryQualification.DISCIPLINARY_SUSPENSION: ("mise a pied disciplinaire",),
    DisciplinaryQualification.DISCIPLINARY_TRANSFER: ("mutation disciplinaire",),
    DisciplinaryQualification.DISCIPLINARY_DEMOTION: ("retrogradation disciplinaire",),
    DisciplinaryQualification.DISMISSAL_SIMPLE_MISCONDUCT: ("faute simple",),
    DisciplinaryQualification.DISMISSAL_GROSS_MISCONDUCT: ("faute grave",),
    DisciplinaryQualification.DISMISSAL_WILFUL_MISCONDUCT: ("faute lourde",),
    DisciplinaryQualification.PROFESSIONAL_INSUFFICIENCY: ("insuffisance professionnelle",),
    DisciplinaryQualification.INSUFFICIENT_RESULTS: ("insuffisance de resultats", "resultats insuffisants"),
    DisciplinaryQualification.JOB_ABANDONMENT: ("abandon de poste",),
    DisciplinaryQualification.REFUSAL_CONTRACT_CHANGE: ("refus d une modification", "refus de modification", "refus d avenant"),
    DisciplinaryQualification.PROTECTED_EMPLOYEE: ("salarie protege", "representant du personnel", "titulaire d un mandat", "inspection du travail"),
}

DISCIPLINARY_MARKERS = (
    "disciplinaire",
    "sanction",
    "licenciement pour faute",
    "entretien prealable",
    "convocation",
    "faits reproches",
) + tuple(marker for markers in QUALIFICATION_MARKERS.values() for marker in markers)

PROCEDURE_CHECKS = (
    "nature exacte de la mesure",
    "existence et champ de la procédure disciplinaire",
    "dates des faits et de leur connaissance par l'employeur",
    "convocation et objet annoncé",
    "entretien préalable et assistance",
    "notification, date et motivation",
    "preuves disponibles et contradictoires",
    "règlement intérieur applicable",
    "accords INEOS et convention collective applicables",
    "Code du travail à jour",
    "jurisprudence réellement comparable",
)


def needs_disciplinary_reasoning(case_or_question: SyndicalCaseInput | str) -> bool:
    if isinstance(case_or_question, SyndicalCaseInput):
        text = " ".join(
            [case_or_question.question]
            + [item.statement for item in case_or_question.declared_facts]
            + [item.statement for item in case_or_question.established_facts]
        )
        if set(case_or_question.suspected_domains).intersection(
            {"disciplinary_procedure", "disciplinaire", "employee_protection", "licenciement"}
        ):
            return True
    else:
        text = str(case_or_question)
    normalized = _normalize(text)
    return any(marker in normalized for marker in DISCIPLINARY_MARKERS)


class DisciplinaryReasoningEngine:
    """Specialize R0 without deciding whether a measure is justified."""

    def __init__(self, base_engine: SyndicalReasoningEngine | None = None) -> None:
        self._base_engine = base_engine or SyndicalReasoningEngine()

    def analyze(
        self,
        case: SyndicalCaseInput,
        *,
        scenario_code: str | None = None,
    ) -> DisciplinaryAnalysis:
        if not isinstance(case, SyndicalCaseInput):
            raise TypeError("case must be a SyndicalCaseInput")
        candidates = self._qualification_candidates(case)
        protection = self._protected_employee_analysis(candidates)
        employee, employer = analyze_disciplinary_positions(case, candidates)
        return DisciplinaryAnalysis(
            self._base_engine.analyze(case),
            candidates,
            PROCEDURE_CHECKS,
            build_disciplinary_questions(case, candidates),
            employee,
            employer,
            disciplinary_evidence(candidates),
            build_disciplinary_strategies(case, protection),
            protection,
            scenario_code,
        )

    @staticmethod
    def _qualification_candidates(
        case: SyndicalCaseInput,
    ) -> tuple[DisciplinaryQualificationCandidate, ...]:
        normalized = _normalize(
            " ".join(
                [case.question]
                + [item.statement for item in case.declared_facts]
                + [item.statement for item in case.established_facts]
            )
        )
        selected = {
            qualification
            for qualification, markers in QUALIFICATION_MARKERS.items()
            if any(marker in normalized for marker in markers)
        }
        if "licenciement" in normalized and selected.intersection(
            {
                DisciplinaryQualification.DISMISSAL_SIMPLE_MISCONDUCT,
                DisciplinaryQualification.DISMISSAL_GROSS_MISCONDUCT,
                DisciplinaryQualification.DISMISSAL_WILFUL_MISCONDUCT,
            }
        ):
            selected.update(
                {
                    DisciplinaryQualification.DISMISSAL_SIMPLE_MISCONDUCT,
                    DisciplinaryQualification.DISMISSAL_GROSS_MISCONDUCT,
                    DisciplinaryQualification.DISMISSAL_WILFUL_MISCONDUCT,
                }
            )
        if not selected:
            selected.add(DisciplinaryQualification.UNDETERMINED_MEASURE)
        return tuple(
            DisciplinaryQualificationCandidate(
                qualification,
                _rationale(qualification),
                _decisive_information(qualification),
            )
            for qualification in sorted(selected, key=lambda item: item.value)
        )

    @staticmethod
    def _protected_employee_analysis(
        candidates: tuple[DisciplinaryQualificationCandidate, ...],
    ) -> ProtectedEmployeeAnalysis:
        possible = any(
            item.qualification == DisciplinaryQualification.PROTECTED_EMPLOYEE
            for item in candidates
        )
        checks = (
            "nature, dates et périmètre du mandat",
            "période exacte de protection",
            "nature de la mesure envisagée",
            "autorisation administrative éventuellement requise",
            "saisine et rôle de l'inspection du travail",
            "conséquences procédurales à vérifier",
        ) if possible else ("existence éventuelle d'un mandat ou d'une protection particulière",)
        cautions = (
            "La protection et l'autorisation ne sont jamais présumées.",
            "La procédure dépend du mandat, de sa date et de la mesure envisagée.",
        )
        return ProtectedEmployeeAnalysis(possible, checks, cautions)


def _rationale(qualification: DisciplinaryQualification) -> str:
    if qualification == DisciplinaryQualification.INFORMAL_REMINDER:
        return "La mesure peut constituer un rappel non disciplinaire selon son contenu et ses effets."
    if qualification in {
        DisciplinaryQualification.PROFESSIONAL_INSUFFICIENCY,
        DisciplinaryQualification.INSUFFICIENT_RESULTS,
    }:
        return "Une insuffisance alléguée ne constitue pas automatiquement une faute."
    if qualification == DisciplinaryQualification.PROTECTED_EMPLOYEE:
        return "Un mandat déclaré peut imposer des vérifications procédurales spécifiques."
    if qualification == DisciplinaryQualification.UNDETERMINED_MEASURE:
        return "La nature de la mesure et les faits sont insuffisamment documentés."
    return f"Les faits contiennent un indice de {qualification.value.replace('_', ' ')}."


def _decisive_information(
    qualification: DisciplinaryQualification,
) -> tuple[str, ...]:
    common = ("faits précis et dates", "mesure écrite", "preuves contradictoires")
    if qualification == DisciplinaryQualification.PROTECTED_EMPLOYEE:
        return ("mandat et dates", "mesure envisagée", "étape administrative")
    if qualification in {
        DisciplinaryQualification.PROFESSIONAL_INSUFFICIENCY,
        DisciplinaryQualification.INSUFFICIENT_RESULTS,
    }:
        return ("objectifs", "moyens et formation", "résultats objectivés")
    return common


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char))
        .lower()
        .replace("’", " ")
        .replace("'", " ")
        .split()
    )
