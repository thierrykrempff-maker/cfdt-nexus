#!/usr/bin/env python
"""Local tests for the PayrollRule selection engine."""

from __future__ import annotations

import copy
import json
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from automation.payroll import payroll_rule_engine as engine  # noqa: E402
from automation.payroll import payroll_rule_validator as validator  # noqa: E402


CATALOG = engine.load_validated_catalog()
RULES = CATALOG["rules"]


def rule(rule_id: str) -> dict[str, object]:
    return engine.get_rule_by_id(RULES, rule_id)


def assert_selected(report: dict[str, object], rule_id: str) -> dict[str, object]:
    for item in report["selected_rules"]:
        if item["rule_id"] == rule_id:
            return item
    raise AssertionError(f"Expected selected rule {rule_id}: {json.dumps(report, indent=2, ensure_ascii=False)}")


def assert_rejected(report: dict[str, object], rule_id: str, reason: str | None = None) -> dict[str, object]:
    for item in report["rejected_rules"]:
        if item["rule_id"] == rule_id and (reason is None or item["reason"] == reason):
            return item
    raise AssertionError(f"Expected rejected rule {rule_id}: {json.dumps(report, indent=2, ensure_ascii=False)}")


def selected_ids(report: dict[str, object]) -> set[str]:
    return {item["rule_id"] for item in report["selected_rules"]}


def calculable_copy(rule_id: str) -> dict[str, object]:
    item = copy.deepcopy(rule(rule_id))
    item["calculation_allowed"] = True
    item["status"] = "active"
    item["source_layer"] = "accord_entreprise"
    item["legal_priority"] = "opposable"
    item["effective_date"] = "2026-01-01"
    item["end_date"] = None
    item["confidence"] = "high"
    return item


def complete_context_for(item: dict[str, object]) -> dict[str, object]:
    return {
        "employee_population": "tous",
        "employment_category": "tous",
        "variables": {variable: "x" for variable in item.get("required_variables", [])},
    }


def complete_context_for_rules(*items: dict[str, object]) -> dict[str, object]:
    variables: dict[str, object] = {}
    for item in items:
        for variable in item.get("required_variables", []):
            variables[variable] = "x"
    return {
        "employee_population": "tous",
        "employment_category": "tous",
        "variables": variables,
    }


def test_load_validated_catalog_keeps_metadata() -> None:
    catalog = engine.load_validated_catalog()
    assert catalog["catalog_id"]
    assert catalog["version"]
    assert len(catalog["rules"]) == 23


def test_load_invalid_catalog_is_refused() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "invalid.json"
        path.write_text(json.dumps({"catalog_id": "bad", "version": "x", "scope": "test", "rules": "bad"}), encoding="utf-8")
        try:
            engine.load_validated_catalog(catalog_path=path)
        except ValueError as exc:
            assert "Invalid payroll rule catalog" in str(exc) or "Invalid payroll catalog" in str(exc)
        else:
            raise AssertionError("Invalid catalog should be refused")


def test_load_empty_catalog_is_refused() -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "empty.json"
        path.write_text(
            json.dumps({"catalog_id": "empty", "version": "x", "scope": "test", "rules": []}),
            encoding="utf-8",
        )
        try:
            engine.load_validated_catalog(catalog_path=path)
        except ValueError as exc:
            assert "no rules available" in str(exc)
        else:
            raise AssertionError("Empty catalog should be refused")


def test_get_unknown_rule_is_refused() -> None:
    try:
        engine.get_rule_by_id(RULES, "UNKNOWN_RULE")
    except KeyError as exc:
        assert "UNKNOWN_RULE" in str(exc)
    else:
        raise AssertionError("Unknown rule_id should raise")


def test_classification_does_not_treat_mise_a_pied_as_payroll() -> None:
    topics = engine.classify_query("La direction veut me mettre a pied.")
    assert topics == []


