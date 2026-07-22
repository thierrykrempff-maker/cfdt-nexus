"""Fail-safe orchestration bridge executed after the historical experts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Callable

from automation.contracts import ExpertReport
from automation.expert_facades import ExpertFacade, ExpertFacadeRegistry
from automation.orchestrator_common import CommonExpertOrchestrator, OrchestrationRequest
from NEXUS_ADAPTERS.payroll import PAYROLL_ADAPTATION, PayrollAdapter
from NEXUS_CORE import EntityId, EntityReference
from NEXUS_CORE.orchestration import (
    EngineCapability,
    EngineDescriptor,
    EngineRegistry,
    ExecutionContext,
    ExecutionPlanner,
    ExecutionResult,
    ExecutionStatus,
    PipelineExecutor,
)

from .config import RuntimeIntegrationConfig
from .mappers import MappedLegalPayload, RuntimeCoreArtifacts, RuntimeExpertPayloadMapper, _stable
from .models import (
    RuntimeCoreIntegrationDiagnostics,
    RuntimeCoreIntegrationInput,
    RuntimeCoreIntegrationResult,
    RuntimeMode,
)


LEGAL_ADAPTATION = EngineCapability("RUNTIME_LEGAL_ADAPTATION")


class _StaticReportFacade(ExpertFacade):
    def __init__(self, expert_id: str, report: ExpertReport) -> None:
        super().__init__(expert_id, ("runtime_payload_adaptation",))
        self._report = report

    def _execute(self, _request):
        return self._report


class _RuntimeLegalCoreEngine:
    engine_id = EntityId("adapter-runtime-legal")

    def __init__(self, artifacts: RuntimeCoreArtifacts) -> None:
        self._artifacts = artifacts

    def execute(self, _context: ExecutionContext) -> ExecutionResult:
        references = tuple(
            [EntityId(item.evidence_id.value) for item in self._artifacts.evidence]
            + [EntityId(item.finding_id.value) for item in self._artifacts.findings]
            + [EntityId(item.recommendation_id.value) for item in self._artifacts.recommendations]
            + [EntityId(item.document_id.value) for item in self._artifacts.documents]
        )
        return ExecutionResult(
            EntityId(_stable("legal-execution-result", *[item.value for item in references])),
            self.engine_id,
            ExecutionStatus.SUCCEEDED,
            (LEGAL_ADAPTATION,),
            references,
        )


class RuntimeCoreIntegration:
    """Run Core opportunistically and always preserve the historical response."""

    def __init__(
        self,
        config: RuntimeIntegrationConfig | None = None,
        *,
        mapper: RuntimeExpertPayloadMapper | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._config = config or RuntimeIntegrationConfig()
        self._mapper = mapper or RuntimeExpertPayloadMapper()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def integrate(self, source: RuntimeCoreIntegrationInput) -> RuntimeCoreIntegrationResult:
        if not self._config.enabled:
            return RuntimeCoreIntegrationResult(
                RuntimeMode.LEGACY,
                RuntimeCoreIntegrationDiagnostics(core_enabled=False),
            )
        try:
            return self._integrate_enabled(source)
        except Exception as exc:
            return self._fallback(
                self._safe_fallback_code(exc),
                legal_executed=self._payload_was_executed(source.legal_payload),
                payroll_executed=self._payload_was_executed(source.payroll_payload),
            )

    def _integrate_enabled(self, source: RuntimeCoreIntegrationInput) -> RuntimeCoreIntegrationResult:
        request = self._mapper.build_request(source.answer)
        timestamp = self._clock()
        subject = EntityReference(EntityId(_stable("subject", request.request_id)), "runtime_request")
        legal = self._mapper.map_legal(
            source.legal_payload, source.answer, request.request_id, subject, timestamp
        )
        payroll_report = self._mapper.map_payroll(source.payroll_payload, request.request_id)
        if legal is None and payroll_report is None:
            return self._fallback("NO_RUNTIME_EXPERT_PAYLOAD")
        if payroll_report is not None and payroll_report.status.value in {"FAILED", "REFUSED"}:
            return self._fallback(
                "PAYROLL_EXPERT_UNAVAILABLE",
                legal_executed=legal is not None,
                payroll_executed=True,
            )

        payroll_adapter = PayrollAdapter(payroll_report, subject, timestamp) if payroll_report else None
        try:
            payroll_result = payroll_adapter.adapt() if payroll_adapter else None
        except Exception:
            return self._fallback(
                "PAYROLL_ADAPTER_FAILED",
                legal_executed=legal is not None,
                payroll_executed=payroll_report is not None,
                payroll_adapter_called=True,
            )
        try:
            core_report = self._run_core(request.request_id, timestamp, legal, payroll_adapter)
        except Exception:
            return self._fallback(
                "CORE_RUNTIME_INTEGRATION_FAILED",
                legal_executed=legal is not None,
                payroll_executed=payroll_report is not None,
                payroll_adapter_called=payroll_adapter is not None,
                core_pipeline_called=True,
            )
        if core_report.summary.failed_count:
            return self._fallback(
                "CORE_PIPELINE_FAILED",
                legal_executed=legal is not None,
                payroll_executed=payroll_report is not None,
                payroll_adapter_called=payroll_adapter is not None,
                core_pipeline_called=True,
            )
        try:
            common = self._run_common(request, legal, payroll_report)
        except Exception:
            return self._fallback(
                "COMMON_ORCHESTRATION_FAILED",
                legal_executed=legal is not None,
                payroll_executed=payroll_report is not None,
                payroll_adapter_called=payroll_adapter is not None,
                core_pipeline_called=True,
                common_orchestrator_called=True,
            )
        if not common.reports:
            return self._fallback(
                "COMMON_ORCHESTRATION_FAILED",
                legal_executed=legal is not None,
                payroll_executed=payroll_report is not None,
                payroll_adapter_called=payroll_adapter is not None,
                core_pipeline_called=True,
                common_orchestrator_called=True,
            )

        legal_artifacts = legal.artifacts if legal else RuntimeCoreArtifacts()
        evidence_count = len(legal_artifacts.evidence) + (len(payroll_result.evidence) if payroll_result else 0)
        finding_count = len(legal_artifacts.findings) + (len(payroll_result.findings) if payroll_result else 0)
        recommendation_count = len(legal_artifacts.recommendations) + (
            len(payroll_result.recommendations) if payroll_result else 0
        )
        selected = tuple(common.selected_experts)
        diagnostics = RuntimeCoreIntegrationDiagnostics(
            core_enabled=True,
            legal_executed=legal is not None,
            payroll_executed=payroll_report is not None,
            payroll_adapter_called=payroll_adapter is not None,
            core_pipeline_called=True,
            common_orchestrator_called=True,
            evidence_count=evidence_count,
            finding_count=finding_count,
            recommendation_count=recommendation_count,
        )
        return RuntimeCoreIntegrationResult(
            RuntimeMode.CORE_V3,
            diagnostics,
            core_status="succeeded",
            common_orchestrator_status=common.status.value.lower(),
            selected_experts=selected,
            report_items=(
                "Nexus Core V3 a agrégé les sorties expertes disponibles.",
                f"Experts intégrés : {len(selected)}.",
                f"Preuves transmises : {evidence_count}.",
                f"Constats transmis : {finding_count}.",
                f"Recommandations transmises : {recommendation_count}.",
            ),
        )

    def _run_core(self, request_id, timestamp, legal: MappedLegalPayload | None, payroll_adapter):
        registry = EngineRegistry()
        requested = []
        if legal is not None:
            engine = _RuntimeLegalCoreEngine(legal.artifacts)
            registry.register(
                EngineDescriptor(engine.engine_id, "RUNTIME_LEGAL_MAPPER", (LEGAL_ADAPTATION,)),
                engine,
            )
            requested.append(LEGAL_ADAPTATION)
        if payroll_adapter is not None:
            engine_id = EntityId("adapter-payroll")
            registry.register(
                EngineDescriptor(engine_id, "RUNTIME_PAYROLL_ADAPTER", (PAYROLL_ADAPTATION,)),
                payroll_adapter,
            )
            requested.append(PAYROLL_ADAPTATION)
        plan_id = EntityId(_stable("core-plan", request_id))
        plan = ExecutionPlanner().plan(plan_id, registry, tuple(requested), timestamp)
        context = ExecutionContext(
            EntityId(_stable("core-execution", request_id)),
            plan_id,
            tuple(requested),
            (EntityId(_stable("core-input", request_id)),),
            timestamp,
        )
        return PipelineExecutor().execute(plan, registry, context, self._clock())

    @staticmethod
    def _run_common(request, legal, payroll_report):
        registry = ExpertFacadeRegistry()
        selected = []
        if legal is not None:
            registry.register(_StaticReportFacade("juriste_travail", legal.report))
            selected.append("juriste_travail")
        if payroll_report is not None:
            registry.register(_StaticReportFacade("paie", payroll_report))
            selected.append("paie")
        return CommonExpertOrchestrator(registry).execute(
            OrchestrationRequest(request, requested_experts=tuple(selected))
        )

    @staticmethod
    def _fallback(
        code: str,
        *,
        legal_executed: bool = False,
        payroll_executed: bool = False,
        payroll_adapter_called: bool = False,
        core_pipeline_called: bool = False,
        common_orchestrator_called: bool = False,
    ) -> RuntimeCoreIntegrationResult:
        return RuntimeCoreIntegrationResult(
            RuntimeMode.CORE_V3_FALLBACK,
            RuntimeCoreIntegrationDiagnostics(
                core_enabled=True,
                legal_executed=legal_executed,
                payroll_executed=payroll_executed,
                payroll_adapter_called=payroll_adapter_called,
                core_pipeline_called=core_pipeline_called,
                common_orchestrator_called=common_orchestrator_called,
                fallback_triggered=True,
                fallback_code=code,
            ),
        )

    @staticmethod
    def _payload_was_executed(payload: object) -> bool:
        if payload is None:
            return False
        if isinstance(payload, Mapping):
            return payload.get("active") is not False
        return True

    @staticmethod
    def _safe_fallback_code(exc: Exception) -> str:
        allowed = {
            "RUNTIME_QUESTION_MISSING",
            "RUNTIME_PAYROLL_PAYLOAD_MALFORMED",
            "RUNTIME_LEGAL_PAYLOAD_MALFORMED",
        }
        candidate = str(exc)
        return candidate if candidate in allowed else "CORE_RUNTIME_INTEGRATION_FAILED"
