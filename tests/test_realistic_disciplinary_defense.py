from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "automation" / "scripts"))

import assistant_ds_router as router  # noqa: E402
from SYNDICAL_REASONING_ENGINE import (  # noqa: E402
    DisciplinaryActCategory,
    DisciplinaryReasoningEngine,
    SyndicalCaseInput,
    extract_disciplinary_facts,
)


@pytest.fixture
def offline_router(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        router,
        "search_bible",
        lambda *_args, **_kwargs: {"sources_used": [], "points_to_verify": []},
    )
    monkeypatch.setattr(router, "bridge", None)
    monkeypatch.setattr(router, "legifrance", None)
    monkeypatch.setattr(router, "judilibre", None)
    monkeypatch.setattr(router, "cdtn", None)
    return router


def ask_disciplinary(offline_router, question: str) -> dict:
    return offline_router.ask(
        question,
        8,
        8,
        offline_router.ASSISTANCE_ENTRETIEN_DISCIPLINAIRE,
    )["disciplinary_assistance"]


def serialized(value: object) -> str:
    return json.dumps(value, ensure_ascii=False).casefold()


@pytest.mark.parametrize(
    ("question", "expected"),
    (
        ("Erreur de manipulation technique.", DisciplinaryActCategory.TECHNICAL_ERROR),
        ("Refus d'exécuter un ordre.", DisciplinaryActCategory.INSUBORDINATION),
        ("Absence injustifiée et retard.", DisciplinaryActCategory.ABSENCE_OR_LATENESS),
        ("Propos grossiers et injure.", DisciplinaryActCategory.INSULTING_OR_INAPPROPRIATE_BEHAVIOR),
        ("Menace de violence.", DisciplinaryActCategory.THREAT_OR_VIOLENCE),
        ("Harcèlement allégué.", DisciplinaryActCategory.ALLEGED_HARASSMENT),
        ("Dégradation matérielle.", DisciplinaryActCategory.MATERIAL_DAMAGE),
        ("Manquement à la sécurité.", DisciplinaryActCategory.SAFETY_BREACH),
        ("Usage abusif des outils informatiques.", DisciplinaryActCategory.IT_MISUSE),
        ("Faute liée à l'alcool.", DisciplinaryActCategory.ALCOHOL_OR_DRUGS),
        ("Conflit interpersonnel.", DisciplinaryActCategory.INTERPERSONAL_CONFLICT),
        ("Faits non détaillés.", DisciplinaryActCategory.UNSPECIFIED_FACTS),
    ),
)
def test_all_required_act_categories_are_distinguished(question, expected) -> None:
    assert extract_disciplinary_facts(question).act_category is expected


def test_recognized_gross_tag_without_identified_target_uses_realistic_defense(
    offline_router,
) -> None:
    report = ask_disciplinary(
        offline_router,
        (
            "Le salarié reconnaît avoir écrit « fils de pute » sur une installation "
            "de l'entreprise après une journée difficile dans une ambiance dégradée. "
            "L'inscription ne visait personne en particulier."
        ),
    )

    facts = report["fact_extraction"]
    assert facts["act_category"] == "INSULTING_OR_INAPPROPRIATE_BEHAVIOR"
    assert facts["employee_admission"] is True
    assert facts["target_identified"] is False
    assert facts["exact_words_or_behavior"] == "fils de pute"
    assert report["5_main_defense_line"]["employee_position"] == "faits reconnus"
    assert "reconnaît un geste déplacé" in report["5_main_defense_line"]["strategy"]
    text = serialized(
        {
            "facts": report["fact_extraction"],
            "questions": report["6_questions_for_employee"],
            "strategy": report["5_main_defense_line"],
        }
    )
    for forbidden in (
        "technical_error",
        "training_failure",
        "procedure_error",
        "safety_incident",
        "formation technique",
        "habilitation",
        "erreur de manipulation",
    ):
        assert forbidden not in text