def test_overtime_unpaid_missing_hourly_rate() -> None:
    report = engine.analyze_payroll_query(
        "J'ai fait 6 heures en plus et elles ne sont pas payees.",
        {
            "employee_population": "personnel de jour",
            "variables": {"overtime_hours": 6},
            "documents": ["bulletin de paie", "planning"],
        },
    )
    assert_selected(report, "PAY_HSUP_TRANCHES_001")
    assert "heures_supplementaires" in report["query_topics"]
    assert "base_horaire" in report["variables"]["missing"]
    assert "bulletin_de_paie" in report["documents_present"]
    assert "planning" in report["documents_present"]
    assert report["calculation_ready"] is False


def test_two_nights_and_sunday_in_5x8_are_qualified_without_calculation() -> None:
    report = engine.analyze_payroll_query(
        "J'ai travaille deux nuits et un dimanche en 5x8.",
        {
            "employee_population": "personnel poste",
            "work_schedule": "5x8",
            "documents": ["planning"],
        },
    )
    assert "nuit" in report["query_topics"]
    assert "dimanche" in report["query_topics"]
    assert "5x8" in report["query_topics"]
    assert report["calculation_ready"] is False
    assert "planning" in report["documents_present"]
    assert not any(item["matched_topics"] == ["5x8"] for item in report["candidate_rules"])
    assert report["calculation_ready"] is False


def test_late_color_change_selects_roulement_rule() -> None:
    report = engine.analyze_payroll_query(
        "On m'a change de couleur trois jours avant.",
        {
            "employee_population": "personnel poste",
            "work_schedule": "5x8",
            "variables": {"notice_date": "2026-06-01", "date_changement": "2026-06-04"},
            "documents": ["planning"],
        },
    )
    assert_selected(report, "WT_CHANGEMENT_ROULEMENT_PREVENANCE_001")
    assert "changement_roulement" in report["query_topics"]
    assert "nombre_postes_remplaces" in report["variables"]["missing"]
    assert report["calculation_ready"] is False


def test_refused_leave_selects_leave_delay_rule() -> None:
    report = engine.analyze_payroll_query(
        "Mon conge a ete refuse alors que je l'ai demande 10 jours avant.",
        {
            "variables": {"date_demande": "2026-07-01", "date_debut_conge": "2026-07-11"},
            "documents": ["demande de conge", "reponse hierarchie"],
        },
    )
    assert_selected(report, "LEAVE_CP_REQUEST_DELAY_001")
    assert "conges_payes" in report["query_topics"]
    assert "demande_conge" in report["documents_present"]
    assert report["calculation_ready"] is False


def test_rjfj_counter_requests_kelio_capture() -> None:
    report = engine.analyze_payroll_query(
        "Pourquoi RH m'a retire des jours de mon RJFJ ?",
        {"employee_population": "personnel poste", "work_schedule": "5x8"},
    )
    ids = selected_ids(report)
    assert "WT_5X8_RJFJ_TO_JR_001" in ids
    assert "WT_5X8_RJFJ_RJFN_USAGE_001" in ids
    assert "releve_kelio" in report["documents_to_request"]
    assert any("verifier" in warning for warning in report["warnings"])
    assert report["calculation_ready"] is False


def test_sickness_selects_maintenance_rule_and_requests_payslip() -> None:
    report = engine.analyze_payroll_query(
        "Je veux verifier mon maintien de salaire pendant mon arret maladie.",
        {
            "variables": {
                "anciennete": "5 ans",
                "date_debut_arret": "2026-05-01",
                "duree_arret": "12 jours",
            },
            "documents": ["arret de travail"],
        },
    )
    assert_selected(report, "PAY_MALADIE_MAINTIEN_001")
    assert "bulletin_de_paie" in report["documents_to_request"]
    assert "salaire_reference" in report["variables"]["missing"]
    assert report["calculation_ready"] is False


def test_thirteenth_month_missing_reference_salary() -> None:
    report = engine.analyze_payroll_query(
        "Je veux verifier mon 13e mois.",
        {"variables": {"presence": "annee complete"}},
    )
    assert_selected(report, "PAY_13E_MOIS_001")
    assert "salaire_reference" in report["variables"]["missing"]
    assert report["calculation_ready"] is False


