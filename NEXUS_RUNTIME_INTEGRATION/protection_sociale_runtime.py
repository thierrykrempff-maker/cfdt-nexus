"""Fail-safe Runtime bridge for existing Protection Sociale metadata artefacts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import time
from typing import Callable

from automation.contracts import ExpertReport, ReportStatus
from automation.expert_facades import ExpertFacade, ExpertFacadeRegistry
from automation.orchestrator_common import CommonExpertOrchestrator, OrchestrationRequest
from NEXUS_ADAPTERS.connectors import (
    CONNECTOR_ADAPTATION,
    ConnectorAdapterInput,
    ConnectorCapability,
    ConnectorDescriptor,
    ConnectorDocumentSnapshot,
    ConnectorQuerySnapshot,
    ConnectorResponseSnapshot,
    ConnectorResponseStatus,
    ConnectorSourceCategory,
    ConnectorSourceSnapshot,
    GenericConnectorAdapter,
)
from NEXUS_CORE import EntityId
from NEXUS_CORE.orchestration import (
    EngineDescriptor,
    EngineRegistry,
    ExecutionContext,
    ExecutionPlanner,
    PipelineExecutor,
    ExecutionResult,
    ExecutionStatus,
)

from .config import RuntimeProtectionSocialeConfig
from .mappers import RuntimeExpertPayloadMapper
from .protection_sociale_search import (
    ProtectionSocialeSearchResult,
    RuntimeProtectionSocialeGateway,
    normalize,
)


_STRONG_MARKERS = (
    "mutuelle", "prevoyance", "frais de sante", "hospitalisation", "optique",
    "dentaire", "incapacite", "invalidite", "capital deces", "maintien de salaire",
    "indemnite complementaire", "notice de garanties", "tableau de garanties",
    "regime frais de sante", "regime de prevoyance",
)
_CONTEXTUAL_MARKERS = ("remboursement", "garantie", "indemnisation", "rente", "deces")
_HEALTH_CONTEXT = ("sante", "mutuelle", "prevoyance", "incapacite", "invalidite", "deces")
_DOMAINS = frozenset({"protection_sociale", "social_protection", "mutuelle", "prevoyance"})


def _stable(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:24]
    grouped = "x".join(digest[index:index + 4] for index in range(0, len(digest), 4))
    return f"runtime-social-{prefix}-{grouped}"


def needs_protection_sociale(answer: Mapping[str, object]) -> bool:
    """Use router declarations first and a closed vocabulary as bounded fallback."""

    if not isinstance(answer, Mapping):
        return False
    route = answer.get("route") if isinstance(answer.get("route"), Mapping) else {}
    routed = [route.get("main_domain")]
    for key in ("domains", "intents"):
        values = route.get(key) or ()
        if isinstance(values, (list, tuple, set, frozenset)):
            routed.extend(values)
    if any(normalize(value).replace(" ", "_") in _DOMAINS for value in routed):
        return True
    question = normalize(answer.get("query"))
    if any(marker in question for marker in _STRONG_MARKERS):
        return True
    return (
        any(marker in question for marker in _CONTEXTUAL_MARKERS)
        and any(marker in question for marker in _HEALTH_CONTEXT)
    )


class RuntimeProtectionSocialeMode(str, Enum):
    DISABLED = "disabled"
    NOT_NEEDED = "not_needed"
    SUCCEEDED = "succeeded"
    FALLBACK = "fallback"


@dataclass(frozen=True, slots=True)
class RuntimeProtectionSocialeDiagnostics:
    protection_sociale_called: bool = False
    protection_sociale_runtime_ms: int = 0
    protection_sociale_elements_used: int = 0
    protection_sociale_fallback: str | None = None

    def __post_init__(self) -> None:
        if self.protection_sociale_runtime_ms < 0 or self.protection_sociale_elements_used < 0:
            raise ValueError("Protection Sociale diagnostic counts must be non-negative")
        code = self.protection_sociale_fallback
        if code is not None and (not code or not code.replace("_", "").isalnum()):
            raise ValueError("protection_sociale_fallback must be a stable technical code")

    def to_dict(self) -> dict[str, object]:
        return {
            "protection_sociale_called": self.protection_sociale_called,
            "protection_sociale_runtime_ms": self.protection_sociale_runtime_ms,
            "protection_sociale_elements_used": self.protection_sociale_elements_used,
            "protection_sociale_fallback": self.protection_sociale_fallback,
        }


@dataclass(frozen=True, slots=True)
class RuntimeProtectionSocialeResult:
    mode: RuntimeProtectionSocialeMode
    diagnostics: RuntimeProtectionSocialeDiagnostics
    document_count: int = 0
    chunk_count: int = 0
    report_items: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "runtime_mode": self.mode.value,
            "diagnostics": self.diagnostics.to_dict(),
            "report_items": list(self.report_items),
        }


class RuntimeProtectionSocialeMapper:
    """Map bounded LOT 1D metadata to the public generic Connector Adapter input."""

    def map(
        self,
        search: ProtectionSocialeSearchResult,
        request_id: str,
        acquired_at: datetime,
    ) -> ConnectorAdapterInput:
        documents = tuple(
            ConnectorDocumentSnapshot(
                external_id=item.document_id,
                source_id="protection_sociale_local_corpus",
                document_type=item.document_type,
                title="PROTECTION_SOCIALE_DOCUMENT",
                fingerprint=item.source_sha256,
                metadata=(("domain", item.domain), ("topic", item.topic), ("metadata_only", True)),
            )
            for item in search.documents
        )
        return ConnectorAdapterInput(
            ConnectorDescriptor(
                "protection_sociale_local", "1.0", (ConnectorCapability.DOCUMENTS,)
            ),
            ConnectorSourceSnapshot(
                "protection_sociale_local_corpus",
                "PROTECTION_SOCIALE_LOCAL_CORPUS",
                ConnectorSourceCategory.INTERNAL_DOCUMENT,
                False,
                metadata=(("read_only", True), ("metadata_only", True)),
            ),
            ConnectorQuerySnapshot(
                _stable("query", request_id), "PROTECTION_SOCIALE_METADATA_LOOKUP"
            ),
            ConnectorResponseSnapshot(
                _stable("response", request_id),
                ConnectorResponseStatus.SUCCEEDED,
                documents=documents,
                source_confidence=0.5,
                duration_ms=search.duration_ms,
            ),
            acquired_at,
        )


class _StaticProtectionSocialeFacade(ExpertFacade):
    def __init__(self, report: ExpertReport) -> None:
        super().__init__("protection_sociale", ("runtime_protection_sociale_adaptation",))
        self._report = report

    def _execute(self, _request):
        return self._report


class _RuntimeProtectionSocialeCoreEngine:
    """Expose already-adapted references through the public Core execution contract."""

    def __init__(self, adapted) -> None:
        self._adapted = adapted
        self.engine_id = EntityId(_stable("engine", "protection_sociale_local"))

    def execute(self, _context):
        outputs = tuple(
            [EntityId(item.document_id.value) for item in self._adapted.documents]
            + [EntityId(item.evidence_id.value) for item in self._adapted.evidence]
            + [EntityId(item.finding_id.value) for item in self._adapted.findings]
        )
        return ExecutionResult(
            EntityId(_stable("core-result", self._adapted.connector_id)),
            self.engine_id,
            ExecutionStatus.SUCCEEDED,
            (CONNECTOR_ADAPTATION,),
            outputs,
        )


class RuntimeProtectionSocialeIntegration:
    """Run local metadata through Generic Connector Adapter, Core and orchestration."""

    def __init__(
        self,
        config: RuntimeProtectionSocialeConfig,
        *,
        gateway: RuntimeProtectionSocialeGateway | None = None,
        mapper: RuntimeProtectionSocialeMapper | None = None,
        clock: Callable[[], datetime] | None = None,
        timer: Callable[[], float] | None = None,
    ) -> None:
        self._config = config
        self._gateway = gateway or RuntimeProtectionSocialeGateway(config)
        self._mapper = mapper or RuntimeProtectionSocialeMapper()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._timer = timer or time.perf_counter

    def integrate(self, answer: Mapping[str, object]) -> RuntimeProtectionSocialeResult:
        if not self._config.enabled:
            return RuntimeProtectionSocialeResult(
                RuntimeProtectionSocialeMode.DISABLED, RuntimeProtectionSocialeDiagnostics()
            )
        if not needs_protection_sociale(answer):
            return RuntimeProtectionSocialeResult(
                RuntimeProtectionSocialeMode.NOT_NEEDED, RuntimeProtectionSocialeDiagnostics()
            )
        started = self._timer()
        try:
            search = self._gateway.search(answer)
        except Exception:
            return self._fallback("PROTECTION_SOCIALE_UNAVAILABLE", started)
        if search.fallback_code:
            return self._fallback(search.fallback_code, started)
        try:
            request = RuntimeExpertPayloadMapper().build_request(answer)
            adapter_input = self._mapper.map(search, request.request_id, self._clock())
        except Exception:
            return self._fallback("PROTECTION_SOCIALE_MAPPING_FAILED", started)
        adapter = GenericConnectorAdapter(adapter_input)
        try:
            adapted = adapter.adapt()
        except Exception:
            return self._fallback("PROTECTION_SOCIALE_ADAPTER_FAILED", started)
        elements = len(adapted.documents) + len(adapted.evidence) + len(adapted.findings)
        if not elements:
            return self._fallback("PROTECTION_SOCIALE_NO_RESULT", started)
        try:
            core = self._run_core(request.request_id, adapter_input.acquired_at, adapted)
        except Exception:
            return self._fallback("PROTECTION_SOCIALE_CORE_FAILED", started)
        if core.summary.failed_count:
            return self._fallback("PROTECTION_SOCIALE_CORE_FAILED", started)
        try:
            common = self._run_common(request, adapted)
        except Exception:
            return self._fallback("PROTECTION_SOCIALE_ORCHESTRATOR_FAILED", started)
        if not common.reports:
            return self._fallback("PROTECTION_SOCIALE_ORCHESTRATOR_FAILED", started)
        return RuntimeProtectionSocialeResult(
            RuntimeProtectionSocialeMode.SUCCEEDED,
            RuntimeProtectionSocialeDiagnostics(
                True, self._duration(started), elements, None
            ),
            search.document_count,
            search.chunk_count,
            (
                f"Protection sociale : {search.document_count} référence(s) documentaire(s) rapprochée(s).",
                "Les éléments disponibles sont présentés sans calcul de garantie ou de prestation.",
                "Une vérification auprès de l'organisme, de la mutuelle, de la prévoyance ou de l'employeur reste nécessaire.",
            ),
        )

    def _run_core(self, request_id: str, timestamp: datetime, adapted):
        registry = EngineRegistry()
        engine = _RuntimeProtectionSocialeCoreEngine(adapted)
        registry.register(
            EngineDescriptor(
                engine.engine_id, "RUNTIME_PROTECTION_SOCIALE_ADAPTER", (CONNECTOR_ADAPTATION,)
            ),
            engine,
        )
        plan_id = EntityId(_stable("plan", request_id))
        plan = ExecutionPlanner().plan(plan_id, registry, (CONNECTOR_ADAPTATION,), timestamp)
        context = ExecutionContext(
            EntityId(_stable("execution", request_id)), plan_id, (CONNECTOR_ADAPTATION,),
            (EntityId(_stable("input", request_id)),), timestamp,
        )
        return PipelineExecutor().execute(plan, registry, context, self._clock())

    @staticmethod
    def _run_common(request, adapted):
        report = ExpertReport(
            report_id=_stable("report", request.request_id),
            request_id=request.request_id,
            producer="protection_sociale",
            findings=(f"PROTECTION_SOCIALE_EVIDENCE_COUNT_{len(adapted.evidence)}",),
            conclusions=("PROTECTION_SOCIALE_METADATA_ADAPTED",),
            recommendations=("PROTECTION_SOCIALE_OFFICIAL_VERIFICATION_REQUIRED",),
            warnings=("PROTECTION_SOCIALE_NO_AUTOMATIC_CALCULATION",),
            status=ReportStatus.PARTIAL,
            metadata={
                "document_count": len(adapted.documents),
                "evidence_count": len(adapted.evidence),
            },
        )
        registry = ExpertFacadeRegistry()
        registry.register(_StaticProtectionSocialeFacade(report))
        return CommonExpertOrchestrator(registry).execute(
            OrchestrationRequest(request, requested_experts=("protection_sociale",))
        )

    def _fallback(self, code: str, started: float) -> RuntimeProtectionSocialeResult:
        return RuntimeProtectionSocialeResult(
            RuntimeProtectionSocialeMode.FALLBACK,
            RuntimeProtectionSocialeDiagnostics(
                True, self._duration(started), 0, code
            ),
        )

    def _duration(self, started: float) -> int:
        return max(0, round((self._timer() - started) * 1000))
