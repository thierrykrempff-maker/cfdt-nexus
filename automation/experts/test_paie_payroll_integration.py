#!/usr/bin/env python
"""Integration tests for PayrollRuleEngine inside the Paie expert."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from automation.experts import paie, report_generator  # noqa: E402


def answer(query: str, context: dict[str, Any] | None = None, domains: list[str] | None = None) -> dict[str, Any]:
    return {
        "query": query,
        "route": {"domains": domains or []},
        "sources": [
            {
                "document": "Source locale de test",
                "source_layer": "accord_entreprise",
                "source_layer_label": "Accord entreprise",
            }
        ],
        "source_layers": [],
        "confidence": "faible",
        "documents_to_request": [],
        "payroll_rule_context": context or {},
    }


def selected_ids(payload: dict[str, Any]) -> set[str]:
    analysis = payload["payroll_rule_analysis"]
    return {str(item["rule_id"]) for item in analysis.get("selected_rules", [])}


def missing_variables(payload: dict[str, Any]) -> set[str]:
    analysis = payload["payroll_rule_analysis"]
    return set(str(item) for item in analysis["variables"].get("missing", []))


def documents_to_request(payload: dict[str, Any]) -> set[str]:
    analysis = payload["payroll_rule_analysis"]
    return set(str(item) for item in analysis.get("documents_to_request", []))


def report_markdown(expert_paie: dict[str, Any]) -> str:
    report = report_generator.build_report(
        {
            "answer": answer("Question de test"),
            "orchestration": {
                "question_posee": "Question de test",
                "experts_mobilises": ["Expert Paie V0"],
                "domaines_detectes": ["paie_remuneration"],
                "niveau_de_confiance": "faible",
            },
            "expert_juriste": {"active": False},
            "expert_paie": expert_paie,
        }
    )
    return report["markdown"]


def enrich_with_engine_report(report: Any) -> dict[str, Any]:
    previous = paie.payroll_rule_engine

    class MalformedEngine:
        @staticmethod
        def classify_query(query: str, context: dict[str, Any] | None = None) -> list[str]:
            return ["heures_supplementaires"]

        @staticmethod
        def analyze_payroll_query(query: str, context: dict[str, Any] | None = None) -> Any:
            return report

    paie.payroll_rule_engine = MalformedEngine()
    try:
        return paie.enrich(answer("Mes heures supplementaires ne sont pas payees."))
    finally:
        paie.payroll_rule_engine = previous


def assert_paie_payload_survives_malformed_engine(payload: dict[str, Any]) -> dict[str, Any]:
    assert payload["active"] is True
    assert payload["elements_du_bulletin_concernes"]
    assert payload["donnees_necessaires_au_calcul"]
    assert payload["calcul_detaille"].startswith("Non produit")
    analysis = payload["payroll_rule_analysis"]
    assert isinstance(analysis, dict)
    assert analysis["calculation_ready"] is False
    assert isinstance(analysis["warnings"], list)
    markdown = report_markdown(payload)
    assert isinstance(markdown, str)
    return analysis


def test_overtime_unpaid_keeps_legacy_fields_and_blocks_calculation() -> None:
    payload = paie.enrich(
        answer(
            "J'ai fait 6 heures supplementaires non payees sur mon bulletin.",
            {"variables": {"overtime_hours": 6}, "documents": ["bulletin de paie", "planning"]},
        )
    )
    assert payload["active"] is True
    assert payload["elements_du_bulletin_concernes"]
    assert payload["donnees_necessaires_au_calcul"]
    assert "PAY_HSUP_TRANCHES_001" in selected_ids(payload)
    assert "base_horaire" in missing_variables(payload)
    assert payload["payroll_rule_analysis"]["calculation_ready"] is False


def test_overtime_display_stays_targeted() -> None:
    payload = paie.enrich(
        answer(
            "J'ai fait 6 heures supplementaires non payees sur mon bulletin.",
            {"variables": {"overtime_hours": 6}, "documents": ["bulletin de paie", "planning"]},
        )
    )
    ids = selected_ids(payload)
    assert ids == {"PAY_HSUP_TRANCHES_001"}
    assert not any(rule_id.startswith("LEAVE_") or "MALADIE" in rule_id for rule_id in ids)
    assert "base_horaire" in missing_variables(payload)


def test_two_nights_and_sunday_in_5x8_requests_hour_details_without_calculation() -> None:
    payload = paie.enrich(
        answer(
            "J'ai travaille deux nuits et un dimanche en 5x8.",
            {"employee_population": "personnel poste", "work_schedule": "5x8"},
        )
    )
    analysis = payload["payroll_rule_analysis"]
    assert payload["active"] is True
    assert {"nuit", "dimanche", "5x8"} <= set(analysis["query_topics"])
    assert any("heure de debut" in item for item in payload["donnees_necessaires_au_calcul"])
    assert analysis["calculation_ready"] is False


def test_late_roster_change_identifies_rule_and_missing_replaced_posts() -> None:
    payload = paie.enrich(
        answer(
            "On m'a change de couleur trois jours avant en 5x8.",
            {"employee_population": "personnel poste", "work_schedule": "5x8"},
        )
    )
    assert "WT_CHANGEMENT_ROULEMENT_PREVENANCE_001" in selected_ids(payload)
    assert "nombre_postes_remplaces" in missing_variables(payload)
    assert payload["payroll_rule_analysis"]["calculation_ready"] is False


def test_refused_leave_uses_payroll_rule_engine_without_legacy_paie_domain() -> None:
    payload = paie.enrich(
        answer(
            "Mon conge a ete refuse alors que je l'ai demande 10 jours avant.",
            {"variables": {"date_demande": "2026-07-01", "date_debut_conge": "2026-07-11"}},
            domains=[],
        )
    )
    assert payload["active"] is True
    assert "LEAVE_CP_REQUEST_DELAY_001" in selected_ids(payload)
    assert len(payload["payroll_rule_analysis"]["selected_rules"]) <= 6
    assert payload["payroll_rule_analysis"]["calculation_ready"] is False


def test_refused_leave_filters_counter_rules_and_kelio_documents() -> None:
    payload = paie.enrich(
        answer(
            "Mon conge a ete refuse alors que je l'ai demande 10 jours avant.",
            {"variables": {"date_demande": "2026-07-01", "date_debut_conge": "2026-07-11"}},
            domains=[],
        )
    )
    ids = selected_ids(payload)
    assert ids == {"LEAVE_CP_REQUEST_DELAY_001"}
    assert not any(token in rule_id for rule_id in ids for token in ["RJFJ", "RJFN", "JR_", "RCTP", "RCTR"])
    requested = documents_to_request(payload)
    assert "demande_conge" in requested
    assert "reponse_hierarchie" in requested
    assert "releve_kelio" not in requested
    assert "arret_de_travail" not in requested


def test_rjfj_counter_requests_kelio_without_rctp_rctr_overselection() -> None:
    payload = paie.enrich(
        answer(
            "Pourquoi RH m'a retire des jours de mon RJFJ ?",
            {"employee_population": "personnel poste", "work_schedule": "5x8"},
        )
    )
    ids = selected_ids(payload)
    assert "WT_5X8_RJFJ_TO_JR_001" in ids
    assert "WT_5X8_RJFJ_RJFN_USAGE_001" in ids
    assert "WT_5X8_RCTP_001" not in ids
    assert "WT_5X8_RCTR_001" not in ids
    assert "releve_kelio" in payload["payroll_rule_analysis"]["documents_to_request"]
    assert payload["payroll_rule_analysis"]["calculation_ready"] is False


def test_rjfj_counter_display_stays_targeted() -> None:
    payload = paie.enrich(
        answer(
            "Pourquoi RH m'a retire des jours de mon RJFJ ?",
            {"employee_population": "personnel poste", "work_schedule": "5x8"},
        )
    )
    ids = selected_ids(payload)
    assert {"WT_5X8_RJFJ_TO_JR_001", "WT_5X8_RJFJ_RJFN_USAGE_001"} <= ids
    assert not any(rule_id.startswith("LEAVE_CP") or "MALADIE" in rule_id for rule_id in ids)
    assert "WT_5X8_RCTP_001" not in ids
    assert "WT_5X8_RCTR_001" not in ids
    assert "releve_kelio" in documents_to_request(payload)


def test_sickness_rule_requests_payslip_without_calculation() -> None:
    payload = paie.enrich(
        answer(
            "Je veux verifier mon maintien de salaire pendant mon arret maladie.",
            {
                "variables": {
                    "anciennete": "5 ans",
                    "date_debut_arret": "2026-02-01",
                    "duree_arret": "10 jours",
                },
                "documents": ["arret maladie"],
            },
        )
    )
    assert "PAY_MALADIE_MAINTIEN_001" in selected_ids(payload)
    assert "bulletin_de_paie" in payload["payroll_rule_analysis"]["documents_to_request"]
    assert payload["payroll_rule_analysis"]["calculation_ready"] is False


def test_sickness_display_filters_leave_rules() -> None:
    payload = paie.enrich(
        answer(
            "Je veux verifier mon maintien de salaire pendant mon arret maladie.",
            {
                "variables": {
                    "anciennete": "5 ans",
                    "date_debut_arret": "2026-02-01",
                    "duree_arret": "10 jours",
                },
                "documents": ["arret maladie"],
            },
        )
    )
    ids = selected_ids(payload)
    assert ids == {"PAY_MALADIE_MAINTIEN_001"}
    assert not any(rule_id.startswith("LEAVE_CP") for rule_id in ids)
    requested = documents_to_request(payload)
    assert "bulletin_de_paie" in requested
    assert "demande_conge" not in requested
    assert "reponse_hierarchie" not in requested


def test_thirteenth_month_identifies_missing_reference_salary() -> None:
    payload = paie.enrich(answer("Je veux verifier mon 13e mois.", {"variables": {"presence": "annee complete"}}))
    assert "PAY_13E_MOIS_001" in selected_ids(payload)
    assert "salaire_reference" in missing_variables(payload)
    assert "bulletin_de_paie" in payload["payroll_rule_analysis"]["documents_to_request"]
    assert payload["payroll_rule_analysis"]["calculation_ready"] is False


def test_catalog_error_keeps_legacy_paie_behavior() -> None:
    previous = paie.payroll_rule_engine

    class BrokenEngine:
        @staticmethod
        def classify_query(query: str, context: dict[str, Any] | None = None) -> list[str]:
            return ["heures_supplementaires"]

        @staticmethod
        def analyze_payroll_query(query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
            raise RuntimeError("catalogue invalide de test")

    paie.payroll_rule_engine = BrokenEngine()
    try:
        payload = paie.enrich(answer("Mes heures supplementaires ne sont pas payees."))
    finally:
        paie.payroll_rule_engine = previous

    assert payload["active"] is True
    assert payload["elements_du_bulletin_concernes"]
    assert payload["calcul_detaille"].startswith("Non produit")
    assert payload["payroll_rule_analysis"]["engine_available"] is False
    assert any("catalogue invalide de test" in item for item in payload["payroll_rule_analysis"]["warnings"])


def test_malformed_engine_reports_do_not_crash_and_keep_legacy_paie_fields() -> None:
    malformed_reports = [
        None,
        [],
        {"variables": []},
        {"variables": "bad"},
        {"warnings": "bad"},
        {"selected_rules": "bad"},
        {"documents_to_request": {}},
        {"calculation_ready": "true"},
        {"confidence": "inconnue"},
        {
            "query_topics": "bad",
            "selected_rules": {"not": "a list"},
            "candidate_rules": "bad",
            "rejected_rules": "bad",
            "variables": {"present": [], "missing": "bad", "ambiguous": {"not": "a list"}},
            "warnings": {"not": "a list"},
            "documents_to_request": {},
            "calculation_ready": "true",
            "confidence": {"not": "a string"},
        },
    ]
    for report in malformed_reports:
        payload = enrich_with_engine_report(report)
        analysis = assert_paie_payload_survives_malformed_engine(payload)
        assert analysis["calculation_ready"] is False
        assert analysis["confidence"] == "faible"


def test_malformed_rule_items_are_ignored_or_safely_normalized() -> None:
    payload = enrich_with_engine_report(
        {
            "query_topics": ["heures_supplementaires"],
            "selected_rules": [
                None,
                "bad",
                12,
                {
                    "rule_id": "PARTIAL_RULE",
                    "title": "Regle partielle",
                    "matched_topics": ["heures_supplementaires"],
                    "required_variables": ["base_horaire"],
                },
            ],
            "candidate_rules": ["bad", {"rule_id": "PARTIAL_RULE", "matched_topics": ["heures_supplementaires"]}],
            "rejected_rules": [None, "bad", 42, {"rule_id": "REJECTED_RULE", "details": "bad"}],
            "variables": {"present": "bad", "missing": ["base_horaire"], "ambiguous": "bad"},
            "warnings": "bad",
            "documents_to_request": {},
            "calculation_ready": "true",
            "confidence": "inconnue",
        }
    )
    analysis = assert_paie_payload_survives_malformed_engine(payload)
    assert [rule["rule_id"] for rule in analysis["selected_rules"]] == ["PARTIAL_RULE"]
    assert analysis["selected_rules"][0]["source_document"] is None
    assert analysis["variables"]["present"] == {}
    assert analysis["variables"]["missing"] == ["base_horaire"]
    assert "bad" in analysis["warnings"]
    assert analysis["confidence"] == "faible"


def test_unexpected_normalization_error_uses_safe_fallback() -> None:
    previous_normalizer = paie.normalize_filtered_payroll_rule_analysis

    def broken_normalizer(report: dict[str, Any], query: str, context: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("normalisation impossible de test")

    paie.normalize_filtered_payroll_rule_analysis = broken_normalizer
    try:
        payload = enrich_with_engine_report({"query_topics": ["heures_supplementaires"]})
    finally:
        paie.normalize_filtered_payroll_rule_analysis = previous_normalizer

    analysis = assert_paie_payload_survives_malformed_engine(payload)
    assert analysis["engine_available"] is False
    assert any("payroll_rule_normalization_error" in item for item in analysis["warnings"])


def test_no_payroll_subject_does_not_add_noise() -> None:
    payload = paie.enrich(answer("Bonjour, je veux organiser une reunion d'equipe.", domains=[]))
    assert payload["active"] is False
    assert "payroll_rule_analysis" not in payload


def test_report_contains_readable_ineos_payroll_section() -> None:
    paie_payload = paie.enrich(answer("Je veux verifier mon 13e mois.", {"variables": {"presence": "annee complete"}}))
    report = report_generator.build_report(
        {
            "answer": answer("Je veux verifier mon 13e mois.", {"variables": {"presence": "annee complete"}}),
            "orchestration": {
                "question_posee": "Je veux verifier mon 13e mois.",
                "experts_mobilises": ["Expert Paie V0"],
                "domaines_detectes": ["paie_remuneration"],
                "niveau_de_confiance": "faible",
            },
            "expert_juriste": {"active": False},
            "expert_paie": paie_payload,
        }
    )
    markdown = report["markdown"]
    assert "Analyse Paie INEOS" in markdown
    assert "PAY_13E_MOIS_001" in markdown
    assert "Calcul automatique: non execute dans le LOT 3" in markdown


def test_report_stays_prudent_even_when_engine_marks_ready() -> None:
    markdown = report_markdown(
        {
            "active": True,
            "objet_du_controle": "Controle test",
            "elements_du_bulletin_concernes": [],
            "methode_de_controle": [],
            "calcul_detaille": "Non produit.",
            "payroll_rule_analysis": {
                "query_topics": ["treizieme_mois"],
                "selected_rules": [{"rule_id": "SYNTH_READY", "title": "Regle synthetique", "status": "active"}],
                "variables": {"present": {"salaire_reference": 1000}, "missing": [], "ambiguous": []},
                "documents_to_request": [],
                "calculation_ready": True,
                "warnings": [],
                "confidence": "elevee",
            },
        }
    )
    assert "Calcul automatique: non execute dans le LOT 3" in markdown
    assert "pret techniquement" not in markdown
    assert "disponible" not in markdown


def test_report_hides_empty_or_malformed_payroll_rule_section() -> None:
    base = {
        "active": True,
        "objet_du_controle": "Controle test",
        "elements_du_bulletin_concernes": [],
        "methode_de_controle": [],
        "calcul_detaille": "Non produit.",
    }
    assert "Analyse Paie INEOS" not in report_markdown(base)
    assert "Analyse Paie INEOS" not in report_markdown({**base, "payroll_rule_analysis": {}})
    assert "Analyse Paie INEOS" not in report_markdown({**base, "payroll_rule_analysis": None})
    assert "Analyse Paie INEOS" not in report_markdown({**base, "payroll_rule_analysis": "mal forme"})
    assert "Analyse Paie INEOS" not in report_markdown({**base, "payroll_rule_analysis": []})


def test_report_shows_useful_payroll_rule_section_signals() -> None:
    base = {
        "active": True,
        "objet_du_controle": "Controle test",
        "elements_du_bulletin_concernes": [],
        "methode_de_controle": [],
        "calcul_detaille": "Non produit.",
    }
    assert "Analyse Paie INEOS" in report_markdown({**base, "payroll_rule_analysis": {"warnings": ["warning utile"]}})
    assert "Analyse Paie INEOS" in report_markdown(
        {**base, "payroll_rule_analysis": {"engine_available": False, "warnings": ["catalogue indisponible"]}}
    )
    assert "Analyse Paie INEOS" in report_markdown(
        {**base, "payroll_rule_analysis": {"documents_to_request": ["bulletin_de_paie"]}}
    )


def test_real_catalog_never_sets_calculation_ready_in_integration_scenarios() -> None:
    scenarios = [
        answer("J'ai fait 6 heures supplementaires non payees.", {"variables": {"overtime_hours": 6}}),
        answer("J'ai travaille deux nuits et un dimanche en 5x8.", {"employee_population": "personnel poste", "work_schedule": "5x8"}),
        answer("On m'a change de couleur trois jours avant en 5x8.", {"employee_population": "personnel poste", "work_schedule": "5x8"}),
        answer("Mon conge a ete refuse alors que je l'ai demande 10 jours avant.", {"variables": {"date_demande": "2026-07-01", "date_debut_conge": "2026-07-11"}}),
        answer("Pourquoi RH m'a retire des jours de mon RJFJ ?", {"employee_population": "personnel poste", "work_schedule": "5x8"}),
        answer("Je veux verifier mon maintien de salaire pendant mon arret maladie.", {"variables": {"anciennete": "5 ans"}}),
        answer("Je veux verifier mon 13e mois.", {"variables": {"presence": "annee complete"}}),
    ]
    ready = []
    for item in scenarios:
        payload = paie.enrich(item)
        if payload.get("payroll_rule_analysis", {}).get("calculation_ready"):
            ready.append(item["query"])
    assert ready == []


def run_all() -> None:
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
            print(f"OK {name}")


if __name__ == "__main__":
    run_all()
