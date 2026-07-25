from __future__ import annotations

import sys
from pathlib import Path

from NEXUS_FINAL_ASSISTANT import AssistantRequest, Fact, NexusFinalAssistant


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation" / "scripts"))
import assistant_ds_router as router  # noqa: E402


def _assistant_with_sources(sources):
    return NexusFinalAssistant(
        {
            "syndical_reasoning": lambda _: {
                "mode": "SUCCEEDED",
                "analysis": {
                    "findings": ["Qualification provisoire à comparer aux faits"],
                    "missing_information": ["Document contractuel à vérifier"],
                    "recommendations": ["Demander une explication écrite"],
                },
                "sources": sources,
            }
        }
    )


def test_sources_follow_the_mandatory_employee_question_hierarchy() -> None:
    result = _assistant_with_sources(
        [
            {"source_layer": "jurisprudence", "title": "Cass. soc.", "decision_date": "2025-01-01"},
            {"source_layer": "code_travail", "title": "Code du travail", "article": "L. 0000-0"},
            {"source_layer": "convention_collective", "title": "CCNIC IDCC 44"},
            {"source_layer": "historique_cse", "title": "PV CSE synthétique"},
            {"source_layer": "accord_entreprise", "title": "Accord INEOS synthétique"},
        ]
    ).analyze(AssistantRequest("Mon contrat et mon poste changent"))

    assert [source.source_type for source in result.sources] == [
        "accord_entreprise",
        "convention_collective",
        "code_travail",
        "jurisprudence",
        "historique_cse",
    ]
    assert result.summary["primary_source"] == ("Accord INEOS synthétique",)


def test_response_analyzes_before_listing_missing_documents() -> None:
    result = _assistant_with_sources([]).analyze(
        AssistantRequest(
            "Mon poste change",
            facts=(Fact("Un changement a été annoncé"),),
        )
    )
    keys = list(result.summary)

    assert keys.index("understanding") < keys.index("factual_answer")
    assert keys.index("factual_answer") < keys.index("primary_source")
    assert keys.index("expert_advice") < keys.index("documents_indispensable")
    assert keys.index("documents_useful") < keys.index("missing")


def test_absent_case_law_and_cse_history_are_reported_not_invented() -> None:
    result = _assistant_with_sources(
        [{"source_layer": "accord_entreprise", "title": "Accord INEOS synthétique"}]
    ).analyze(AssistantRequest("Mon contrat change"))

    assert result.summary["comparable_case_law"] == (
        "Aucune jurisprudence comparable vérifiée n'a été retenue.",
    )
    assert result.summary["cse_elements"] == (
        "Aucun passage vérifié de procès-verbal du CSE n'a été retrouvé.",
    )


def test_case_law_is_never_presented_as_automatically_applicable() -> None:
    result = _assistant_with_sources(
        [
            {
                "source_layer": "jurisprudence",
                "title": "Cour de cassation, décision synthétique",
                "decision_date": "2025-01-01",
            }
        ]
    ).analyze(AssistantRequest("Une situation comparable est-elle jugée ?"))

    rendered = " ".join(result.summary["comparable_case_law"]).lower()
    assert "comparaison factuelle requise" in rendered
    assert "automatiquement applicable" not in rendered


def test_router_classifies_cse_minutes_as_context_not_legal_rule() -> None:
    source = {
        "document": "PV CSE du 12 mars 2024",
        "document_type": "proces verbal CSE",
    }
    assert router.source_layer_for_source(source) == "historique_cse"
    normalized = router.normalize_source(source, "cse_memory")
    assert normalized["source_layer"] == "historique_cse"


def test_router_employee_method_explains_document_utility_after_analysis() -> None:
    answer = {
        "understanding": "Situation comprise.",
        "short_answer": "Première réponse prudente.",
        "working_position": "Comparer la règle aux faits.",
        "sources": [],
        "findings": ["Argument salarié à vérifier."],
        "documents_to_request": ["contrat de travail", "planning"],
        "questions_to_ask": ["Quelle date ?"],
        "warnings": ["Prudence."],
        "next_action": "Demander une explication écrite.",
    }
    method = router.build_employee_method_analysis(answer)

    assert method["factual_answer"] == "Première réponse prudente."
    assert method["documents_after_analysis"][0]["document"] == "contrat de travail"
    assert method["documents_after_analysis"][0]["utility"]
    assert method["cse_status"].startswith("aucun passage vérifié")
