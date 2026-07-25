from __future__ import annotations

import sys
from pathlib import Path

import pytest

from NEXUS_RUNTIME_INTEGRATION import (
    RuntimeFinalAssistantConfig,
    RuntimeFinalAssistantIntegration,
    RuntimeSyndicalReasoningConfig,
    RuntimeSyndicalReasoningIntegration,
    RuntimeSyndicalReasoningMode,
)


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation" / "scripts"))
import assistant_ds_router as router  # noqa: E402


BASE = (
    "Une salariée du laboratoire travaille de jour. La direction veut la contraindre "
    "à remplacer un salarié démissionnaire en passant à un rythme posté matin/après-midi, "
    "avec des week-ends et jours fériés. Ce changement n'est pas volontaire et elle ne le "
    "souhaite pas. La rémunération serait plus élevée, mais ce n'est pas l'objet principal. "
    "L'équipe de jour pourrait être réduite. L'objectif est de défendre la salariée."
)


@pytest.mark.parametrize(
    "query",
    (
        BASE,
        BASE.replace("contraindre", "obliger"),
        BASE.replace("La direction veut la contraindre", "Le changement est imposé"),
        BASE.replace("matin/après-midi", "en équipes postées"),
        BASE.replace("week-ends et jours fériés", "jours fériés et repos variables"),
        BASE.replace("remplacer un salarié démissionnaire", "assurer le remplacement après une démission"),
        BASE.replace("L'équipe de jour pourrait être réduite", "La direction veut réduire l'équipe de jour"),
        BASE.replace("La rémunération serait plus élevée", "Une prime de poste serait versée"),
        BASE.replace("elle ne le souhaite pas", "elle refuse de donner son accord"),
        BASE.replace("L'objectif est de défendre la salariée", "Le DS veut accompagner et protéger la salariée"),
    ),
)
def test_ten_forced_day_to_shift_scenarios_keep_the_right_priorities(query: str) -> None:
    route = router.route_query(query)

    assert route["main_domain"] == "droit_travail_general"
    assert {"droit_travail_general", "temps_travail", "cse"} <= set(route["domains"])
    assert "analyser_situation_individuelle" in route["intents"]
    assert "preparer_cse" in route["intents"]
    assert "paie_remuneration" not in route["domains"]
    assert "analyser_paie" not in route["intents"]
    assert "expert_paie_v2" not in route["engines"]


def test_runtime_keeps_r1a_primary_and_adds_r1c_and_r2a() -> None:
    answer = router.ask(BASE, 2, 4)
    result = RuntimeSyndicalReasoningIntegration(
        RuntimeSyndicalReasoningConfig(True), timer=lambda: 1.0
    ).integrate(answer)

    assert result.mode is RuntimeSyndicalReasoningMode.SUCCEEDED
    assert result.domain_analysis is not None
    articulation = result.domain_analysis["articulation"]
    assert articulation["primary_domain"] == "R1A_CONTRACT_CHANGE"
    assert {"R1C_WORKING_TIME", "R2A_CSE_CONSULTATION"} <= set(
        articulation["complementary_domains"]
    )
    assert {"working_time", "cse_consultation"} <= set(
        result.domain_analysis["complementary_analyses"]
    )


def test_answer_preserves_negations_and_never_infers_promotion_or_consent() -> None:
    answer = router.ask(BASE, 2, 4)
    facts = " ".join(item["statement"] for item in answer["facts"]).lower()
    short = answer["short_answer"].lower()

    assert "n'est pas volontaire" in facts
    assert "n'est pas l'objet principal" in facts
    assert "imposé" in facts
    assert "ne doit pas être présentée comme une promotion" in short
    assert "ne prouve ni accord" in short
    assert "expert_paie_v2" not in answer["route"]["engines"]


def test_critical_questions_and_defensive_plan_are_present() -> None:
    answer = router.ask(BASE, 2, 12)
    questions = " ".join(answer["questions_to_ask"]).lower()
    documents = " ".join(answer["documents_to_request"]).lower()
    position = answer["working_position"].lower()

    for marker in (
        "contrat",
        "temporaire ou permanent",
        "cycle exact",
        "délai de prévenance",
        "volontaires",
        "accord ineos",
        "effectif",
        "cse",
        "transport",
    ):
        assert marker in questions
    assert "effectifs avant/après" in documents
    assert "sans laisser entendre qu'elle a accepté" in position
    assert "refus non préparé" in position


def test_explicit_payroll_control_still_selects_payroll() -> None:
    query = (
        BASE
        + " Je demande aussi de calculer précisément la prime et de contrôler le bulletin de paie."
    )
    route = router.route_query(query)

    assert "paie_remuneration" in route["domains"]
    assert "analyser_paie" in route["intents"]


def test_final_assistant_does_not_execute_payroll_for_secondary_pay_context() -> None:
    answer = router.ask(BASE, 2, 4)
    result = RuntimeFinalAssistantIntegration(
        RuntimeFinalAssistantConfig(True), timer=lambda: 1.0
    ).integrate(
        answer,
        {"title": "Rapport historique", "sections": []},
        existing_results={
            "syndical_reasoning": {"mode": "SUCCEEDED"},
            "cse_memory": {"mode": "DISABLED"},
        },
    )

    assert "expert_paie_v2" not in result.assistant["trace"]["engines_called"]
    understanding = " ".join(result.assistant["summary"]["understanding"]).lower()
    assert "imposé" in understanding
    assert "n'est pas volontaire" in understanding
