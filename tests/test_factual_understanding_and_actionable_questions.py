from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
ROUTER_DIR = ROOT / "automation" / "scripts"
if str(ROUTER_DIR) not in sys.path:
    sys.path.insert(0, str(ROUTER_DIR))

import assistant_ds_router as router  # noqa: E402
from NEXUS_RUNTIME_INTEGRATION import sanitize_public_payload  # noqa: E402
from tools.run_real_business_cases_baseline import (  # noqa: E402
    ROUTE_BY_CASE,
    build_case_prompt,
    load_fixtures,
)
from tools.run_real_business_cases_second_baseline import (  # noqa: E402
    load_second_fixtures,
)


EXPECTED_CATEGORIES = {
    "REAL-01-INSULTING_EMAILS_ALCOHOL": "INSULTING_EMAILS",
    "REAL-02-SMOKING_BREAKS_SEVESO_BADGE": "BREAKS_AND_BADGE_CONTROL",
    "REAL-03-TAG_INSTALLATION": "INSULTING_TAG",
    "REAL-04-FORCED_DAY_TO_SHIFT_LABORATORY": "WORK_SCHEDULE_CHANGE",
    "REAL-05-DELEGATION_HOURS_CSSCT_INCOMPLETE": "CSSCT_MEETING_TIME",
    "REAL-06-ANNUAL_LEAVE_TEN_PERCENT_UNRESOLVED": "AMBIGUOUS_TEN_PERCENT_RULE",
    "REAL-07-SAFETY_PPE_UNAVAILABLE_OR_UNSUITABLE": "PPE_AVAILABILITY_OR_SUITABILITY",
    "REAL-08-TEMPORARY_DAY_TO_THREE_SHIFT_REFUSAL": "WORK_SCHEDULE_CHANGE",
    "REAL-09-CHEMICAL_RECIPE_OUTDATED_PROCEDURE": "TECHNICAL_ERROR_AND_OUTDATED_PROCEDURE",
    "REAL-10-POSITIVE_ALCOHOL_TEST_HIGH_RISK_POSITION": "POSITIVE_ALCOHOL_TEST",
    "REAL-11-INSULTS_SUPERVISOR_FATIGUE_CONTEXT": "INSULTING_BEHAVIOR",
}


@pytest.fixture(autouse=True)
def offline_connectors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        router,
        "search_bible",
        lambda *_args, **_kwargs: {"sources_used": [], "points_to_verify": []},
    )
    monkeypatch.setattr(router, "bridge", None)
    monkeypatch.setattr(router, "legifrance", None)
    monkeypatch.setattr(router, "judilibre", None)
    monkeypatch.setattr(router, "cdtn", None)


def all_fixtures() -> tuple[dict, ...]:
    return (*load_fixtures(), *load_second_fixtures())


def path_for(fixture: dict) -> str:
    return str(
        fixture["case_input"].get("requested_path")
        or ROUTE_BY_CASE[fixture["case_id"]]
    )


def answer_for(fixture: dict) -> dict:
    return router.ask(
        build_case_prompt(fixture),
        6,
        6,
        path_for(fixture),
    )


def test_all_eleven_cases_preserve_requested_path_and_primary_category() -> None:
    fixtures = all_fixtures()

    assert len(fixtures) == 11
    for fixture in fixtures:
        answer = answer_for(fixture)
        core = answer["case_factual_core"]
        assert answer["route"]["employee_path"] == path_for(fixture)
        assert core["requested_path"] == path_for(fixture)
        assert core["event_category"] == EXPECTED_CATEGORIES[fixture["case_id"]]
        assert core["primary_event"]
        assert core["primary_grievance_or_decision"]
        assert core["confidence_level"] in {"LOW", "MEDIUM", "HIGH"}


def test_real_01_keeps_insulting_emails_primary_and_alcohol_secondary() -> None:
    fixture = next(
        item for item in all_fixtures()
        if item["case_id"] == "REAL-01-INSULTING_EMAILS_ALCOHOL"
    )
    core = answer_for(fixture)["case_factual_core"]

    assert "courriels insultants" in core["primary_grievance_or_decision"].casefold()
    assert any("alcool" in item.casefold() for item in core["secondary_topics"])
    assert "alcool" not in core["primary_grievance_or_decision"].casefold()


def test_real_02_keeps_breaks_and_badge_purpose_with_control_checks() -> None:
    fixture = next(
        item for item in all_fixtures()
        if item["case_id"] == "REAL-02-SMOKING_BREAKS_SEVESO_BADGE"
    )
    answer = answer_for(fixture)
    rendered = json.dumps(answer["actionable_preparation"], ensure_ascii=False).casefold()

    assert "pauses" in answer["case_factual_core"][
        "primary_grievance_or_decision"
    ].casefold()
    for marker in ("finalité", "cnil", "cse"):
        assert marker in rendered


