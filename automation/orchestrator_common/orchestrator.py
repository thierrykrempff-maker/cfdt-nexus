"""Sequential common orchestrator operating only through ARCH-03 facades."""

from __future__ import annotations

from automation.contracts import ExpertReport
from automation.expert_facades import ExpertFacadeRegistry

from .aggregation import aggregate_results
from .models import ErrorPolicy, ExpertExecutionResult, OrchestrationError, OrchestrationRequest, OrchestrationResult
from .selection import select_experts


class CommonExpertOrchestrator:
    def __init__(self, registry: ExpertFacadeRegistry) -> None:
        if not isinstance(registry, ExpertFacadeRegistry):
            raise TypeError("registry must be an ExpertFacadeRegistry")
        self._registry = registry

    def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        if not isinstance(request, OrchestrationRequest):
            raise TypeError("request must be an OrchestrationRequest")
        selection = select_experts(request, self._registry)
        executions: list[ExpertExecutionResult] = []
        for registration in selection.registrations:
            try:
                facade = self._registry.resolve(registration.expert_id)
                report = facade.execute(request.expert_request)
                if not isinstance(report, ExpertReport):
                    raise TypeError("facade did not return an ExpertReport")
                report.validate_for_request(request.expert_request)
                executions.append(ExpertExecutionResult(
                    registration.expert_id, registration.status, True, True, report=report,
                    metadata={"execution_index": len(executions)},
                ))
            except Exception as exc:  # isolation boundary: never expose exception internals
                error = OrchestrationError(
                    code="EXPERT_EXECUTION_FAILED", message="Expert execution failed.", stage="execution",
                    expert_id=registration.expert_id,
                    metadata={"exception_type": type(exc).__name__},
                )
                executions.append(ExpertExecutionResult(
                    registration.expert_id, registration.status, True, False, error=error,
                    metadata={"execution_index": len(executions)},
                ))
                if request.error_policy is ErrorPolicy.STOP:
                    break
        execution_tuple = tuple(executions)
        reports, errors, summary, status = aggregate_results(execution_tuple, selection.errors)
        return OrchestrationResult(
            request_id=request.expert_request.request_id,
            selected_experts=tuple(item.expert_id for item in selection.registrations),
            execution_results=execution_tuple,
            reports=reports,
            errors=errors,
            summary=summary,
            status=status,
            metadata=request.metadata,
        )
