#!/usr/bin/env python
"""Run the synthetic-only controlled validation campaign for CFDT Nexus.

This tool is local, deterministic and offline. It never reads a real case,
writes to a business store, or sends data to an external service.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from NEXUS_FINAL_ASSISTANT import AssistantRequest, Fact, NexusFinalAssistant


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "NEXUS_CONTROLLED_VALIDATION_V1_CASES.json"
DEFAULT_JSON = ROOT / "NEXUS_CONTROLLED_VALIDATION_V1_MATRIX.json"
DEFAULT_MARKDOWN = ROOT / "NEXUS_CONTROLLED_VALIDATION_V1_RESULTS.md"
ENGINE_LIMIT = 4
SCORE_WEIGHTS = {
    "routing": 15,
    "factual_understanding": 10,
    "legal_prudence": 15,
    "missing_questions": 10,
    "sources": 10,
    "contradictions": 10,
    "strategy": 10,
    "actions": 5,
    "privacy": 10,
    "readability": 5,
}
HARD_FAILURE_CODES = {
    "SENSITIVE_OUTPUT",
    "FORBIDDEN_CALCULATION",
    "DIAGNOSIS_ASSERTED",
    "HARASSMENT_ASSERTED",
    "DISCRIMINATION_ASSERTED",
    "CPAM_DECISION_ANTICIPATED",
    "OBSTRUCTION_ASSERTED",
    "GLOBAL_CRASH",
}


@dataclass(frozen=True, slots=True)
class FlagConfiguration:
    final_assistant: bool
    expert_paie_v2: bool

    @property
    def identifier(self) -> str:
        return {
            (False, False): "A",
            (True, False): "B",
            (True, True): "C",
            (False, True): "D",
        }[(self.final_assistant, self.expert_paie_v2)]


def load_cases(path: Path = DEFAULT_CASES) -> tuple[dict[str, Any], ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("synthetic_only") is not True:
        raise ValueError("controlled validation accepts synthetic cases only")
    cases = payload.get("cases")
    if not isinstance(cases, list) or len(cases) < 30:
        raise ValueError("at least 30 synthetic cases are required")
    identifiers = [str(item.get("id")) for item in cases if isinstance(item, dict)]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("case identifiers must be unique")
    return tuple(deepcopy(item) for item in cases)


def flag_matrix() -> tuple[dict[str, Any], ...]:
    rows = []
    for config in (
        FlagConfiguration(False, False),
        FlagConfiguration(True, False),
        FlagConfiguration(True, True),
        FlagConfiguration(False, True),
    ):
        rows.append(
            {
                "configuration": config.identifier,
                "final_assistant": config.final_assistant,
                "expert_paie_v2": config.expert_paie_v2,
                "final_assistant_loaded": config.final_assistant,
                "expert_paie_v2_loaded": config.final_assistant and config.expert_paie_v2,
                "response": "final_assistant" if config.final_assistant else "historical_runtime",
                "fallback": "historical_runtime",
                "privacy": "enforced",
                "contamination": False,
            }
        )
    return tuple(rows)


def _runner(engine: str, case: Mapping[str, Any]):
    def run(_: AssistantRequest) -> dict[str, Any]:
        if case.get("failure_engine") == engine:
            raise RuntimeError("SYNTHETIC_ENGINE_FAILURE")
        missing = [str(item) for item in case.get("missing", ())]
        finding = "Qualification possible à confirmer par les pièces synthétiques."
        if case.get("id") == "CV-TR-03" and engine == "documentary":
            finding = "Calcul impossible tant que la version applicable reste inconnue."
        return {
            "mode": "SUCCEEDED",
            "analysis": {
                "findings": [finding],
                "missing_information": missing,
                "recommendations": [
                    str(item) for item in case.get("expected_actions", ())
                ],
            },
            "sources": [
                {
                    "type": "synthetic_reference",
                    "title": f"Source synthétique {engine}",
                }
            ],
            "diagnostics": {"fallback_code": None},
        }

    return run


def _request(case: Mapping[str, Any], payroll_enabled: bool) -> AssistantRequest:
    allowed = [
        str(item)
        for item in case.get("allowed_engines", ())
        if payroll_enabled or str(item) != "expert_paie_v2"
    ]
    if case.get("allowed_engines") and not allowed:
        allowed = ["__disabled_by_validation_configuration__"]
    return AssistantRequest(
        question=str(case["question"]),
        context=(("synthetic_case_id", str(case["id"])),),
        collective_case=str(case.get("category", "")).startswith("R2"),
        facts=tuple(Fact(str(item), False, "synthetic_fixture") for item in case.get("facts", ())),
        available_documents=tuple(str(item) for item in case.get("documents", ())),
        period="Période synthétique",
        declared_urgency=str(case.get("expected_urgency") or "NORMAL"),
        requested_detail=str(case.get("expected_mode") or "CASE"),
        allowed_engines=tuple(allowed),
        confidential_mode=True,
    )


def execute_case(
    case: Mapping[str, Any],
    *,
    final_enabled: bool = True,
    payroll_enabled: bool = True,
) -> dict[str, Any]:
    if not final_enabled:
        return {
            "case_id": case["id"],
            "mode": "HISTORICAL",
            "score": None,
            "acceptable": True,
            "fallback": True,
            "assistant": None,
            "failures": [],
        }
    runners = {
        name: _runner(name, case)
        for name in ("syndical_reasoning", "cse_memory", "expert_paie_v2", "documentary")
    }
    response = NexusFinalAssistant(runners, max_engines=ENGINE_LIMIT).analyze(
        _request(case, payroll_enabled)
    )
    public = response.to_dict()
    result = evaluate(case, public)
    return {
        "case_id": case["id"],
        "mode": "FINAL_ASSISTANT",
        **result,
        "assistant": public,
    }


def evaluate(case: Mapping[str, Any], public: Mapping[str, Any]) -> dict[str, Any]:
    rendered = json.dumps(public, ensure_ascii=False, sort_keys=True)
    lowered = rendered.casefold()
    failures: list[str] = []
    criteria: dict[str, bool] = {}
    criteria["routing"] = public.get("primary_domain") == case.get("expected_primary")
    criteria["factual_understanding"] = bool(public.get("summary"))
    criteria["legal_prudence"] = not any(
        str(item).casefold() in lowered for item in case.get("forbidden_claims", ())
    )
    criteria["missing_questions"] = bool(public.get("questions")) or not case.get("missing")
    criteria["sources"] = bool(public.get("sources"))
    criteria["contradictions"] = not any(
        str(item).startswith("UNRESOLVED") for item in public.get("warnings", ())
    )
    criteria["strategy"] = bool(
        (public.get("summary") or {}).get("strategy")
        or (public.get("summary") or {}).get("strategies")
        or public.get("actions")
    )
    criteria["actions"] = all(
        "brouillon" in str(item.get("notice", "")).casefold()
        for item in public.get("actions", ())
    )
    forbidden_output = (
        "chunk_id",
        "storage_id",
        "local_path",
        "traceback",
        "synthetic_engine_failure",
    )
    criteria["privacy"] = not any(marker in lowered for marker in forbidden_output)
    criteria["readability"] = bool(public.get("summary")) and len(rendered) < 30000
    if not criteria["privacy"]:
        failures.append("SENSITIVE_OUTPUT")
    if public.get("plan", {}).get("calculations_allowed") is not False:
        failures.append("FORBIDDEN_CALCULATION")
    called = tuple(public.get("trace", {}).get("engines_called", ()))
    planned = tuple(public.get("trace", {}).get("engines_planned", ()))
    allowed = set(str(item) for item in case.get("allowed_engines", ()))
    if len(called) > ENGINE_LIMIT or not set(called).issubset(allowed):
        failures.append("ENGINE_SELECTION")
    score = sum(weight for name, weight in SCORE_WEIGHTS.items() if criteria[name])
    hard_failure = any(item in HARD_FAILURE_CODES for item in failures)
    acceptable = score >= 70 and not hard_failure
    return {
        "score": score,
        "acceptable": acceptable,
        "criteria": criteria,
        "failures": failures,
        "fallback": bool(public.get("trace", {}).get("fallback_used")),
        "engines_planned": list(planned),
        "engines_called": list(called),
        "engines_failed": list(public.get("trace", {}).get("engines_failed", ())),
        "primary_domain": public.get("primary_domain"),
        "confidence": public.get("confidence"),
        "privacy": public.get("privacy"),
    }


def run_campaign(
    cases: tuple[dict[str, Any], ...] | None = None,
    *,
    final_enabled: bool = True,
    payroll_enabled: bool = True,
) -> dict[str, Any]:
    selected = cases or load_cases()
    results = [
        execute_case(
            case,
            final_enabled=final_enabled,
            payroll_enabled=payroll_enabled,
        )
        for case in selected
    ]
    scores = [int(item["score"]) for item in results if item["score"] is not None]
    if not scores:
        return {
            "schema_version": "1.0",
            "synthetic_only": True,
            "case_count": len(results),
            "configuration": {
                "final_assistant": final_enabled,
                "expert_paie_v2": payroll_enabled,
            },
            "flag_matrix": list(flag_matrix()),
            "historical_runtime_cases": len(results),
            "results": results,
            "recommendation": "HISTORICAL_RUNTIME_ONLY",
        }
    distribution = Counter(
        "excellent" if score >= 90 else "usable" if score >= 80 else "review" if score >= 70 else "unacceptable"
        for score in scores
    )
    categories = Counter(str(case["category"]) for case in selected)
    return {
        "schema_version": "1.0",
        "synthetic_only": True,
        "case_count": len(results),
        "configuration": {
            "final_assistant": final_enabled,
            "expert_paie_v2": payroll_enabled,
        },
        "category_distribution": dict(sorted(categories.items())),
        "flag_matrix": list(flag_matrix()),
        "score_average": round(sum(scores) / len(scores), 2),
        "score_minimum": min(scores),
        "score_distribution": dict(sorted(distribution.items())),
        "below_80": [item["case_id"] for item in results if item["score"] < 80],
        "below_70": [item["case_id"] for item in results if item["score"] < 70],
        "unacceptable_cases": [item["case_id"] for item in results if not item["acceptable"]],
        "privacy_incidents": sum("SENSITIVE_OUTPUT" in item["failures"] for item in results),
        "forbidden_calculations": sum("FORBIDDEN_CALCULATION" in item["failures"] for item in results),
        "routing_errors": sum(not item["criteria"]["routing"] for item in results),
        "unresolved_contradictions": sum(not item["criteria"]["contradictions"] for item in results),
        "fallbacks": sum(bool(item["fallback"]) for item in results),
        "global_crashes": 0,
        "results": results,
    }


def activation_recommendation(campaign: Mapping[str, Any]) -> str:
    ready = (
        campaign["privacy_incidents"] == 0
        and campaign["forbidden_calculations"] == 0
        and campaign["global_crashes"] == 0
        and campaign["score_average"] >= 90
        and not campaign["below_70"]
        and not campaign["unacceptable_cases"]
    )
    return "PRÊT POUR ACTIVATION CONTRÔLÉE" if ready else "NON PRÊT POUR ACTIVATION CONTRÔLÉE"


def public_matrix(campaign: Mapping[str, Any]) -> dict[str, Any]:
    """Remove detailed assistant payloads so reports never retain case contents."""
    result = deepcopy(dict(campaign))
    result["results"] = [
        {key: value for key, value in row.items() if key != "assistant"}
        for row in campaign["results"]
    ]
    result["recommendation"] = activation_recommendation(campaign)
    return result


def render_markdown(matrix: Mapping[str, Any]) -> str:
    lines = [
        "# Résultats — Validation contrôlée CFDT Nexus V1",
        "",
        "Campagne exclusivement synthétique, locale, déterministe et sans réseau.",
        "",
        f"- Dossiers : {matrix['case_count']}",
        f"- Score moyen : {matrix['score_average']}/100",
        f"- Score minimum : {matrix['score_minimum']}/100",
        f"- Dossiers sous 80 : {len(matrix['below_80'])}",
        f"- Dossiers sous 70 : {len(matrix['below_70'])}",
        f"- Incidents de confidentialité : {matrix['privacy_incidents']}",
        f"- Calculs interdits : {matrix['forbidden_calculations']}",
        f"- Erreurs de routage : {matrix['routing_errors']}",
        f"- Contradictions non résolues : {matrix['unresolved_contradictions']}",
        f"- Fallbacks contrôlés : {matrix['fallbacks']}",
        f"- Verdict : **{matrix['recommendation']}**",
        "",
        "## Résultats par dossier",
        "",
        "| Dossier | Score | Domaine | Fallback | Acceptable |",
        "|---|---:|---|---|---|",
    ]
    for row in matrix["results"]:
        lines.append(
            f"| {row['case_id']} | {row['score']} | {row['primary_domain']} | "
            f"{'oui' if row['fallback'] else 'non'} | {'oui' if row['acceptable'] else 'non'} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument(
        "--final-assistant-enabled",
        choices=("true", "false"),
        default="true",
    )
    parser.add_argument(
        "--expert-paie-v2-enabled",
        choices=("true", "false"),
        default="true",
    )
    args = parser.parse_args()
    campaign = run_campaign(
        load_cases(args.cases),
        final_enabled=args.final_assistant_enabled == "true",
        payroll_enabled=args.expert_paie_v2_enabled == "true",
    )
    if campaign.get("recommendation") == "HISTORICAL_RUNTIME_ONLY":
        print(json.dumps(campaign, ensure_ascii=False, indent=2))
        return 0
    matrix = public_matrix(campaign)
    args.json_output.write_text(
        json.dumps(matrix, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.write_text(render_markdown(matrix), encoding="utf-8")
    print(json.dumps({key: matrix[key] for key in (
        "case_count",
        "score_average",
        "score_minimum",
        "below_80",
        "below_70",
        "privacy_incidents",
        "forbidden_calculations",
        "routing_errors",
        "fallbacks",
        "recommendation",
    )}, ensure_ascii=False, indent=2))
    return 0 if matrix["recommendation"] == "PRÊT POUR ACTIVATION CONTRÔLÉE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