def test_real_03_tag_does_not_become_threat_or_repeated_harassment() -> None:
    fixture = next(
        item for item in all_fixtures()
        if item["case_id"] == "REAL-03-TAG_INSTALLATION"
    )
    answer = answer_for(fixture)
    core = answer["case_factual_core"]

    assert core["event_category"] == "INSULTING_TAG"
    assert "tag" in core["primary_grievance_or_decision"].casefold()
    assert "menace ou violence" not in core["primary_grievance_or_decision"].casefold()
    assert "harcèlement répété" not in json.dumps(core, ensure_ascii=False).casefold()


def test_real_04_does_not_import_unrelated_shift_facts() -> None:
    fixture = next(
        item for item in all_fixtures()
        if item["case_id"] == "REAL-04-FORCED_DAY_TO_SHIFT_LABORATORY"
    )
    answer = answer_for(fixture)
    generated = json.dumps(
        {
            "core": answer["case_factual_core"],
            "preparation": answer["actionable_preparation"],
        },
        ensure_ascii=False,
    ).casefold()

    for forbidden in ("repos de neuf heures", "sncc", "provox", "climatisation"):
        assert forbidden not in generated
    assert "rythme posté" in answer["case_factual_core"][
        "primary_grievance_or_decision"
    ].casefold()


def test_real_05_is_incomplete_and_never_switches_to_discipline() -> None:
    fixture = next(
        item for item in all_fixtures()
        if item["case_id"] == "REAL-05-DELEGATION_HOURS_CSSCT_INCOMPLETE"
    )
    answer = answer_for(fixture)

    assert answer["route"]["employee_path"] == router.QUESTION_SALARIE
    assert answer["disciplinary_assistance"] is None
    assert answer["route"]["analysis_suspended"] is True
    assert any(
        "partie manquante" in item.casefold()
        for item in answer["case_factual_core"]["blocking_ambiguities"]
    )


def test_real_06_stops_and_asks_definition_before_analysis() -> None:
    fixture = next(
        item for item in all_fixtures()
        if item["case_id"] == "REAL-06-ANNUAL_LEAVE_TEN_PERCENT_UNRESOLVED"
    )
    answer = answer_for(fixture)
    first = answer["actionable_preparation"]["questions_for_employee"][0]

    assert answer["route"]["analysis_suspended"] is True
    assert first["question"].startswith("Que désigne exactement")
    assert answer["short_answer"].startswith(first["question"])
    assert "legifrance_code_travail" not in answer["route"]["engines"]
    assert "judilibre_jurisprudence" not in answer["route"]["engines"]


@pytest.mark.parametrize(
    ("case_id", "primary_marker", "required_markers"),
    [
        (
            "REAL-07-SAFETY_PPE_UNAVAILABLE_OR_UNSUITABLE",
            "epi",
            ("disponibles", "adaptation", "stock"),
        ),
        (
            "REAL-08-TEMPORARY_DAY_TO_THREE_SHIFT_REFUSAL",
            "temporaire",
            ("contrat", "familiale", "volontaires"),
        ),
        (
            "REAL-09-CHEMICAL_RECIPE_OUTDATED_PROCEDURE",
            "procédure",
            ("version", "journaux", "contrôle croisé"),
        ),
        (
            "REAL-10-POSITIVE_ALCOHOL_TEST_HIGH_RISK_POSITION",
            "alcoolémie",
            ("contre-expertise", "calibration", "règlement intérieur"),
        ),
        (
            "REAL-11-INSULTS_SUPERVISOR_FATIGUE_CONTEXT",
            "insultants",
            ("mots exacts", "repos", "excuses"),
        ),
    ],
)
def test_second_set_keeps_primary_fact_and_actionable_evidence(
    case_id: str,
    primary_marker: str,
    required_markers: tuple[str, ...],
) -> None:
    fixture = next(item for item in all_fixtures() if item["case_id"] == case_id)
    answer = answer_for(fixture)
    core = answer["case_factual_core"]
    preparation = json.dumps(
        answer["actionable_preparation"], ensure_ascii=False
    ).casefold()

    assert primary_marker in core["primary_grievance_or_decision"].casefold()
    for marker in required_markers:
        assert marker in preparation