def test_kilometric_allowance_keeps_to_verify_warning() -> None:
    report = engine.analyze_payroll_query(
        "Je veux verifier mon indemnite kilometrique.",
        {
            "variables": {
                "round_trip_km": 40,
                "jours_travailles": 12,
                "taux_applicable": {"value": "a confirmer", "confirmed": False},
            }
        },
    )
    assert_selected(report, "PAY_INDEMNITE_KM_2023_001")
    assert report["variables"]["ambiguous"]
    assert report["calculation_ready"] is False
    assert any("verifier" in warning for warning in report["warnings"])


def test_incompatible_posted_holiday_rule_is_rejected_for_day_worker() -> None:
    report = engine.analyze_payroll_query(
        "J'ai travaille un jour ferie poste.",
        {"employee_population": "personnel de jour", "work_schedule": "jour"},
    )
    assert_selected(report, "PAY_HOLIDAY_DAY_WORKED_001")
    assert_rejected(report, "PAY_HOLIDAY_POSTED_NORMAL_001", "population_incompatible")
    assert_rejected(report, "PAY_HOLIDAY_POSTED_REST_001", "population_incompatible")


def test_company_memory_rule_is_never_selected() -> None:
    memory_rule = copy.deepcopy(rule("PAY_13E_MOIS_001"))
    memory_rule["rule_id"] = "MEMORY_TEST_RULE"
    memory_rule["source_layer"] = "memoire_entreprise"
    memory_rule["document_type"] = "pv_cse"
    memory_rule["historical_only"] = True
    memory_rule["legal_priority"] = "memory_only"
    report = engine.analyze_payroll_query("Verifier le 13e mois.", {}, rules=[memory_rule])
    assert report["selected_rules"] == []
    assert_rejected(report, "MEMORY_TEST_RULE", "historical_or_memory_source")
    assert report["historical_rules"]
    assert report["calculation_ready"] is False


def test_empty_context_does_not_crash() -> None:
    report = engine.analyze_payroll_query("Je veux comprendre mes conges payes.", {})
    assert report["query_topics"]
    assert report["candidate_rules"]
    assert report["calculation_ready"] is False


def test_wrong_population_rejects_specific_rule() -> None:
    report = engine.analyze_payroll_query(
        "Pourquoi mon RCTP 5x8 a change ?",
        {"employee_population": "personnel de jour", "work_schedule": "jour"},
    )
    assert_rejected(report, "WT_5X8_RCTP_001", "population_incompatible")


def test_date_out_of_period_rejects_rule() -> None:
    expired = copy.deepcopy(rule("PAY_13E_MOIS_001"))
    expired["effective_date"] = "2020-01-01"
    expired["end_date"] = "2020-12-31"
    report = engine.analyze_payroll_query(
        "Verifier mon 13e mois.",
        {"reference_date": "2026-01-01"},
        rules=[expired],
    )
    assert_rejected(report, "PAY_13E_MOIS_001", "date_out_of_period")


def test_expired_status_is_rejected() -> None:
    expired = copy.deepcopy(rule("PAY_13E_MOIS_001"))
    expired["status"] = "expired"
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", {}, rules=[expired])
    assert_rejected(report, "PAY_13E_MOIS_001", "status_expired")


def test_superseded_status_is_rejected() -> None:
    superseded = copy.deepcopy(rule("PAY_13E_MOIS_001"))
    superseded["status"] = "superseded"
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", {}, rules=[superseded])
    assert_rejected(report, "PAY_13E_MOIS_001", "status_superseded")


def test_disputed_status_is_selected_with_warning() -> None:
    disputed = copy.deepcopy(rule("PAY_13E_MOIS_001"))
    disputed["status"] = "disputed"
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", {}, rules=[disputed])
    selected = assert_selected(report, "PAY_13E_MOIS_001")
    assert any("contestee" in warning for warning in selected["warnings"])


def test_to_verify_rule_is_selected_with_warning() -> None:
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", {})
    selected = assert_selected(report, "PAY_13E_MOIS_001")
    assert any("verifier" in warning for warning in selected["warnings"])


