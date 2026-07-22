"""Fail-safe Runtime bridge for the existing Retirement domain and adapter."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import time
from typing import Callable
import unicodedata

from automation.contracts import ExpertReport, ReportStatus
from automation.expert_facades import ExpertFacade, ExpertFacadeRegistry
from automation.orchestrator_common import CommonExpertOrchestrator, OrchestrationRequest
from NEXUS_ADAPTERS.retirement import (
    RETIREMENT_ADAPTATION,
    RetirementAdapter,
    RetirementAdapterInput,
)
from NEXUS_CORE import EntityId, EntityReference
from NEXUS_CORE.orchestration import (
    EngineDescriptor,
    EngineRegistry,
    ExecutionContext,
    ExecutionPlanner,
    PipelineExecutor,
)
from RETIREMENT_PENIBILITY_ENGINE import (
    MissingInformation,
    RetirementConfidence,
    RetirementOutputLevel,
    RetirementPlatform,
    RetirementReport,
)

from .config import RuntimeRetirementConfig
from .mappers import RuntimeExpertPayloadMapper


_RETIREMENT_MARKERS = (
    "retraite",
    "carriere longue",
    "age legal",
    "depart anticipe",
    "penibilite",
    "c2p",
    "exposition",
    "trimestre",
    "carriere",
)
_RETIREMENT_DOMAINS = frozenset({
    "retirement",
    "retraite",
    "retirement_penibility",
    "retirement_penibility_engine",
    "penibilite",
})


def _stable(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:24]
    grouped = "x".join(digest[index:index + 4] for index in range(0, len(digest), 4))
    return f"runtime-retirement-{prefix}-{grouped}"


def _normalized(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join("".join(char for char in text if not unicodedata.combining(char)).lower().split())


def needs_retirement(answer: Mapping[str, object]) -> bool:
    """Reuse router metadata first, then a closed vocabulary of explicit markers."""

    if not isinstance(answer, Mapping):
        return False
    route = answer.get("route") if isinstance(answer.get("route"), Mapping) else {}
    routed = [route.get("main_domain")]
    for key in ("domains", "intents"):
        values = route.get(key) or ()
        if isinstance(values, (list, tuple, set, frozenset)):
            routed.extend(values)
    if any(_normalized(value).replace(" ", "_") in _RETIREMENT_DOMAINS for value in routed):
        return True
    question = _normalized(answer.get("query"))
    return any(marker in question for marker in _RETIREMENT_MARKERS)


class RuntimeRetirementMode(str, Enum):
    DISABLED = "disabled"
    NOT_NEEDED = "not_needed"
    SUCCEEDED = "succeeded"
    FALLBACK = "fallback"


@dataclass(frozen=True, slots=True)
class RuntimeRetirementDiagnostics:
    retirement_called: bool = False
    retirement_runtime_ms: int = 0
    retirement_elements_used: int = 0
    retirement_fallback: str | None = None

    def __post_init__(self) -> None:
        if self.retirement_runtime_ms < 0 or self.retirement_elements_used < 0:
            raise ValueError("Retirement diagnostic counts must be non-negative")
        code = self.retirement_fallback
        if code is not None and (not code or not code.replace("_", "").isalnum()):
            raise ValueError("retirement_fallback must be a stable technical code")

    def to_dict(self) -> dict[str, object]:
        return {
            "retirement_called": self.retirement_called,
            "retirement_runtime_ms": self.retirement_runtime_ms,
            "retirement_elements_used": self.retirement_elements_used,
            "retirement_fallback": self.retirement_fallback,
        }


@dataclass(frozen=True, slots=True)
class RuntimeRetirementResult:
    mode: RuntimeRetirementMode
    diagnostics: RuntimeRetirementDiagnostics
    report_items: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "runtime_mode": self.mode.value,
            "diagnostics": self.diagnostics.to_dict(),
            "report_items": list(self.report_items),
        }


class RuntimeRetirementGateway:
    """Create a non-decisional Retirement report from the public foundation only."""

    def build(self, request_id: str) -> RetirementReport | None:
        contract = RetirementPlatform().describe()
        if contract.domain_id != "RETIREMENT_PENIBILITY_ENGINE":
            return None
        return RetirementReport(
            report_id=_stable("report", request_id),
            request_id=request_id,
            summary="RETIREMENT_DOMAIN_REQUEST_IDENTIFIED",
            missing_information=(MissingInformation(
                missing_id=_stable("missing", request_id),
                description="CAREER_AND_OFFICIAL_EVIDENCE_REQUIRED",
                reason="NO_INDIVIDUAL_CAREER_DATA_SUPPLIED_TO_RUNTIME",
                blocking=True,
                requested_source="OFFICIAL_RETIREMENT_SOURCE",
            ),),
            confidence=RetirementConfidence.UNKNOWN,
            output_level=RetirementOutputLevel.INFORMATION_GENERALE,
            recommended_actions=("REQUEST_OFFICIAL_CAREER_REVIEW",),
            warnings=("NO_RETIREMENT_CALCULATION_PERFORMED",),
        )


class _StaticRetirementFacade(ExpertFacade):
    def __init__(self, report: ExpertReport) -> None:
        super().__init__("retirement_penibility", ("runtime_retirement_adaptation",))
        self._report = report

    def _execute(self, _request):
        return self._report


class RuntimeRetirementIntegration:
    """Route safe Retirement metadata through Adapter, Core and common orchestration."""

    def __init__(
        self,
        config: RuntimeRetirementConfig,
        *,
        gateway: RuntimeRetirementGateway | None = None,
        clock: Callable[[], datetime] | None = None,
        timer: Callable[[], float] | None = None,
    ) -> None:
        self._config = config
        self._gateway = gateway or RuntimeRetirementGateway()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._timer = timer or time.perf_counter

    def integrate(self, answer: Mapping[str, object]) -> RuntimeRetirementResult:
        if not self._config.enabled:
            return RuntimeRetirementResult(
                RuntimeRetirementMode.DISABLED, RuntimeRetirementDiagnostics()
            )
        if not needs_retirement(answer):
            return RuntimeRetirementResult(
                RuntimeRetirementMode.NOT_NEEDED, RuntimeRetirementDiagnostics()
            )
        started = self._timer()
        try:
            request = RuntimeExpertPayloadMapper().build_request(answer)
            report = self._gateway.build(request.request_id)
        except Exception:
            return self._fallback("RETIREMENT_RUNTIME_UNAVAILABLE", started)
        if report is None:
            return self._fallback("RETIREMENT_NO_RESULT", started)
        timestamp = self._clock()
        subject = EntityReference(
            EntityId(_stable("subject", request.request_id)), "runtime_request"
        )
        adapter = RetirementAdapter(RetirementAdapterInput(report, subject, timestamp))
        try:
            adapted = adapter.adapt()
        except Exception:
            return self._fallback("RETIREMENT_ADAPTER_FAILED", started)
        element_count = (
            len(adapted.evidence)
            + len(adapted.findings)
            + len(adapted.recommendations)
            + len(adapted.documents)
            + len(adapted.employment_periods)
        )
        if element_count == 0:
            return self._fallback("RETIREMENT_NO_RESULT", started)
        try:
            core_report = self._run_core(request.request_id, timestamp, adapter)
        except Exception:
            return self._fallback("RETIREMENT_CORE_FAILED", started)
        if core_report.summary.failed_count:
            return self._fallback("RETIREMENT_CORE_FAILED", started)
        try:
            common = self._run_common(request, adapted)
        except Exception:
            return self._fallback("RETIREMENT_ORCHESTRATION_FAILED", started)
        if not common.reports:
            return self._fallback("RETIREMENT_ORCHESTRATION_FAILED", started)
        duration = self._duration(started)
        return RuntimeRetirementResult(
            RuntimeRetirementMode.SUCCEEDED,
            RuntimeRetirementDiagnostics(True, duration, element_count),
            (
                "Le domaine Retraite et pénibilité a été pris en compte.",
                "Aucun calcul de retraite, de trimestre ou de point C2P n'a été effectué.",
                "Une vérification de carrière auprès d'une source officielle reste nécessaire.",
            ),
        )

    def _run_core(self, request_id: str, timestamp: datetime, adapter: RetirementAdapter):
        registry = EngineRegistry()
        registry.register(
            EngineDescriptor(
                EntityId("adapter-retirement"),
                "RUNTIME_RETIREMENT_ADAPTER",
                (RETIREMENT_ADAPTATION,),
            ),
            adapter,
        )
        plan_id = EntityId(_stable("plan", request_id))
        plan = ExecutionPlanner().plan(plan_id, registry, (RETIREMENT_ADAPTATION,), timestamp)
        context = ExecutionContext(
            EntityId(_stable("execution", request_id)),
            plan_id,
            (RETIREMENT_ADAPTATION,),
            (EntityId(_stable("input", request_id)),),
            timestamp,
        )
        return PipelineExecutor().execute(plan, registry, context, self._clock())

    @staticmethod
    def _run_common(request, adapted):
        report = ExpertReport(
            report_id=_stable("expert-report", request.request_id),
            request_id=request.request_id,
            producer="retirement_penibility",
            findings=(f"RETIREMENT_FINDING_COUNT_{len(adapted.findings)}",),
            conclusions=("RETIREMENT_RUNTIME_ADAPTED",),
            recommendations=("RETIREMENT_OFFICIAL_REVIEW_REQUIRED",),
            warnings=("RETIREMENT_NON_DECISIONAL",),
            status=ReportStatus.PARTIAL,
            metadata={"element_count": (
                len(adapted.evidence) + len(adapted.findings) + len(adapted.recommendations)
            )},
        )
        registry = ExpertFacadeRegistry()
        registry.register(_StaticRetirementFacade(report))
        return CommonExpertOrchestrator(registry).execute(
            OrchestrationRequest(request, requested_experts=("retirement_penibility",))
        )

    def _fallback(self, code: str, started: float) -> RuntimeRetirementResult:
        return RuntimeRetirementResult(
            RuntimeRetirementMode.FALLBACK,
            RuntimeRetirementDiagnostics(True, self._duration(started), 0, code),
        )

    def _duration(self, started: float) -> int:
        return max(0, round((self._timer() - started) * 1000))