def test_actionable_questions_are_short_structured_unique_and_capped() -> None:
    required = {
        "question",
        "target",
        "purpose",
        "priority",
        "answer_type",
        "changes_analysis_if",
        "follow_up",
    }
    for fixture in all_fixtures():
        preparation = answer_for(fixture)["actionable_preparation"]
        rows = [
            *preparation["questions_for_employee"],
            *preparation["questions_for_employer"],
            *preparation["representative_checks"],
        ]
        normalized = [row["question"].casefold().strip() for row in rows]

        assert len(normalized) == len(set(normalized))
        assert all(set(row) == required for row in rows)
        assert all(len(row["question"]) <= 130 for row in rows)
        assert all(row["target"] in {"EMPLOYEE", "EMPLOYER", "DOCUMENT"} for row in rows)
        assert all(
            row["priority"] in {"BLOCKING", "HIGH", "MEDIUM", "LOW"}
            for row in rows
        )
        assert sum(row["priority"] == "BLOCKING" for row in rows) <= 5
        assert sum(row["priority"] == "HIGH" for row in rows) <= 8
        assert sum(
            row["priority"] in {"MEDIUM", "LOW"} for row in rows
        ) <= 5
        assert all(row["purpose"] and row["changes_analysis_if"] for row in rows)


def test_no_case_specific_identifier_or_cross_scenario_payload_in_engine() -> None:
    source = (
        ROOT / "SYNDICAL_REASONING_ENGINE" / "factual_core.py"
    ).read_text(encoding="utf-8")

    assert "REAL-01" not in source
    assert "REAL-11" not in source
    assert "SNCC" not in source
    assert "PROVOX" not in source


def test_temporary_shift_case_does_not_import_pay_or_collective_headcount() -> None:
    fixture = next(
        item for item in all_fixtures()
        if item["case_id"] == "REAL-08-TEMPORARY_DAY_TO_THREE_SHIFT_REFUSAL"
    )
    answer = answer_for(fixture)
    rendered = json.dumps(answer, ensure_ascii=False).casefold()

    assert "rémunération supérieure" not in rendered
    assert "effectifs avant/après" not in rendered


def test_public_factual_payload_is_compact_and_keeps_field_work_sheet() -> None:
    fixture = next(
        item for item in all_fixtures()
        if item["case_id"] == "REAL-03-TAG_INSTALLATION"
    )
    internal = {
        "ok": True,
        "answer": answer_for(fixture),
        "final_assistant_runtime": {"mode": "DISABLED", "assistant": None},
    }
    public = sanitize_public_payload(internal)
    serialized = json.dumps(public, ensure_ascii=False).encode("utf-8")

    assert len(serialized) < 50_000
    assert public["orchestration"]["questions_utiles"]
    assert public["analysis_report"]["sections"]
    assert public["expert_juriste"]["active"] is True
    assert public["answer"]["case_factual_core"]["event_category"] == "INSULTING_TAG"


def test_factual_fix_results_cover_unchanged_eleven_case_baseline() -> None:
    output = (
        ROOT
        / "tests"
        / "fixtures"
        / "real_business_cases"
        / "factual_fix_baseline"
    )
    results = json.loads(
        (output / "factual-fix-results.json").read_text(encoding="utf-8")
    )
    raw = sorted((output / "raw").glob("*.response.json"))

    assert results["case_count"] == 11
    assert results["score_average_after"] > 55
    assert results["cases_with_factual_understanding_at_least_14"] >= 9
    assert len(raw) == 11
    assert all(
        json.loads(path.read_text(encoding="utf-8"))[
            "evaluation_data_exposed_to_nexus"
        ]
        is False
        for path in raw
    )


def test_connector_inventory_is_complete_honest_and_factually_targeted() -> None:
    inventory_path = (
        ROOT
        / "tests"
        / "fixtures"
        / "real_business_cases"
        / "factual_fix_baseline"
        / "connector-usage-inventory.json"
    )
    payload = json.loads(inventory_path.read_text(encoding="utf-8"))
    connectors = {
        item["connector_platform_id"]: item for item in payload["connectors"]
    }
    registered = {
        "legifrance",
        "judilibre",
        "cdtn",
        "cnil",
        "carsat",
        "anact",
        "inrs",
        "dreets_grand_est",
        "alsace_moselle_local_law",
        "france_chimie",
        "defenseur_droits",
        "ministere_travail",
        "service_public",
        "assurance_maladie",
        "urssaf",
        "agirc_arrco",
    }

    assert set(connectors) == registered
    assert payload["execution_observation"][
        "official_runtime_results_exploited"
    ] == 0
    assert "REAL-02" in connectors["cnil"]["expected_cases"]
    assert {
        "finalité du badgeage",
        "information des salariés",
        "durée de conservation",
        "utilisation disciplinaire des données",
    } <= set(connectors["cnil"]["expected_topics"])
    assert {"REAL-03", "REAL-07", "REAL-11"} <= set(
        connectors["carsat"]["expected_cases"]
    )
    assert connectors["carsat"]["source_nature"] == "PREVENTION_PRACTICE"
    assert connectors["cdtn"]["source_nature"] == "EDUCATIONAL_GUIDANCE"
    assert "ne remplace" in connectors["cdtn"]["expected_condition"]
    assert all(
        item["results_exploited"] == 0
        for item in connectors.values()
        if not item["available"]
    )
