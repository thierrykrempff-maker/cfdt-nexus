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
