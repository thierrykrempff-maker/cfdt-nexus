#!/usr/bin/env python
"""Synthetic LOT 5C adapter from employee cases to Cockpit V3 JSON."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from automation.cases.employee_case import EmployeeCase, ExpertAnalysis, ExpertStatus
from automation.cases.employee_case_pipeline import PIPELINE_STEPS, EmployeeCasePipeline, load_fixture_cases
from automation.cases.employee_case_report import EmployeeCaseReportGenerator


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT / "automation" / "cases" / "fixtures" / "employee-cases.synthetic.json"

SCENARIOS: dict[str, dict[str, str]] = {
    "overtime-complete": {"case_id": "CASE_OVERTIME_SYN_001", "label": "Heures supplementaires - complet"},
    "on-call-incomplete": {"case_id": "CASE_ONCALL_SYN_002", "label": "Astreinte - incomplet"},
    "sickness-contradictory": {"case_id": "CASE_SICK_SYN_003", "label": "Maladie - pieces contradictoires"},
    "classification-missing-job": {"case_id": "CASE_CLASS_SYN_004", "label": "Classification - fiche de poste manquante"},
    "paid-leave-complete": {"case_id": "CASE_LEAVE_SYN_005", "label": "Conges payes - complet"},
}


def public_scenarios() -> list[dict[str, str]]:
    return [{"id": scenario_id, "label": value["label"]} for scenario_id, value in SCENARIOS.items()]


def _case_for_scenario(scenario_id: str) -> EmployeeCase:
    config = SCENARIOS.get(scenario_id)
    if config is None:
        raise KeyError("Dossier synthetique inconnu.")
    cases = {item.case_id: item for item in load_fixture_cases(FIXTURE_PATH)}
    employee_case = cases.get(config["case_id"])
    if employee_case is None or employee_case.privacy_probe:
        raise PermissionError("Donnee de demonstration refusee par le controle de confidentialite.")
    return employee_case


def _present_document_ids(employee_case: EmployeeCase) -> tuple[str, ...]:
    return tuple(item.document_id for item in employee_case.documents if item.availability.value == "present")


def synthetic_expert_analyses(employee_case: EmployeeCase) -> list[ExpertAnalysis]:
    documents = _present_document_ids(employee_case)
    incomplete = employee_case.case_id in {"CASE_ONCALL_SYN_002", "CASE_CLASS_SYN_004"}
    payroll_status = ExpertStatus.UNAVAILABLE if employee_case.case_id == "CASE_CLASS_SYN_004" else (
        ExpertStatus.REFUSED if incomplete else ExpertStatus.COMPLETED
    )
    legal_status = ExpertStatus.REFUSED if incomplete else ExpertStatus.COMPLETED
    refusal = "Impossible de conclure sans les pieces obligatoires indiquees." if incomplete else None
    payroll = ExpertAnalysis(
        expert="expert_paie",
        status=payroll_status,
        summary="Synthese paie fictive limitee aux pieces declarees.",
        findings=("Rapprochement documentaire a effectuer.",) if not incomplete else (),
        cited_rules_or_sources=("Source synthetique a confirmer",),
        documents_used=documents[:2],
        control_points=("Verifier la coherence entre les pieces presentes.",),
        risks=("Ne pas utiliser une valeur synthetique comme base de calcul.",),
        confidence="LOW" if incomplete else "HIGH",
        refusal_reason="Expert Paie indisponible pour ce scenario." if payroll_status is ExpertStatus.UNAVAILABLE else refusal,
        limits=("Aucun calcul de paie.",),
        period=employee_case.period,
    )
    legal = ExpertAnalysis(
        expert="juriste_travail",
        status=legal_status,
        summary="Synthese juridique fictive limitee aux sources declarees.",
        findings=("La source applicable doit etre verifiee.",) if not incomplete else (),
        cited_rules_or_sources=("Source synthetique a confirmer",),
        documents_used=documents[-2:],
        control_points=("Verifier le champ d'application des sources.",),
        risks=("Ne pas presenter cette synthese comme un avis definitif.",),
        confidence="LOW" if incomplete else "HIGH",
        refusal_reason=refusal,
        limits=("Aucun avis juridique definitif.",),
        period=employee_case.period,
    )
    return [payroll, legal]


def _completeness_rate(theme_completeness: dict[str, Any]) -> float:
    scores = [float(item.get("score_percent", 0)) for item in theme_completeness.values() if isinstance(item, dict)]
    return round(sum(scores) / len(scores), 2) if scores else 0.0


def build_demo_payload(scenario_id: str) -> dict[str, Any]:
    employee_case = _case_for_scenario(scenario_id)
    analyses = synthetic_expert_analyses(employee_case)
    pipeline_result = EmployeeCasePipeline().run(employee_case, analyses)
    if pipeline_result.get("final_status") in {"blocked", "failed"}:
        raise RuntimeError(str(pipeline_result.get("error") or "Pipeline dossier bloque."))

    pipeline_result["title"] = employee_case.title
    pipeline_result["confidentiality"] = employee_case.confidentiality.value
    pipeline_result["assumptions"] = list(employee_case.assumptions)
    report = EmployeeCaseReportGenerator().generate(pipeline_result, analyses)
    if not report.get("employee_view") or not report.get("expert_view"):
        raise RuntimeError("Rapport dossier indisponible.")

    context = pipeline_result["contexts"]["expert_paie"]
    completeness = context.get("theme_completeness") or {}
    diagnostic = pipeline_result["diagnostic"]
    case_data = employee_case.as_dict()
    case_data.pop("privacy_probe", None)
    return {
        "ok": True,
        "scenario": scenario_id,
        "available_scenarios": public_scenarios(),
        "case": case_data,
        "pipeline": {
            "steps": [{"id": step, "status": pipeline_result["steps"].get(step, "not_started")} for step in PIPELINE_STEPS],
            "final_status": pipeline_result["final_status"],
            "contexts": pipeline_result["contexts"],
        },
        "completeness": {
            "by_theme": completeness,
            "rate_percent": _completeness_rate(completeness),
            "notice": "Ce taux mesure uniquement la presence documentaire; ce n'est ni une probabilite de succes ni un niveau de conformite juridique.",
        },
        "themes_analyzed": list(diagnostic.get("themes_analyzed") or []),
        "themes_blocked": list(diagnostic.get("themes_blocked") or []),
        "contradictions": list(diagnostic.get("contradictions") or []),
        "diagnostic": diagnostic,
        "report": report,
        "employee_view": report["employee_view"],
        "expert_view": report["expert_view"],
        "report_metadata": report["sections"]["metadata"],
        "calculation_performed": False,
        "synthetic_only": True,
    }