def test_multiple_concurrent_rules_are_kept() -> None:
    report = engine.analyze_payroll_query(
        "Je veux verifier mon indemnite kilometrique et la distance retenue.",
        {"variables": {"round_trip_km": 40}},
    )
    ids = selected_ids(report)
    assert "PAY_INDEMNITE_KM_2023_001" in ids
    assert "PAY_INDEMNITE_KM_DISTANCE_2026_001" in ids


def test_no_sufficient_data_keeps_calculation_refused() -> None:
    report = engine.analyze_payroll_query("Verifier mes heures supplementaires.", {})
    assert_selected(report, "PAY_HSUP_TRANCHES_001")
    assert report["variables"]["missing"]
    assert report["calculation_ready"] is False


def test_complete_context_still_refuses_when_calculation_not_allowed() -> None:
    report = engine.analyze_payroll_query(
        "Verifier mon 13e mois.",
        {
            "variables": {
                "salaire_reference": 3000,
                "presence": "annee complete",
                "mois_paiement": "decembre",
                "montant_deja_verse": 0,
            }
        },
    )
    assert_selected(report, "PAY_13E_MOIS_001")
    assert report["variables"]["missing"] == []
    assert report["calculation_ready"] is False


def test_calculation_ready_blocks_to_verify_rule() -> None:
    item = calculable_copy("PAY_13E_MOIS_001")
    item["status"] = "to_verify"
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", complete_context_for(item), rules=[item])
    assert_selected(report, "PAY_13E_MOIS_001")
    assert report["calculation_ready"] is False


def test_calculation_ready_blocks_disputed_rule() -> None:
    item = calculable_copy("PAY_13E_MOIS_001")
    item["status"] = "disputed"
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", complete_context_for(item), rules=[item])
    assert_selected(report, "PAY_13E_MOIS_001")
    assert report["calculation_ready"] is False


def test_calculation_ready_blocks_pratique_officielle() -> None:
    item = calculable_copy("PAY_13E_MOIS_001")
    item["source_layer"] = "pratique_officielle"
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", complete_context_for(item), rules=[item])
    assert_selected(report, "PAY_13E_MOIS_001")
    assert report["calculation_ready"] is False


def test_calculation_ready_blocks_memoire_entreprise() -> None:
    item = calculable_copy("PAY_13E_MOIS_001")
    item["source_layer"] = "memoire_entreprise"
    item["historical_only"] = True
    item["legal_priority"] = "memory_only"
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", complete_context_for(item), rules=[item])
    assert report["selected_rules"] == []
    assert report["calculation_ready"] is False


def test_calculation_ready_blocks_missing_effective_date() -> None:
    item = calculable_copy("PAY_13E_MOIS_001")
    item["effective_date"] = None
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", complete_context_for(item), rules=[item])
    assert_selected(report, "PAY_13E_MOIS_001")
    assert report["calculation_ready"] is False


def test_calculation_ready_blocks_future_effective_date() -> None:
    item = calculable_copy("PAY_13E_MOIS_001")
    item["effective_date"] = "2099-01-01"
    context = complete_context_for(item)
    context["reference_date"] = "2026-01-01"
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", context, rules=[item])
    assert_rejected(report, "PAY_13E_MOIS_001", "rule_not_yet_effective")
    assert report["calculation_ready"] is False
    assert any("rule_not_yet_effective" in warning for warning in report["warnings"])


def test_calculation_ready_allows_effective_date_equal_reference_date() -> None:
    item = calculable_copy("PAY_13E_MOIS_001")
    context = complete_context_for(item)
    context["reference_date"] = "2026-01-01"
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", context, rules=[item])
    assert_selected(report, "PAY_13E_MOIS_001")
    assert report["calculation_ready"] is True


def test_calculation_ready_blocks_incompatible_selected_rules() -> None:
    first = calculable_copy("PAY_13E_MOIS_001")
    second = copy.deepcopy(first)
    second["rule_id"] = "PAY_13E_MOIS_CONFLICT_002"
    second["calculation_formula"]["expression"] = "Formule concurrente incompatible pour le meme 13e mois."
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", complete_context_for(first), rules=[first, second])
    assert len(report["selected_rules"]) == 2
    assert report["calculation_ready"] is False
    assert report["rule_conflict"]["has_conflict"] is True
    assert report["rule_conflict"]["conflicting_rule_ids"] == ["PAY_13E_MOIS_001", "PAY_13E_MOIS_CONFLICT_002"]
    assert any("PAY_13E_MOIS_001" in warning and "PAY_13E_MOIS_CONFLICT_002" in warning for warning in report["warnings"])


