from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
ROUTER_DIR = ROOT / "automation" / "scripts"
SERVER_PATH = ROOT / "apps" / "nexus-local-interface" / "server.py"
sys.path.insert(0, str(ROUTER_DIR))
import assistant_ds_router as router  # noqa: E402


@pytest.mark.parametrize(
    "question",
    [
        "Quels sont mes droits sur mes horaires ?",
        "Comment vérifier ma prime et mon bulletin de paie ?",
        "Puis-je prendre mes congés en septembre ?",
        "Mon contrat prévoit du travail posté.",
    ],
)
def test_ordinary_employee_questions_use_public_path(question: str) -> None:
    route = router.route_query(question)

    assert route["employee_path"] == router.QUESTION_SALARIE
    assert route["functional_intent"] == router.QUESTION_SALARIE
    assert route["response_profile"] == "public_pedagogical"


@pytest.mark.parametrize(
    "question",
    [
        "Je viens de recevoir une convocation.",
        "Je suis convoqué à un entretien préalable.",
        "Comment répondre à un avertissement ?",
        "Une mise à pied disciplinaire est envisagée.",
        "On me reproche une faute et une insubordination.",
        "Je dois préparer la défense du salarié.",
        "Comment accompagner le salarié à un entretien ?",
    ],
)
def test_explicit_disciplinary_signals_use_deep_path(question: str) -> None:
    route = router.route_query(question)

    assert route["employee_path"] == router.ASSISTANCE_ENTRETIEN_DISCIPLINAIRE
    assert route["main_domain"] == "disciplinaire"
    assert "analyser_situation_individuelle" in route["intents"]
    assert route["response_profile"] == "syndical_defense_deep"


@pytest.mark.parametrize(
    "question",
    [
        "Comment préparer mon entretien professionnel ?",
        "Mon entretien annuel est prévu vendredi.",
        "Je passe un entretien de recrutement.",
        "Comment accompagner un entretien professionnel ?",
    ],
)
def test_non_disciplinary_interviews_are_not_false_positives(question: str) -> None:
    route = router.route_query(question)

    assert route["employee_path"] == router.QUESTION_SALARIE
    assert route["main_domain"] != "disciplinaire"


def test_ambiguous_interview_stays_public_with_advisory() -> None:
    route = router.route_query("Comment préparer cet entretien avec mon responsable ?")

    assert route["employee_path"] == router.QUESTION_SALARIE
    assert "mode disciplinaire" in route["employee_path_advisory"]


def test_explicit_deep_ui_choice_is_honored_without_inventing_a_signal() -> None:
    route = router.route_query(
        "Je souhaite préparer le dossier.",
        router.ASSISTANCE_ENTRETIEN_DISCIPLINAIRE,
    )

    assert route["employee_path"] == router.ASSISTANCE_ENTRETIEN_DISCIPLINAIRE
    assert route["main_domain"] == "disciplinaire"


def test_unknown_explicit_path_is_rejected() -> None:
    with pytest.raises(ValueError, match="Parcours salarié inconnu"):
        router.route_query("Question", "UNKNOWN")


def test_full_disciplinary_scenario_produces_ordered_a_to_g_dossier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        router,
        "search_bible",
        lambda *_args, **_kwargs: {
            "sources_used": [],
            "points_to_verify": [],
        },
    )
    monkeypatch.setattr(router, "bridge", None)
    monkeypatch.setattr(router, "legifrance", None)
    monkeypatch.setattr(router, "judilibre", None)
    monkeypatch.setattr(router, "cdtn", None)

    answer = router.ask(
        (
            "Un salarié reçoit une convocation à un entretien préalable après un "
            "incident de sécurité. L'employeur évoque une faute, mais les consignes "
            "et la formation sont contestées. Comment préparer sa défense ?"
        ),
        6,
        6,
    )
    dossier = answer["disciplinary_assistance"]

    assert answer["route"]["employee_path"] == router.ASSISTANCE_ENTRETIEN_DISCIPLINAIRE
    assert answer["employee_method_analysis"] is None
    assert list(dossier)[2:9] == [
        "A_qualification",
        "B_timeline",
        "C_procedure_control",
        "D_facts_analysis",
        "E_interview_preparation",
        "F_during_interview",
        "G_after_interview",
    ]
    assert dossier["D_facts_analysis"]["recognized_facts"] == []
    assert "Aucun fait" in dossier["D_facts_analysis"]["guardrail"]
    assert dossier["E_interview_preparation"]["questions_for_employee"]
    assert dossier["E_interview_preparation"]["questions_for_employer"]
    assert dossier["E_interview_preparation"]["documents_after_initial_analysis"]
    rendered = json.dumps(dossier, ensure_ascii=False).casefold()
    assert "automatiquement la sanction d'illégale" in rendered
    assert "ne présume aucun fait reconnu" in rendered


