"""Prudent comparator assessments for equal-treatment analysis."""

from __future__ import annotations

import unicodedata

from .discrimination_models import ComparatorAssessment
from .models import ConfidenceLevel, SyndicalCaseInput


def assess_comparators(case: SyndicalCaseInput) -> tuple[ComparatorAssessment, ...]:
    text = _case_text(case)
    specifications = []
    if any(marker in text for marker in ("remuneration", "salaire", "prime")):
        specifications.append(("comparable_work", ("fonctions", "responsabilités"), ("ancienneté", "performance", "contraintes")))
    if any(marker in text for marker in ("classification", "coefficient")):
        specifications.append(("same_classification", ("classification déclarée",), ("contenu réel du poste", "expérience")))
    if any(marker in text for marker in ("sanction", "disciplinaire")):
        specifications.append(("similar_misconduct", ("faits apparemment similaires",), ("antécédents", "gravité", "contexte")))
    if any(marker in text for marker in ("mandat", "syndical", "signalement")):
        specifications.append(("before_after_event", ("même salarié",), ("organisation", "objectifs", "période")))
    if any(marker in text for marker in ("equipe", "collegue", "autres salaries", "comparateur")):
        specifications.append(("same_team", ("équipe ou hiérarchie commune",), ("missions", "ancienneté", "résultats")))
    if not specifications:
        specifications.append(("comparator_to_identify", (), ("fonctions", "ancienneté", "hiérarchie", "période")))
    available_types = {piece.document_type for piece in case.available_pieces}
    reliability = (
        ConfidenceLevel.MODERATE
        if available_types.intersection({"career_history", "payslip", "appraisal", "classification_record"})
        else ConfidenceLevel.LOW
    )
    return tuple(
        ComparatorAssessment(
            comparator_type=code,
            relevance="Pertinence à confirmer sur des situations réellement comparables.",
            similarities=similarities,
            objective_differences=differences,
            missing_data=("population de comparaison", "période comparable", "données homogènes"),
            reliability=reliability,
            limitations=(
                "Une différence constatée ne démontre pas à elle seule une discrimination.",
                "Les différences objectives doivent être examinées contradictoirement.",
            ),
            alternative_explanations=("organisation", "expérience", "résultats documentés", "contraintes du poste"),
        )
        for code, similarities, differences in specifications
    )


def _case_text(case: SyndicalCaseInput) -> str:
    value = " ".join(
        [case.question]
        + [item.statement for item in case.declared_facts]
        + [item.statement for item in case.established_facts]
    )
    normalized = unicodedata.normalize("NFKD", value)
    return " ".join(
        "".join(char for char in normalized if not unicodedata.combining(char))
        .lower()
        .replace("’", " ")
        .replace("'", " ")
        .split()
    )