def test_thirteenth_month_and_paid_leave_do_not_conflict() -> None:
    thirteenth_month = calculable_copy("PAY_13E_MOIS_001")
    paid_leave = calculable_copy("LEAVE_CP_ACQUISITION_001")
    context = complete_context_for_rules(thirteenth_month, paid_leave)
    report = engine.analyze_payroll_query(
        "Verifier mon 13e mois et mes conges payes.",
        context,
        rules=[thirteenth_month, paid_leave],
    )
    assert selected_ids(report) == {"PAY_13E_MOIS_001", "LEAVE_CP_ACQUISITION_001"}
    assert report["rule_conflict"]["has_conflict"] is False
    assert report["calculation_ready"] is True


def test_precise_overtime_contradiction_is_detected() -> None:
    first = calculable_copy("PAY_HSUP_TRANCHES_001")
    second = copy.deepcopy(first)
    second["rule_id"] = "PAY_HSUP_TRANCHES_CONFLICT_002"
    second["calculation_formula"]["expression"] = "Formule concurrente: majoration heures supplementaires differente."
    report = engine.analyze_payroll_query(
        "Verifier mes heures supplementaires.",
        complete_context_for_rules(first, second),
        rules=[first, second],
    )
    assert selected_ids(report) == {"PAY_HSUP_TRANCHES_001", "PAY_HSUP_TRANCHES_CONFLICT_002"}
    assert report["calculation_ready"] is False
    assert report["rule_conflict"]["has_conflict"] is True
    assert report["rule_conflict"]["conflicting_rule_ids"] == [
        "PAY_HSUP_TRANCHES_001",
        "PAY_HSUP_TRANCHES_CONFLICT_002",
    ]
    assert any(
        "PAY_HSUP_TRANCHES_001" in warning and "PAY_HSUP_TRANCHES_CONFLICT_002" in warning
        for warning in report["warnings"]
    )


def test_generic_day_topic_does_not_create_conflict() -> None:
    thirteenth_month = calculable_copy("PAY_13E_MOIS_001")
    sickness = calculable_copy("PAY_MALADIE_MAINTIEN_001")
    thirteenth_month["work_time_topic"] = ["jour"]
    sickness["work_time_topic"] = ["jour"]
    sickness["benefit_or_obligation"] = "droit_salarie"
    context = complete_context_for_rules(thirteenth_month, sickness)
    report = engine.analyze_payroll_query(
        "Verifier mon 13e mois et mon maintien de salaire en arret maladie.",
        context,
        rules=[thirteenth_month, sickness],
    )
    assert selected_ids(report) == {"PAY_13E_MOIS_001", "PAY_MALADIE_MAINTIEN_001"}
    assert report["rule_conflict"]["has_conflict"] is False
    assert report["calculation_ready"] is True


def test_generic_droit_salarie_consequence_does_not_conflict_when_topics_differ() -> None:
    thirteenth_month = calculable_copy("PAY_13E_MOIS_001")
    kilometres = calculable_copy("PAY_INDEMNITE_KM_2023_001")
    thirteenth_month["benefit_or_obligation"] = "droit_salarie"
    kilometres["benefit_or_obligation"] = "droit_salarie"
    context = complete_context_for_rules(thirteenth_month, kilometres)
    report = engine.analyze_payroll_query(
        "Verifier mon 13e mois et mon indemnite kilometrique.",
        context,
        rules=[thirteenth_month, kilometres],
    )
    assert selected_ids(report) == {"PAY_13E_MOIS_001", "PAY_INDEMNITE_KM_2023_001"}
    assert report["rule_conflict"]["has_conflict"] is False
    assert report["calculation_ready"] is True