def test_public_path_keeps_employee_method_and_separates_deep_dossier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        router,
        "search_bible",
        lambda *_args, **_kwargs: {
            "sources_used": [],
            "points_to_verify": [],
        },
    )
    answer = router.ask("Quels sont mes droits sur mes horaires ?", 6, 6)

    assert answer["employee_method_analysis"]["source_hierarchy"][0] == (
        "Accords d'entreprise INEOS"
    )
    assert answer["disciplinary_assistance"] is None


def test_local_interface_exposes_two_distinct_employee_choices() -> None:
    html = (ROOT / "apps" / "nexus-local-interface" / "index.html").read_text(
        encoding="utf-8"
    )
    script = (ROOT / "apps" / "nexus-local-interface" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "Poser une question salarié" in html
    assert (
        "Obtenez une première analyse sur vos droits, votre contrat, vos horaires, "
        "votre paie, vos congés ou vos conditions de travail."
    ) in html
    assert "Préparer un entretien disciplinaire" in html
    assert (
        "Analysez une convocation, préparez la défense du salarié et construisez "
        "une stratégie avant, pendant et après l’entretien."
    ) in html
    assert 'data-employee-path="QUESTION_SALARIE"' in html
    assert 'data-employee-path="ASSISTANCE_ENTRETIEN_DISCIPLINAIRE"' in html
    assert "employee_path: currentEmployeePath" in script


def test_employee_questionnaire_collects_and_explicitly_exports_answers() -> None:
    html = (ROOT / "apps" / "nexus-local-interface" / "index.html").read_text(
        encoding="utf-8"
    )
    script = (ROOT / "apps" / "nexus-local-interface" / "app.js").read_text(
        encoding="utf-8"
    )

    assert 'id="employeeInterview"' in html
    assert 'id="downloadInterviewButton"' in html
    assert "Aucune sauvegarde automatique" in html
    assert "const employeeInterviewSections" in script
    assert "Principe appliqué" in script
    assert "employee_interview_answers: interviewAnswers" in script
    assert "function downloadInterview()" in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script


def test_local_interface_distinguishes_server_unavailable_from_raw_fetch_error() -> None:
    script = (ROOT / "apps" / "nexus-local-interface" / "app.js").read_text(
        encoding="utf-8"
    )

    assert (
        "Le serveur Nexus local ne répond pas. Relancez start-nexus-local.bat "
        "puis ouvrez http://127.0.0.1:8765/"
    ) in script
    assert 'new NexusRequestError("network", SERVER_UNAVAILABLE_MESSAGE)' in script
    assert "renderError(error.message)" not in script


def test_local_interface_has_a_specific_analysis_timeout() -> None:
    script = (ROOT / "apps" / "nexus-local-interface" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "const ANALYZE_TIMEOUT_MS" in script
    assert "new AbortController()" in script
    assert 'error?.name === "AbortError"' in script
    assert "Le délai d’analyse est dépassé." in script


def test_local_interface_reports_http_status_and_business_error_safely() -> None:
    script = (ROOT / "apps" / "nexus-local-interface" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "Erreur HTTP ${response.status}" in script
    assert "if (!response.ok)" in script
    assert "if (!payload.ok)" in script
    assert 'new NexusRequestError("business", businessMessage)' in script
    assert "Une erreur interne Nexus est survenue." in script


def test_local_interface_rejects_invalid_json_and_keeps_valid_payload() -> None:
    script = (ROOT / "apps" / "nexus-local-interface" / "app.js").read_text(
        encoding="utf-8"
    )

    assert "rawBody = await response.text()" in script
    assert "const payload = parseNexusResponse(rawBody)" in script
    assert "Le serveur Nexus a renvoyé une réponse invalide" in script
    assert 'new NexusRequestError("invalid_json", INVALID_SERVER_RESPONSE_MESSAGE)' in script
    assert "return payload;" in script
    assert "renderResult(payload)" in script


def test_local_launcher_refuses_a_silent_second_instance() -> None:
    launcher = (
        ROOT / "apps" / "nexus-local-interface" / "start-nexus-local.bat"
    ).read_text(encoding="utf-8")

    assert "TcpClient" in launcher
    assert "http://127.0.0.1:8765/health" in launcher
    assert "Une instance Nexus est deja active." in launcher
    assert "Le port 8765 est deja utilise par une autre application." in launcher
    assert 'if "%NEXUS_PORT_STATE%"=="0"' in launcher
    assert 'if "%NEXUS_PORT_STATE%"=="2"' in launcher


def test_server_passes_explicit_employee_path_to_router(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sys.path.insert(0, str(SERVER_PATH.parent))
    spec = importlib.util.spec_from_file_location("employee_paths_server", SERVER_PATH)
    assert spec and spec.loader
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    captured: dict[str, object] = {}

    def fake_run(command, **_kwargs):
        captured["command"] = command
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"ok": True}),
            stderr="",
        )

    monkeypatch.setattr(server.subprocess, "run", fake_run)
    server.run_router(
        "Préparer le dossier.",
        6,
        router.ASSISTANCE_ENTRETIEN_DISCIPLINAIRE,
    )

    command = captured["command"]
    assert "--employee-path" in command
    assert router.ASSISTANCE_ENTRETIEN_DISCIPLINAIRE in command
