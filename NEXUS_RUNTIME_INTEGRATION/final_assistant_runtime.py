"""Feature-flagged bridge from the historical Runtime to the final assistant."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
import time
from typing import Any, Callable

from NEXUS_FINAL_ASSISTANT import (
    AssistantRequest,
    Fact,
    NexusFinalAssistant,
)

from .config import RuntimeFinalAssistantConfig


class RuntimeFinalAssistantMode(str, Enum):
    DISABLED = "DISABLED"
    SUCCEEDED = "SUCCEEDED"
    FALLBACK = "FALLBACK"


@dataclass(frozen=True, slots=True)
class RuntimeFinalAssistantDiagnostics:
    enabled: bool
    called: bool = False
    runtime_ms: int = 0
    engines_used: tuple[str, ...] = ()
    fallback_code: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "called": self.called,
            "runtime_ms": self.runtime_ms,
            "engines_used": list(self.engines_used),
            "fallback_code": self.fallback_code,
        }


@dataclass(frozen=True, slots=True)
class RuntimeFinalAssistantResult:
    mode: RuntimeFinalAssistantMode
    diagnostics: RuntimeFinalAssistantDiagnostics
    report: Mapping[str, Any]
    assistant: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "diagnostics": self.diagnostics.to_dict(),
            "assistant": dict(self.assistant) if self.assistant is not None else None,
        }


class RuntimeFinalAssistantIntegration:
    def __init__(
        self,
        config: RuntimeFinalAssistantConfig | None = None,
        *,
        timer: Callable[[], float] | None = None,
    ) -> None:
        self._config = config or RuntimeFinalAssistantConfig()
        self._timer = timer or time.perf_counter

    def integrate(
        self,
        answer: Mapping[str, Any],
        historical_report: Mapping[str, Any],
        *,
        existing_results: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> RuntimeFinalAssistantResult:
        if not self._config.enabled:
            return RuntimeFinalAssistantResult(
                RuntimeFinalAssistantMode.DISABLED,
                RuntimeFinalAssistantDiagnostics(False),
                historical_report,
            )
        started = self._timer()
        supplied = dict(existing_results or {})
        try:
            request = _request_from_answer(answer)
            runners = {
                "syndical_reasoning": lambda _: supplied.get(
                    "syndical_reasoning", {"mode": "DISABLED"}
                ),
                "cse_memory": lambda _: supplied.get(
                    "cse_memory", {"mode": "DISABLED"}
                ),
                "expert_paie_v2": lambda _: _run_expert_paie_v2(answer),
                "documentary": lambda _: _documentary_payload(answer),
            }
            response = NexusFinalAssistant(
                runners, max_engines=self._config.max_engines
            ).analyze(request)
            public = response.to_dict()
            report = _map_report(historical_report, public)
            return RuntimeFinalAssistantResult(
                RuntimeFinalAssistantMode.SUCCEEDED,
                RuntimeFinalAssistantDiagnostics(
                    True,
                    True,
                    _duration(self._timer, started),
                    response.trace.engines_called,
                ),
                report,
                public,
            )
        except Exception:
            return RuntimeFinalAssistantResult(
                RuntimeFinalAssistantMode.FALLBACK,
                RuntimeFinalAssistantDiagnostics(
                    True,
                    True,
                    _duration(self._timer, started),
                    fallback_code="FINAL_ASSISTANT_RUNTIME_FAILED",
                ),
                historical_report,
            )


def _run_expert_paie_v2(answer: Mapping[str, Any]) -> dict[str, Any]:
    """Import Expert Paie V2 only when the plan actually executes this runner."""
    from .config import RuntimeExpertPaieV2Config
    from .expert_paie_v2_runtime import RuntimeExpertPaieV2Integration

    return RuntimeExpertPaieV2Integration(
        RuntimeExpertPaieV2Config.from_env()
    ).integrate(answer).to_dict()


def _request_from_answer(answer: Mapping[str, Any]) -> AssistantRequest:
    route = answer.get("route") if isinstance(answer.get("route"), Mapping) else {}
    route_domains = tuple(
        str(item) for item in route.get("domains", ()) if isinstance(item, str)
    )
    raw_facts = answer.get("facts")
    facts = []
    if isinstance(raw_facts, (list, tuple)):
        for item in raw_facts:
            if isinstance(item, Mapping):
                text = str(item.get("statement") or item.get("text") or "").strip()
                if text:
                    facts.append(
                        Fact(
                            text,
                            bool(item.get("documented")),
                            str(item.get("source") or "user_statement"),
                        )
                    )
            elif str(item).strip():
                facts.append(Fact(str(item)))
    return AssistantRequest(
        question=str(answer.get("query") or ""),
        collective_case=any(
            marker in str(answer.get("query") or "").lower()
            for marker in ("plusieurs salariés", "collectif", "cse")
        ),
        facts=tuple(facts),
        available_documents=tuple(
            str(item)
            for item in answer.get("available_documents", ())
            if isinstance(item, str)
        ),
        period=str(answer.get("period")) if answer.get("period") else None,
        expected_output=str(answer.get("expected_output") or "analysis"),
        requested_detail=str(answer.get("detail") or "auto"),
        route_domains=route_domains,
    )


def _documentary_payload(answer: Mapping[str, Any]) -> Mapping[str, Any]:
    sources = answer.get("sources")
    return {
        "mode": "SUCCEEDED" if isinstance(sources, (list, tuple)) and sources else "NOT_APPLICABLE",
        "sources": list(sources) if isinstance(sources, (list, tuple)) else [],
    }


def _map_report(
    historical_report: Mapping[str, Any], assistant: Mapping[str, Any]
) -> dict[str, Any]:
    result = deepcopy(dict(historical_report))
    summary = assistant.get("summary") if isinstance(assistant.get("summary"), Mapping) else {}
    items = []
    labels = {
        "understanding": "Compréhension de la situation",
        "factual_answer": "Réponse factuelle",
        "primary_source": "Source principale",
        "comparative_analysis": "Analyse comparée",
        "comparable_case_law": "Jurisprudence comparable",
        "cse_elements": "Éléments issus du CSE",
        "employee_arguments": "Arguments du salarié",
        "employer_arguments": "Arguments possibles de l'employeur",
        "solutions": "Solutions concrètes",
        "expert_advice": "Conseil d'expert",
        "documents_indispensable": "Documents indispensables",
        "documents_useful": "Documents utiles",
        "documents_not_required": "Documents non nécessaires",
        "missing": "Points restant à vérifier",
        "limits": "Limites",
    }
    for key in (
        "understanding",
        "factual_answer",
        "primary_source",
        "comparative_analysis",
        "comparable_case_law",
        "cse_elements",
        "employee_arguments",
        "employer_arguments",
        "solutions",
        "expert_advice",
        "qualifications",
        "sources_to_verify",
        "risks_and_urgencies",
        "action_plan",
        "documents_indispensable",
        "documents_useful",
        "documents_not_required",
        "missing",
        "limits",
    ):
        values = summary.get(key)
        if isinstance(values, (list, tuple)):
            items.extend(
                f"{labels.get(key, key)} : {value}" for value in values[:4]
            )
    sections = list(result.get("sections") or ())
    sections.append(
        {
            "id": "nexus_final_assistant",
            "title": "Assistant final CFDT Nexus",
            "items": list(dict.fromkeys(items)),
        }
    )
    result["sections"] = sections
    generated = list(result.get("generated_from") or ())
    generated.append("Nexus Final Assistant")
    result["generated_from"] = list(dict.fromkeys(generated))
    result["final_assistant"] = dict(assistant)
    return result


def _duration(timer: Callable[[], float], started: float) -> int:
    return max(0, int((timer() - started) * 1000))
