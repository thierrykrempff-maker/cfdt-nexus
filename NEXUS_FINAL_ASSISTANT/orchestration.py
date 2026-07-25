"""Fail-safe execution of selected engines."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .adapters import adapt_engine_payload
from .models import (
    AnalysisPlan,
    AssistantRequest,
    Confidence,
    Domain,
    NormalizedEngineResult,
    TechnicalTrace,
)

EngineRunner = Callable[[AssistantRequest], Mapping[str, Any]]


class EngineOrchestrator:
    def __init__(self, runners: Mapping[str, EngineRunner], max_engines: int = 4) -> None:
        self._runners = dict(runners)
        self._max_engines = max_engines

    def execute(
        self, request: AssistantRequest, plan: AnalysisPlan
    ) -> tuple[tuple[NormalizedEngineResult, ...], TechnicalTrace]:
        called: list[str] = []
        failed: list[str] = []
        results: list[NormalizedEngineResult] = []
        for engine in plan.execution_order[: self._max_engines]:
            runner = self._runners.get(engine)
            if runner is None:
                failed.append(engine)
                continue
            called.append(engine)
            try:
                payload = runner(request)
                domain = _domain_for_engine(engine, plan)
                results.append(adapt_engine_payload(engine, domain, payload))
            except Exception:
                failed.append(engine)
                results.append(
                    NormalizedEngineResult(
                        engine,
                        _domain_for_engine(engine, plan),
                        available=False,
                        confidence=Confidence.LOW,
                        technical_errors=("ENGINE_FAILED",),
                        limits=("Résultat moteur indisponible.",),
                    )
                )
        trace = TechnicalTrace(
            plan.execution_order,
            tuple(called),
            tuple(failed),
            bool(failed) or not results,
            self._max_engines,
        )
        return tuple(results), trace


def _domain_for_engine(engine: str, plan: AnalysisPlan) -> Domain:
    if engine == "expert_paie_v2":
        return Domain.PAYROLL
    if engine == "cse_memory":
        return Domain.CSE_OPERATION
    if engine == "documentary":
        return Domain.DOCUMENTARY
    return plan.primary_domain