def test_precise_same_subject_without_overlapping_period_does_not_conflict() -> None:
    old = calculable_copy("PAY_HSUP_TRANCHES_001")
    old["effective_date"] = "2020-01-01"
    old["end_date"] = "2020-12-31"
    new = copy.deepcopy(old)
    new["rule_id"] = "PAY_HSUP_TRANCHES_2021_002"
    new["effective_date"] = "2021-01-01"
    new["end_date"] = None
    new["calculation_formula"]["expression"] = "Formule heures supplementaires applicable depuis 2021."
    context = complete_context_for_rules(new)
    context["reference_date"] = "2021-06-01"
    report = engine.analyze_payroll_query("Verifier mes heures supplementaires.", context, rules=[old, new])
    assert_selected(report, "PAY_HSUP_TRANCHES_2021_002")
    assert_rejected(report, "PAY_HSUP_TRANCHES_001", "date_out_of_period")
    assert report["rule_conflict"]["has_conflict"] is False
    assert report["calculation_ready"] is True


def test_precise_same_subject_population_mismatch_is_rejected_before_conflict() -> None:
    posted = calculable_copy("PAY_HSUP_TRANCHES_001")
    day = copy.deepcopy(posted)
    posted["employee_population"] = ["personnel_poste"]
    day["rule_id"] = "PAY_HSUP_TRANCHES_JOUR_002"
    day["employee_population"] = ["personnel_jour"]
    day["calculation_formula"]["expression"] = "Formule heures supplementaires personnel de jour."
    context = complete_context_for_rules(posted)
    context["employee_population"] = "personnel poste"
    report = engine.analyze_payroll_query("Verifier mes heures supplementaires.", context, rules=[posted, day])
    assert_selected(report, "PAY_HSUP_TRANCHES_001")
    assert_rejected(report, "PAY_HSUP_TRANCHES_JOUR_002", "population_incompatible")
    assert report["rule_conflict"]["has_conflict"] is False
    assert report["calculation_ready"] is True


def test_calculation_ready_allows_compatible_main_and_complementary_rules() -> None:
    first = calculable_copy("PAY_13E_MOIS_001")
    second = copy.deepcopy(first)
    second["rule_id"] = "PAY_13E_MOIS_COMPLEMENT_002"
    second["benefit_or_obligation"] = "information"
    second["required_variables"] = []
    second["calculation_formula"]["expression"] = "Information complementaire compatible sur le calendrier."
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", complete_context_for(first), rules=[first, second])
    assert len(report["selected_rules"]) == 2
    assert report["rule_conflict"]["has_conflict"] is False
    assert report["calculation_ready"] is True


def test_population_mismatch_is_rejected_before_conflict_detection() -> None:
    first = calculable_copy("PAY_13E_MOIS_001")
    second = copy.deepcopy(first)
    first["employee_population"] = ["personnel_poste"]
    second["rule_id"] = "PAY_13E_MOIS_JOUR_002"
    second["employee_population"] = ["personnel_jour"]
    context = complete_context_for(first)
    context["employee_population"] = "personnel poste"
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", context, rules=[first, second])
    assert_selected(report, "PAY_13E_MOIS_001")
    assert_rejected(report, "PAY_13E_MOIS_JOUR_002", "population_incompatible")
    assert report["rule_conflict"]["has_conflict"] is False
    assert report["calculation_ready"] is True


def test_date_period_selects_only_applicable_rule_before_conflict_detection() -> None:
    old = calculable_copy("PAY_13E_MOIS_001")
    old["effective_date"] = "2020-01-01"
    old["end_date"] = "2020-12-31"
    new = copy.deepcopy(old)
    new["rule_id"] = "PAY_13E_MOIS_2021_002"
    new["effective_date"] = "2021-01-01"
    new["end_date"] = None
    context = complete_context_for(new)
    context["reference_date"] = "2021-06-01"
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", context, rules=[old, new])
    assert_selected(report, "PAY_13E_MOIS_2021_002")
    assert_rejected(report, "PAY_13E_MOIS_001", "date_out_of_period")
    assert report["rule_conflict"]["has_conflict"] is False
    assert report["calculation_ready"] is True


