"""R1A reasoning projection for contract and working-condition changes."""

from __future__ import annotations

import unicodedata

from .contract_change_arguments import analyze_positions
from .contract_change_evidence import required_evidence
from .contract_change_models import (
    ChangeDimension,
    ContractChangeAnalysis,
    QualificationCandidate,
)
from .contract_change_questions import build_questions
from .contract_change_strategies import build_contract_change_strategies
from .engine import SyndicalReasoningEngine
from .models import SyndicalCaseInput


DIMENSION_MARKERS = {
    ChangeDimension.CONTRACT: ("contrat", "avenant", "accord du salarie"),
    ChangeDimension.WORKING_CONDITIONS: ("conditions de travail", "organisation du travail"),
    ChangeDimension.WORKING_HOURS: ("horaire", "planning", "cycle"),
    ChangeDimension.DAY_TO_SHIFT: ("equipe postee", "travail poste", "jour vers"),
    ChangeDimension.TEAM: ("changement d equipe", "nouvelle equipe", "changer d equipe"),
    ChangeDimension.POSITION: ("changement de poste", "mutation interne", "nouveau poste"),
    ChangeDimension.QUALIFICATION: ("qualification", "missions"),
    ChangeDimension.CLASSIFICATION: ("classification", "coefficient"),
    ChangeDimension.GEOGRAPHIC_MOBILITY: ("mobilite", "mutation geographique", "autre site"),
    ChangeDimension.POSITION_REMOVAL: ("suppression de poste", "poste supprime"),
    ChangeDimension.REORGANIZATION: ("reorganisation", "plusieurs salaries", "service restructure"),
    ChangeDimension.REMUNERATION: ("remuneration", "salaire", "prime", "coefficient"),
}


def needs_contract_change_reasoning(case_or_question: SyndicalCaseInput | str) -> bool:
    if isinstance(case_or_question, SyndicalCaseInput):
        text = " ".join(
            [case_or_question.question]
            + [item.statement for item in case_or_question.declared_facts]
            + [item.statement for item in case_or_question.established_facts]
        )
        domains = set(case_or_question.suspected_domains)
        if domains.intersection(
            {
                "employment_contract",
                "contrat_travail",
                "working_time",
                "temps_travail",
                "classification_carriere",
            }
        ):
            return True
    else:
        text = str(case_or_question)
    normalized = _normalize(text)
    return any(
        marker in normalized
        for markers in DIMENSION_MARKERS.values()
        for marker in markers
    )


class ContractChangeReasoningEngine:
    """Specialize R0 while retaining its complete transverse report."""

    def __init__(self, base_engine: SyndicalReasoningEngine | None = None) -> None:
        self._base_engine = base_engine or SyndicalReasoningEngine()

    def analyze(
        self,
        case: SyndicalCaseInput,
        *,
        scenario_code: str | None = None,
    ) -> ContractChangeAnalysis:
        if not isinstance(case, SyndicalCaseInput):
            raise TypeError("case must be a SyndicalCaseInput")
        dimensions = self._dimensions(case)
        candidates = self._qualification_candidates(dimensions)
        employee, employer = analyze_positions(case, dimensions)
        return ContractChangeAnalysis(
            self._base_engine.analyze(case),
            dimensions,
            candidates,
            build_questions(case, dimensions),
            employee,
            employer,
            required_evidence(dimensions),
            build_contract_change_strategies(case),
            scenario_code,
        )

    @staticmethod
    def _dimensions(case: SyndicalCaseInput) -> tuple[ChangeDimension, ...]:
        normalized = _normalize(
            " ".join(
                [case.question]
                + [item.statement for item in case.declared_facts]
                + [item.statement for item in case.established_facts]
            )
        )
        selected = {
            dimension
            for dimension, markers in DIMENSION_MARKERS.items()
            if any(marker in normalized for marker in markers)
        }
        if {
            ChangeDimension.WORKING_HOURS,
            ChangeDimension.DAY_TO_SHIFT,
            ChangeDimension.TEAM,
            ChangeDimension.POSITION,
        }.intersection(selected):
            selected.add(ChangeDimension.WORKING_CONDITIONS)
            selected.add(ChangeDimension.CONTRACT)
        if ChangeDimension.DAY_TO_SHIFT in selected:
            selected.add(ChangeDimension.WORKING_HOURS)
        if ChangeDimension.POSITION_REMOVAL in selected:
            selected.add(ChangeDimension.REORGANIZATION)
            selected.add(ChangeDimension.POSITION)
        return tuple(sorted(selected, key=lambda item: item.value))

    @staticmethod
    def _qualification_candidates(
        dimensions: tuple[ChangeDimension, ...],
    ) -> tuple[QualificationCandidate, ...]:
        candidates = []
        selected = set(dimensions)
        if ChangeDimension.CONTRACT in selected:
            candidates.append(
                QualificationCandidate(
                    ChangeDimension.CONTRACT,
                    "Une clause contractualisée, la rémunération, la qualification ou "
                    "un élément déterminant pourrait être affecté.",
                    (
                        "contrat et avenants",
                        "accord explicite du salarié",
                        "écart précis avant/après",
                    ),
                )
            )
        if ChangeDimension.WORKING_CONDITIONS in selected:
            candidates.append(
                QualificationCandidate(
                    ChangeDimension.WORKING_CONDITIONS,
                    "Le changement pourrait relever de l'organisation du travail si "
                    "aucun élément contractualisé n'est altéré.",
                    (
                        "portée des clauses contractuelles",
                        "ampleur et durée du changement",
                        "contraintes concrètes",
                    ),
                )
            )
        for dimension in dimensions:
            if dimension in {
                ChangeDimension.CONTRACT,
                ChangeDimension.WORKING_CONDITIONS,
            }:
                continue
            candidates.append(
                QualificationCandidate(
                    dimension,
                    f"Les faits comportent un indice de {dimension.value.replace('_', ' ')}.",
                    ("décision écrite", "chronologie", "pièces comparatives"),
                )
            )
        if not candidates:
            candidates.append(
                QualificationCandidate(
                    ChangeDimension.WORKING_CONDITIONS,
                    "Les informations sont insuffisantes pour identifier la nature du changement.",
                    ("nature exacte du changement", "date", "durée", "effets"),
                )
            )
        return tuple(candidates)


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char))
        .lower()
        .replace("’", " ")
        .replace("'", " ")
        .split()
    )