def test_contested_gross_tag_prioritizes_attribution_and_evidence(
    offline_router,
) -> None:
    report = ask_disciplinary(
        offline_router,
        (
            "Le salarié conteste être l'auteur d'un tag grossier sur un mur de "
            "l'entreprise. La direction évoque seulement une suspicion et aucune photo."
        ),
    )

    assert report["fact_extraction"]["employee_admission"] is False
    assert report["5_main_defense_line"]["employee_position"] == "attribution contestée"
    strategy = report["5_main_defense_line"]["strategy"]
    assert "simple suspicion" in strategy
    assert "preuve de l'attribution" in strategy
    assert "faire reconnaître" not in strategy


def test_insult_clearly_targeting_manager_increases_risk(offline_router) -> None:
    report = ask_disciplinary(
        offline_router,
        (
            "Le salarié a tenu des propos injurieux visant clairement son supérieur "
            "hiérarchique devant plusieurs collègues."
        ),
    )

    facts = report["fact_extraction"]
    assert facts["act_category"] == "INSULTING_OR_INAPPROPRIATE_BEHAVIOR"
    assert facts["target_identified"] is True
    assert facts["target_type"] == "supérieur hiérarchique"
    assert "personne précisément visée" in report["4_real_disciplinary_risk"][
        "aggravating_factors"
    ]


def test_isolated_words_without_prior_warning_are_mitigating(
    offline_router,
) -> None:
    report = ask_disciplinary(
        offline_router,
        (
            "Il s'agit d'un propos grossier isolé. Le salarié n'a aucun antécédent "
            "disciplinaire et n'a jamais été sanctionné."
        ),
    )

    facts = report["fact_extraction"]
    assert facts["repetition"] is False
    assert facts["prior_warnings"] is False
    mitigating = report["4_real_disciplinary_risk"]["mitigating_factors"]
    assert "fait présenté comme isolé" in mitigating
    assert "absence d'antécédent indiquée" in mitigating


def test_repeated_words_with_prior_warning_are_aggravating(
    offline_router,
) -> None:
    report = ask_disciplinary(
        offline_router,
        (
            "Les propos grossiers se sont répétés plusieurs fois. Un avertissement "
            "antérieur avait déjà été notifié pour des faits similaires."
        ),
    )

    facts = report["fact_extraction"]
    assert facts["repetition"] is True
    assert facts["prior_warnings"] is True
    aggravating = report["4_real_disciplinary_risk"]["aggravating_factors"]
    assert "faits répétés" in aggravating
    assert "antécédent disciplinaire indiqué" in aggravating


def test_gross_inscription_with_material_damage_separates_damage(
    offline_router,
) -> None:
    report = ask_disciplinary(
        offline_router,
        (
            "Le salarié reconnaît une inscription injurieuse sur un équipement de "
            "l'entreprise. Elle a causé une dégradation et un coût de remise en état."
        ),
    )

    assert (
        report["fact_extraction"]["act_category"]
        == "INSULTING_OR_INAPPROPRIATE_BEHAVIOR"
    )
    assert report["fact_extraction"]["material_damage"] is True
    assert "dégradation matérielle alléguée" in report["4_real_disciplinary_risk"][
        "aggravating_factors"
    ]


def test_real_technical_manipulation_error_keeps_technical_questions() -> None:
    analysis = DisciplinaryReasoningEngine().analyze(
        SyndicalCaseInput(
            "Entretien disciplinaire après une erreur de manipulation technique sur une machine."
        )
    )

    assert (
        analysis.fact_extraction.act_category
        is DisciplinaryActCategory.TECHNICAL_ERROR
    )
    questions = " ".join(item.question for item in analysis.automatic_questions)
    assert "formations" in questions
    assert "habilitations" in questions