def test_calculation_ready_blocks_ambiguous_variable() -> None:
    item = calculable_copy("PAY_13E_MOIS_001")
    context = complete_context_for(item)
    context["variables"]["salaire_reference"] = "3000 ?"
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", context, rules=[item])
    assert_selected(report, "PAY_13E_MOIS_001")
    assert report["variables"]["ambiguous"]
    assert report["calculation_ready"] is False


def test_employment_category_cadres_rejected_for_non_cadres() -> None:
    item = copy.deepcopy(rule("PAY_13E_MOIS_001"))
    item["employment_category"] = ["cadres"]
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", {"employment_category": "non_cadres"}, rules=[item])
    assert_rejected(report, "PAY_13E_MOIS_001", "employment_category_incompatible")


def test_employment_category_non_cadres_rejected_for_cadres() -> None:
    item = copy.deepcopy(rule("PAY_13E_MOIS_001"))
    item["employment_category"] = ["non_cadres"]
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", {"employment_category": "cadres"}, rules=[item])
    assert_rejected(report, "PAY_13E_MOIS_001", "employment_category_incompatible")


def test_employment_category_ouvriers_rejected_for_cadres() -> None:
    item = copy.deepcopy(rule("PAY_13E_MOIS_001"))
    item["employment_category"] = ["ouvriers"]
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", {"employment_category": "cadres"}, rules=[item])
    assert_rejected(report, "PAY_13E_MOIS_001", "employment_category_incompatible")


def test_employment_category_tous_accepts_cadres() -> None:
    item = copy.deepcopy(rule("PAY_13E_MOIS_001"))
    item["employment_category"] = ["tous"]
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", {"employment_category": "cadres"}, rules=[item])
    assert_selected(report, "PAY_13E_MOIS_001")


def test_missing_specific_employment_category_adds_warning() -> None:
    item = copy.deepcopy(rule("PAY_13E_MOIS_001"))
    item["employment_category"] = ["cadres"]
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", {}, rules=[item])
    selected = assert_selected(report, "PAY_13E_MOIS_001")
    assert any("Categorie" in warning for warning in selected["warnings"])


def test_legal_priority_does_not_override_category_mismatch() -> None:
    item = copy.deepcopy(rule("PAY_13E_MOIS_001"))
    item["employment_category"] = ["cadres"]
    item["legal_priority"] = "opposable"
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", {"employment_category": "non_cadres"}, rules=[item])
    assert_rejected(report, "PAY_13E_MOIS_001", "employment_category_incompatible")


def test_kilometres_synonyms_detect_kilometric_allowance() -> None:
    assert "indemnite_kilometrique" in engine.classify_query("mes kilometres ne sont pas payes")
    assert "indemnite_kilometrique" in engine.classify_query("mes kilom\u00e8tres ne sont pas pay\u00e9s")
    assert "indemnite_kilometrique" in engine.classify_query("frais kilometriques domicile usine")
    assert "indemnite_kilometrique" in engine.classify_query("trajet domicile-usine")


def test_generic_repos_does_not_trigger_topic() -> None:
    assert engine.classify_query("je suis en repos") == []


def test_qualified_repos_topics_are_detected() -> None:
    assert "repos_compensateur" in engine.classify_query("repos compensateur heures supplementaires")
    assert "repos" in engine.classify_query("repos entre deux postes")
    assert "recuperation_jour_ferie" in engine.classify_query("recuperation jour ferie")


def test_rjfj_query_does_not_select_unrelated_5x8_rules() -> None:
    report = engine.analyze_payroll_query(
        "Pourquoi RH m'a retire des jours dans mon RJFJ ?",
        {"employee_population": "personnel poste", "work_schedule": "5x8"},
    )
    ids = selected_ids(report)
    assert "WT_5X8_RJFJ_TO_JR_001" in ids
    assert "WT_5X8_RJFJ_RJFN_USAGE_001" in ids
    assert "WT_5X8_RCTP_001" not in ids
    assert "WT_5X8_RCTR_001" not in ids
    assert "WT_CHANGEMENT_ROULEMENT_PREVENANCE_001" not in ids
    assert "PAY_HOLIDAY_POSTED_NORMAL_001" not in ids
    assert "PAY_HOLIDAY_POSTED_REST_001" not in ids


