"""Fail-safe Runtime bridge for the existing CSE Memory artefacts and adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
from typing import Callable

from automation.contracts import ExpertReport, ReportStatus
from automation.expert_facades import ExpertFacade, ExpertFacadeRegistry
from automation.orchestrator_common import CommonExpertOrchestrator, OrchestrationRequest
from NEXUS_ADAPTERS.cse import CSE_ADAPTATION, CSEAdapter, CSEAdapterInput
from NEXUS_CORE import EntityId, EntityReference
from NEXUS_CORE.orchestration import (
    EngineDescriptor, EngineRegistry, ExecutionContext, ExecutionPlanner, PipelineExecutor,
)

from .config import RuntimeCSEMemoryConfig
from .cse_memory_search import RuntimeCSEMemoryGateway, needs_cse_memory
from .mappers import RuntimeExpertPayloadMapper


def _stable(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:24]
    return f"runtime-cse-{prefix}-{digest}"


class RuntimeCSEMemoryMode(str, Enum):
    DISABLED = "disabled"
    NOT_NEEDED = "not_needed"
    SUCCEEDED = "succeeded"
    FALLBACK = "fallback"


@dataclass(frozen=True, slots=True)
class RuntimeCSEMemoryDiagnostics:
    enabled: bool
    called: bool = False
    document_count: int = 0
    chunk_count: int = 0
    duration_ms: int = 0
    adapter_called: bool = False
    core_pipeline_called: bool = False
    common_orchestrator_called: bool = False
    fallback_triggered: bool = False
    fallback_code: str | None = None

    def to_dict(self):
        return {
            "enabled": self.enabled,
            "called": self.called,
            "document_count": self.document_count,
            "chunk_count": self.chunk_count,
            "duration_ms": self.duration_ms,
            "adapter_called": self.adapter_called,
            "core_pipeline_called": self.core_pipeline_called,
            "common_orchestrator_called": self.common_orchestrator_called,
            "fallback_triggered": self.fallback_triggered,
            "fallback_code": self.fallback_code,
        }


@dataclass(frozen=True, slots=True)
class RuntimeCSEMemoryResult:
    mode: RuntimeCSEMemoryMode
    diagnostics: RuntimeCSEMemoryDiagnostics
    report_items: tuple[str, ...] = ()

    def to_dict(self):
        return {
            "runtime_mode": self.mode.value,
            "diagnostics": self.diagnostics.to_dict(),
            "report_items": list(self.report_items),
        }


class _StaticCSEFacade(ExpertFacade):
    def __init__(self, report: ExpertReport) -> None:
        super().__init__("cse_memory", ("runtime_cse_memory_adaptation",))
        self._report = report

    def _execute(self, _request):
        return self._report


class RuntimeCSEMemoryIntegration:
    def __init__(
        self,
        config: RuntimeCSEMemoryConfig,
        *,
        gateway: RuntimeCSEMemoryGateway | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._config = config
        self._gateway = gateway or RuntimeCSEMemoryGateway(config)
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def integrate(self, answer) -> RuntimeCSEMemoryResult:
        if not self._config.enabled:
            return RuntimeCSEMemoryResult(
                RuntimeCSEMemoryMode.DISABLED, RuntimeCSEMemoryDiagnostics(False)
            )
        if not needs_cse_memory(answer):
            return RuntimeCSEMemoryResult(
                RuntimeCSEMemoryMode.NOT_NEEDED, RuntimeCSEMemoryDiagnostics(True)
            )
        try:
            search = self._gateway.search(answer)
        except Exception:
            return self._fallback("CSE_MEMORY_SEARCH_FAILED", called=True)
        if search.fallback_code:
            return self._fallback(
                search.fallback_code,
                called=True,
                duration_ms=search.duration_ms,
            )
        request = RuntimeExpertPayloadMapper().build_request(answer)
        timestamp = self._clock()
        subject = EntityReference(EntityId(_stable("subject", request.request_id)), "runtime_request")
        adapter = CSEAdapter(CSEAdapterInput(subject, timestamp, search.documents))
        try:
            adapted = adapter.adapt()
        except Exception:
            return self._fallback(
                "CSE_MEMORY_ADAPTER_FAILED",
                called=True,
                document_count=search.document_count,
                chunk_count=search.chunk_count,
                duration_ms=search.duration_ms,
                adapter_called=True,
            )
        try:
            core_report = self._run_core(request.request_id, timestamp, adapter)
        except Exception:
            return self._fallback(
                "CSE_MEMORY_CORE_FAILED", called=True,
                document_count=search.document_count, chunk_count=search.chunk_count,
                duration_ms=search.duration_ms, adapter_called=True, core_pipeline_called=True,
            )
        if core_report.summary.failed_count:
            return self._fallback(
                "CSE_MEMORY_CORE_FAILED", called=True,
                document_count=search.document_count, chunk_count=search.chunk_count,
                duration_ms=search.duration_ms, adapter_called=True, core_pipeline_called=True,
            )
        try:
            common = self._run_common(request, adapted, search.document_count, search.chunk_count)
        except Exception:
            return self._fallback(
                "CSE_MEMORY_ORCHESTRATION_FAILED", called=True,
                document_count=search.document_count, chunk_count=search.chunk_count,
                duration_ms=search.duration_ms, adapter_called=True, core_pipeline_called=True,
                common_orchestrator_called=True,
            )
        if not common.reports:
            return self._fallback(
                "CSE_MEMORY_ORCHESTRATION_FAILED", called=True,
                document_count=search.document_count, chunk_count=search.chunk_count,
                duration_ms=search.duration_ms, adapter_called=True, core_pipeline_called=True,
                common_orchestrator_called=True,
            )
        diagnostics = RuntimeCSEMemoryDiagnostics(
            True, True, search.document_count, search.chunk_count, search.duration_ms,
            True, True, True,
        )
        return RuntimeCSEMemoryResult(
            RuntimeCSEMemoryMode.SUCCEEDED,
            diagnostics,
            (
                f"CSE Memory : {search.document_count} document(s) rapproché(s).",
                f"CSE Memory : {search.chunk_count} chunk(s) documentaire(s) utilisé(s).",
                f"CSE Memory : {len(adapted.evidence)} preuve(s) transmise(s) au Core.",
            ),
        )

    def _run_core(self, request_id, timestamp, adapter):
        registry = EngineRegistry()
        registry.register(
            EngineDescriptor(EntityId("adapter-cse"), "RUNTIME_CSE_MEMORY_ADAPTER", (CSE_ADAPTATION,)),
            adapter,
        )
        plan_id = EntityId(_stable("plan", request_id))
        plan = ExecutionPlanner().plan(plan_id, registry, (CSE_ADAPTATION,), timestamp)
        context = ExecutionContext(
            EntityId(_stable("execution", request_id)), plan_id, (CSE_ADAPTATION,),
            (EntityId(_stable("input", request_id)),), timestamp,
        )
        return PipelineExecutor().execute(plan, registry, context, self._clock())

    @staticmethod
    def _run_common(request, adapted, document_count, chunk_count):
        report = ExpertReport(
            report_id=_stable("report", request.request_id),
            request_id=request.request_id,
            producer="cse_memory",
            findings=(
                f"CSE_DOCUMENT_COUNT_{document_count}",
                f"CSE_CHUNK_COUNT_{chunk_count}",
                f"CSE_EVIDENCE_COUNT_{len(adapted.evidence)}",
            ),
            conclusions=("CSE_MEMORY_RESULTS_ADAPTED",),
            status=ReportStatus.COMPLETED,
            metadata={
                "document_count": document_count,
                "chunk_count": chunk_count,
                "evidence_count": len(adapted.evidence),
            },
        )
        registry = ExpertFacadeRegistry()
        registry.register(_StaticCSEFacade(report))
        return CommonExpertOrchestrator(registry).execute(
            OrchestrationRequest(request, requested_experts=("cse_memory",))
        )

    @staticmethod
    def _fallback(code, **values):
        return RuntimeCSEMemoryResult(
            RuntimeCSEMemoryMode.FALLBACK,
            RuntimeCSEMemoryDiagnostics(
                True,
                fallback_triggered=True,
                fallback_code=code,
                **values,
            ),
        )