def test_ambiguous_disciplinary_interview_stays_undetermined(
    offline_router,
) -> None:
    report = ask_disciplinary(
        offline_router,
        "Le salarié est convoqué à un entretien disciplinaire mais les faits ne sont pas précisés.",
    )

    assert report["fact_extraction"]["act_category"] == "UNSPECIFIED_FACTS"
    assert report["5_main_defense_line"]["employee_position"] == (
        "position du salarié à établir"
    )
    conclusion = report["4_real_disciplinary_risk"]["provisional_conclusion"]
    assert "trop tôt" in conclusion
    text = serialized(
        {
            "qualification": report["3_provisional_qualification"]["wording"],
            "risk": report["4_real_disciplinary_risk"],
            "strategy": report["5_main_defense_line"],
        }
    )
    for forbidden in ("dossier plutôt favorable", "dossier défavorable", "aucune faute", "faute grave"):
        assert forbidden not in text


def test_disciplinary_report_has_requested_structure_and_no_duplicate_questions(
    offline_router,
) -> None:
    report = ask_disciplinary(
        offline_router,
        "Le salarié reconnaît un tag grossier qui ne visait personne en particulier.",
    )

    assert list(report)[3:] == [
        "1_facts_understood",
        "2_points_to_verify",
        "3_provisional_qualification",
        "4_real_disciplinary_risk",
        "5_main_defense_line",
        "6_questions_for_employee",
        "7_questions_for_management",
        "8_interview_preparation",
        "9_points_not_to_say",
        "10_after_interview",
    ]
    employee_questions = report["6_questions_for_employee"]
    management_questions = report["7_questions_for_management"]
    assert len(employee_questions) == len(set(employee_questions))
    assert len(management_questions) == len(set(management_questions))


def test_irrelevant_disciplinary_sources_are_excluded() -> None:
    route = router.route_query(
        "Entretien disciplinaire pour une inscription grossière qui ne visait personne.",
        router.ASSISTANCE_ENTRETIEN_DISCIPLINAIRE,
    )

    def source(document: str, excerpt: str, layer: str) -> dict:
        return router.normalize_source(
            {
                "document": document,
                "excerpt": excerpt,
                "source_layer": layer,
                "score": 100,
            },
            "test",
        )

    selected = router.select_final_sources(
        [
            source(
                "Règlement intérieur",
                "Respect des personnes, propos grossiers, inscriptions, dégradations et échelle des sanctions.",
                "accord_entreprise",
            ),
            source(
                "Communications électroniques",
                "Sanction disciplinaire liée à la messagerie professionnelle.",
                "accord_entreprise",
            ),
            source(
                "Formation et habilitation",
                "Erreur de manipulation et mode opératoire technique.",
                "accord_entreprise",
            ),
            source(
                "Harcèlement moral",
                "Agissements répétés constitutifs de harcèlement.",
                "jurisprudence",
            ),
            source(
                "Licenciement collectif",
                "Plan de sauvegarde de l'emploi et licenciements collectifs.",
                "convention_collective",
            ),
        ],
        route,
        8,
    )

    rendered = serialized(selected)
    assert "règlement intérieur" in rendered
    for forbidden in (
        "communications électroniques",
        "formation et habilitation",
        "harcèlement moral",
        "licenciement collectif",
    ):
        assert forbidden not in rendered


def test_judilibre_query_targets_factually_comparable_insult_cases() -> None:
    query, theme = router.judilibre_query_for_route(
        "Sanction pour un graffiti contenant une injure non adressée directement.",
        {
            "domains": ["disciplinaire"],
            "query": "Sanction pour un graffiti contenant une injure non adressée directement.",
        },
    )

    for expected in ("injure", "propos grossiers", "graffiti", "fait isolé", "absence antécédent"):
        assert expected in query
    assert "Propos injurieux" in theme


def test_local_interface_renders_the_ten_disciplinary_sections() -> None:
    script = (
        ROOT / "apps" / "nexus-local-interface" / "app.js"
    ).read_text(encoding="utf-8")
    for key in (
        "1_facts_understood",
        "2_points_to_verify",
        "3_provisional_qualification",
        "4_real_disciplinary_risk",
        "5_main_defense_line",
        "6_questions_for_employee",
        "7_questions_for_management",
        "8_interview_preparation",
        "9_points_not_to_say",
        "10_after_interview",
    ):
        assert key in script