def test_zero_business_values_are_present() -> None:
    report = engine.analyze_payroll_query(
        "Verifier mes heures en plus.",
        {"variables": {"hours_worked": 0, "hourly_rate": 0}},
    )
    assert report["variables"]["present"]["heures_validees"]["value"] == 0
    assert report["variables"]["present"]["base_horaire"]["value"] == 0


def test_empty_planning_is_not_present_document() -> None:
    report = engine.analyze_payroll_query(
        "Verifier mes heures en plus.",
        {"planning_available": False, "documents": [""]},
    )
    assert "planning" not in report["documents_present"]


def test_conflicting_variable_aliases_are_ambiguous() -> None:
    report = engine.analyze_payroll_query(
        "Verifier mes heures en plus.",
        {"variables": {"hours_worked": 0, "heures_validees": 1}},
    )
    assert any(item["variable"] == "heures_validees" for item in report["variables"]["ambiguous"])


def test_conflicting_work_schedule_is_ambiguous() -> None:
    report = engine.analyze_payroll_query(
        "Pourquoi RH m'a retire des jours dans mon RJFJ ?",
        {"work_schedule": ["jour", "5x8"], "employee_population": "personnel poste"},
    )
    assert any(item["variable"] == "work_schedule" for item in report["variables"]["ambiguous"])


def test_ambiguous_date_marker_is_ambiguous() -> None:
    report = engine.analyze_payroll_query(
        "Je veux poser mes conges.",
        {"variables": {"date_demande": "2026-07-01 ?", "date_debut_conge": "2026-07-15"}},
    )
    assert any(item["variable"] == "date_demande" for item in report["variables"]["ambiguous"])


def test_kelio_counter_without_statement_date_is_ambiguous() -> None:
    report = engine.analyze_payroll_query(
        "Pourquoi RH m'a retire des jours dans mon RJFJ ?",
        {"employee_population": "personnel poste", "work_schedule": "5x8", "documents": ["compteur Kelio"]},
    )
    assert any(item["variable"] == "releve_kelio_date" for item in report["variables"]["ambiguous"])


def test_payslip_present_but_amount_missing_keeps_variable_missing() -> None:
    report = engine.analyze_payroll_query("Verifier mon 13e mois.", {"documents": ["bulletin de paie"]})
    assert "bulletin_de_paie" in report["documents_present"]
    assert "salaire_reference" in report["variables"]["missing"]


def test_no_relevant_rule_for_unknown_question() -> None:
    report = engine.analyze_payroll_query("Bonjour, question generale sans sujet paie.", {})
    assert report["query_topics"] == []
    assert report["candidate_rules"] == []
    assert report["selected_rules"] == []


def test_current_catalog_never_sets_calculation_ready() -> None:
    catalog = engine.load_validated_catalog()
    ready_rule_ids = []
    for item in catalog["rules"]:
        query = " ".join(item.get("payroll_topic", []) + item.get("leave_topic", []) + item.get("work_time_topic", []))
        context = {"variables": {variable: "x" for variable in item.get("required_variables", [])}}
        report = engine.analyze_payroll_query(query, context, rules=[item])
        if report["calculation_ready"]:
            ready_rule_ids.append(item["rule_id"])
    assert ready_rule_ids == []


def test_source_hierarchy_keeps_company_agreement_first() -> None:
    report = engine.analyze_payroll_query("Verifier mon jour ferie travaille.", {})
    assert report["source_hierarchy"][0] == "accord_entreprise"
    assert "memoire_entreprise" == report["source_hierarchy"][-1]


def test_catalog_still_validates_with_validator() -> None:
    catalog = validator.load_catalog()
    schema = validator.load_schema()
    report = validator.validate_catalog(catalog, schema=schema)
    assert report["valid"], report


def run_all() -> None:
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
            print(f"OK {name}")


if __name__ == "__main__":
    run_all()
