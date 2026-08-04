from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import uuid

from SYNDICAL_REASONING_ENGINE import (
    build_actionable_preparation,
    build_case_factual_core,
    build_research_plan,
)


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "apps" / "nexus-local-interface" / "server.py"


def load_server():
    module_name = f"interactive_enrichment_server_{uuid.uuid4().hex}"
    sys.path.insert(0, str(SERVER_PATH.parent))
    spec = importlib.util.spec_from_file_location(module_name, SERVER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INITIAL_QUESTION = (
    "Une salariée du laboratoire travaillant de jour peut-elle être obligée de "
    "passer en équipe postée après une démission, alors qu’elle n’est pas "
    "volontaire et que le CSE n’a pas été informé ?"
)


def enriched_context() -> dict[str, object]:
    return {
        "user_question": INITIAL_QUESTION,
        "facts": {"stillEmployed": True},
        "employee_interview": [
            {
                "question": "Quel changement exact l’employeur veut-il appliquer ?",
                "answer": "Un avenant permanent vers un rythme posté.",
            }
        ],
        "follow_up_answers": [
            {
                "question": "Quel cycle exact a été annoncé ?",
                "answer": (
                    "Il n’y a pas de nuit, mais le cycle inclut des week-ends "
                    "et des jours fériés."
                ),
            },
            {
                "question": "Quelle réponse la direction a-t-elle donnée ?",
                "answer": "La DRH a déclaré : c’est ça ou un licenciement.",
            },
            {
                "question": "Quel est l’impact sur le service de jour ?",
                "answer": (
                    "Le service de jour se retrouverait avec une personne de moins, "
                    "sans étude communiquée et sans information du CSE."
                ),
            },
        ],
    }


def test_portal_answers_are_projected_into_typed_factual_sections() -> None:
    server = load_server()
    query = server.build_enriched_analysis_query("texte décoré ignoré", enriched_context())

    assert query.startswith("Faits fournis:")
    assert f"- {INITIAL_QUESTION}" in query
    assert "Faits allégués:" in query
    normalized_query = query.casefold()
    assert "il n’y a pas de nuit" in normalized_query
    assert "c’est ça ou un licenciement" in normalized_query
    assert "une personne de moins" in normalized_query
    assert "Contexte:" in query
    assert "Le salarié est encore en poste : oui" in query


def test_enriched_facts_rebuild_the_legal_plan_without_disciplinary_rerouting() -> None:
    server = load_server()
    query = server.build_enriched_analysis_query("", enriched_context())
    core = build_case_factual_core(query, "QUESTION_SALARIE")
    plan = build_research_plan(core)

    assert core.event_category == "WORK_SCHEDULE_CHANGE"
    assert core.requested_path == "QUESTION_SALARIE"
    assert core.collective_impact_possible is True
    assert core.sanction_or_measure_considered == "licenciement"
    rendered_facts = " ".join(
        fact.canonical_text for fact in core.canonical_facts
    ).casefold()
    assert "avenant" in rendered_facts
    assert "week-ends" in rendered_facts
    assert "jours fériés" in rendered_facts
    assert "personne de moins" in rendered_facts
    assert len(plan.issues) == 7
    assert not any("disciplinaire" in issue.title.casefold() for issue in plan.issues)


def test_enriched_analysis_turns_the_exchange_into_actionable_union_reasoning() -> None:
    server = load_server()
    query = server.build_enriched_analysis_query("", enriched_context())
    answer = server.run_router(query, 6, "QUESTION_SALARIE")

    position = answer["working_position"].casefold()
    short_answer = answer["short_answer"].casefold()
    questions = " ".join(answer["questions_to_ask"]).casefold()
    documents = " ".join(answer["documents_to_request"]).casefold()

    assert "projet d'avenant écrit" in position
    assert "week-ends, jours fériés, repos" in position
    assert "effectifs avant/après" in position
    assert "accepter ou licenciement" in position
    assert "seul refus d'un avenant" in position
    assert "absence de nuit ne suffit pas" in short_answer
    assert "motif juridique précis" in questions
    assert "confirmation écrite" in documents
    assert "évaluation des risques" in documents


def test_follow_up_projection_is_request_local_and_bounded() -> None:
    server = load_server()
    first = server.build_enriched_analysis_query("", enriched_context())
    second = server.build_enriched_analysis_query(
        "",
        {
            "user_question": "Comment vérifier une erreur de classification ?",
            "follow_up_answers": [
                {"question": f"Question {index}", "answer": "x" * 4000}
                for index in range(20)
            ],
        },
    )

    assert "licenciement" in first
    assert "licenciement" not in second
    assert second.count("En réponse à") == server.MAX_FOLLOW_UP_ANSWERS
    assert "x" * (server.MAX_FOLLOW_UP_ANSWER_LENGTH + 1) not in second


def test_legacy_api_query_without_portal_context_is_unchanged() -> None:
    server = load_server()
    raw = "Question juridique historique."
    assert server.build_enriched_analysis_query(raw, {}) == raw


def test_interface_exposes_local_non_persistent_follow_up_controls() -> None:
    html = (ROOT / "apps" / "nexus-local-interface" / "index.html").read_text(
        encoding="utf-8"
    )
    script = (ROOT / "apps" / "nexus-local-interface" / "app.js").read_text(
        encoding="utf-8"
    )

    assert 'id="factualEnrichmentPanel"' in html
    assert 'id="followUpQuestions"' in html
    assert 'id="refineAnalysisButton"' in html
    assert "Préciser et améliorer la réponse" in html
    assert "function refineAnalysisWithFollowUp()" in script
    assert "follow_up_answers: followUpConversation.map" in script
    assert "employee_interview: Object.entries(interviewAnswers)" in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script


def test_employee_flow_requests_documents_during_the_dialogue_not_upfront() -> None:
    html = (ROOT / "apps" / "nexus-local-interface" / "index.html").read_text(
        encoding="utf-8"
    )
    script = (ROOT / "apps" / "nexus-local-interface" / "app.js").read_text(
        encoding="utf-8"
    )

    assert 'id="followUpDocuments"' in html
    assert "Pièces à fournir seulement si elles sont utiles et disponibles" in script
    assert "Ne bloquez pas l’échange pour les rechercher immédiatement" in script
    assert "return usesConversationalEmployeeFlow() ? [2]" in script
    assert 'currentEmployeePath === "QUESTION_SALARIE"' in script
    assert "Signaler une pièce dans la discussion" in script


def test_simple_employee_question_is_a_single_screen_chatbot() -> None:
    html = (ROOT / "apps" / "nexus-local-interface" / "index.html").read_text(
        encoding="utf-8"
    )
    script = (ROOT / "apps" / "nexus-local-interface" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "Poser une question" in html
    assert "Nexus répond directement" in html
    assert 'title: "Posez votre question"' in script
    assert '2: usesConversationalEmployeeFlow() ? "Question" : "Description"' in script
    assert "currentWizardStep = conversationalFlow ? 2 : 1" in script
    assert 'wizardView.classList.toggle("chatbot-mode", conversationalFlow)' in script
    assert 'analyzeButton.textContent = usesConversationalEmployeeFlow()' in script
    assert '"Envoyer la question à Nexus"' in script
    assert 'const responseMode = conversationalFlow' in script
    assert '? "QUICK"' in script


def test_simple_employee_result_hides_technical_detail_until_requested() -> None:
    html = (ROOT / "apps" / "nexus-local-interface" / "index.html").read_text(
        encoding="utf-8"
    )
    script = (ROOT / "apps" / "nexus-local-interface" / "app.js").read_text(
        encoding="utf-8"
    )
    styles = (ROOT / "apps" / "nexus-local-interface" / "styles.css").read_text(
        encoding="utf-8"
    )

    assert 'id="chatbotDetailsButton" hidden' in html
    assert "Voir les sources et le détail" in html
    assert 'resultView.classList.toggle("chatbot-result", conversationalFlow)' in script
    assert "usesConversationalEmployeeFlow() ? 1 : 10" in script
    assert ".result-panel.chatbot-result:not(.chatbot-details-open)" in styles
    assert "#reportPanel" in styles
    assert "function conversationalDirectAnswer(" in script
    direct_answer = script[
        script.index("function conversationalDirectAnswer(") :
        script.index("function conversationalNextSteps(")
    ]
    assert "publicSummary.syndical_position" in direct_answer
    assert "publicSummary.rule_to_facts" in direct_answer
    assert 'category === "WORK_SCHEDULE_CHANGE"' not in direct_answer
    assert "orchestration.reponse_synthetique_nexus" in direct_answer
    assert "DISCIPLINARY_CASE_UNSPECIFIED" not in direct_answer
    assert "PPE_AVAILABILITY_OR_SUITABILITY" not in direct_answer
    assert "factualEnrichmentPanel.hidden = false" in script
    assert "function conversationalNextSteps(" in script
    assert 'id="chatbotSourcesSummary" hidden' in html
    assert 'id="chatbotPvSummary" hidden' in html
    assert "Documents consultés par Nexus" in html
    assert "function renderConversationalSources(" in script
    assert "function appendHighlightedExcerpt(" in script
    assert 'document.createElement("mark")' in script
    assert "appendHighlightedExcerpt(excerpt, source.excerpt)" in script
    assert "appendHighlightedExcerpt(excerpt, context.excerpt)" in script
    assert ".nexus-source-highlight" in styles
    assert "background: #ffe66d" in styles
    assert "Nexus attend une précision déterminante" in script
    assert "Nexus a recherché les documents pertinents" in script
    assert "Nexus pose une seule question décisive à la fois" in html
    assert "Préciser et améliorer la réponse" in html
    assert 'openWorkspace("employee", "", "QUESTION_SALARIE");' in script
    assert "← Autres outils Nexus" in script
    assert 'statusPill.classList.toggle("chatbot-status-hidden", conversationalFlow)' in script
    assert ".wizard-view.chatbot-mode #pilotBannerInput" in styles


def test_plain_schedule_change_question_gets_a_real_legal_plan() -> None:
    core = build_case_factual_core(
        (
            "Mon employeur veut changer mes horaires et me faire travailler "
            "les week-ends. Puis-je refuser ?"
        ),
        "QUESTION_SALARIE",
    )
    plan = build_research_plan(core)

    assert core.event_category == "WORK_SCHEDULE_CHANGE"
    assert len(plan.issues) == 7
    assert any(issue.title == "Modification contractuelle" for issue in plan.issues)


def test_unspecified_conservatory_suspension_asks_for_the_exact_grievance() -> None:
    core = build_case_factual_core(
        "Un salarié a reçu une lettre de mise à pied à titre conservatoire.",
        "QUESTION_SALARIE",
    )
    preparation = build_actionable_preparation(core)
    questions = [
        item["question"]
        for item in preparation["questions_for_employee"]
    ]

    assert core.event_category == "DISCIPLINARY_CASE_UNSPECIFIED"
    assert core.blocking_ambiguities == [
        "Préciser le manquement exact reproché au salarié avant toute analyse de fond."
    ]
    assert any("manquement précis" in question for question in questions)
    assert all("harcèlement" not in question.casefold() for question in questions)


def test_follow_up_safety_fact_reclassifies_and_unblocks_document_search() -> None:
    server = load_server()
    initial = "Un salarié a reçu une mise à pied à titre conservatoire."
    enriched = server.build_enriched_analysis_query(
        initial,
        {
            "user_question": initial,
            "follow_up_answers": [
                {
                    "question": "Quel manquement précis est reproché ?",
                    "answer": (
                        "L'employeur reproche le non-port des lunettes de protection. "
                        "Le salarié indique qu'elles étaient inadaptées."
                    ),
                }
            ],
        },
    )
    core = build_case_factual_core(enriched, "QUESTION_SALARIE")

    assert core.event_category == "PPE_AVAILABILITY_OR_SUITABILITY"
    assert core.blocking_ambiguities == []
