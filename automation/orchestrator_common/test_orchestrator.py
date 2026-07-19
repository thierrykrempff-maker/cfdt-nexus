"""ARCH-04 acceptance tests using deterministic in-memory facades."""

from __future__ import annotations

import inspect

import pytest

from automation.contracts import ExpertReport, ExpertRequest, ReportStatus
from automation.expert_facades import ExpertFacade, ExpertFacadeRegistry, FacadeStatus
from automation.orchestrator_common import (
    CommonExpertOrchestrator, ErrorPolicy, OrchestrationRequest, OrchestrationStatus,
)


def make_request() -> ExpertRequest:
    return ExpertRequest("req-04", "Question neutre", "generic", metadata={"case": "stable"})


class FakeFacade(ExpertFacade):
    def __init__(self, expert_id: str, *, conclusion: str | None = None, failure: bool = False) -> None:
        super().__init__(expert_id, ("test",))
        self.conclusion = conclusion or expert_id
        self.failure = failure
        self.seen: list[ExpertRequest] = []

    def _execute(self, request: ExpertRequest) -> ExpertReport:
        self.seen.append(request)
        if self.failure:
            raise RuntimeError("private failure details")
        return ExpertReport(
            report_id=f"report:{self.expert_id}", request_id=request.request_id,
            producer=self.expert_id, conclusions=(self.conclusion,), status=ReportStatus.COMPLETED,
            metadata={"preserved": self.expert_id},
        )


class InvalidFacade(FakeFacade):
    def execute(self, request: ExpertRequest):  # type: ignore[override]
        return {"invalid": True}


def registry_with(*facades: FakeFacade) -> ExpertFacadeRegistry:
    registry = ExpertFacadeRegistry()
    for facade in facades:
        registry.register(facade)
    return registry


def run(registry: ExpertFacadeRegistry, experts=None, **kwargs):
    request = OrchestrationRequest(make_request(), requested_experts=experts, **kwargs)
    return CommonExpertOrchestrator(registry).execute(request)


def test_import_and_initialization_with_empty_registry():
    orchestrator = CommonExpertOrchestrator(ExpertFacadeRegistry())
    result = orchestrator.execute(OrchestrationRequest(make_request()))
    assert result.status is OrchestrationStatus.NO_EXPERT_AVAILABLE
    assert result.errors[0].code == "NO_EXPERT_SELECTED"


def test_registry_statuses_and_selection_rules():
    registry = ExpertFacadeRegistry()
    registry.register(FakeFacade("available"))
    registry.register(FakeFacade("partial"), FacadeStatus.PARTIAL)
    registry.declare("waiting", FacadeStatus.NOT_READY)
    registry.declare("off", FacadeStatus.DISABLED)
    result = run(registry, ("available", "partial", "waiting", "off", "missing"))
    assert result.selected_experts == ("available",)
    assert [error.code for error in result.errors] == [
        "PARTIAL_EXPERT_NOT_ALLOWED", "EXPERT_NOT_READY", "EXPERT_DISABLED", "UNKNOWN_EXPERT",
    ]


def test_partial_can_be_allowed_when_facade_exists():
    registry = ExpertFacadeRegistry()
    registry.register(FakeFacade("partial"), FacadeStatus.PARTIAL)
    result = run(registry, ("partial",), allow_partial_experts=True)
    assert result.selected_experts == ("partial",)
    assert result.status is OrchestrationStatus.SUCCESS


def test_explicit_order_and_duplicates_are_stable():
    registry = registry_with(FakeFacade("alpha"), FakeFacade("beta"))
    result = run(registry, ("beta", "alpha", "beta"))
    assert result.selected_experts == ("beta", "alpha")
    assert tuple(report.producer for report in result.reports) == ("beta", "alpha")


def test_implicit_order_uses_registry_canonical_order():
    result = run(registry_with(FakeFacade("zeta"), FakeFacade("alpha")))
    assert result.selected_experts == ("alpha", "zeta")


def test_success_preserves_report_and_metadata():
    result = run(registry_with(FakeFacade("alpha")), ("alpha",), metadata={"trace": "fixed"})
    assert result.status is OrchestrationStatus.SUCCESS
    assert result.reports[0].conclusions == ("alpha",)
    assert result.reports[0].metadata["preserved"] == "alpha"
    assert result.metadata["trace"] == "fixed"


def test_failure_is_isolated_without_traceback_or_private_message():
    result = run(registry_with(FakeFacade("bad", failure=True), FakeFacade("good")), ("bad", "good"))
    assert result.status is OrchestrationStatus.PARTIAL_SUCCESS
    assert tuple(report.producer for report in result.reports) == ("good",)
    error = result.errors[0]
    assert error.code == "EXPERT_EXECUTION_FAILED"
    assert error.message == "Expert execution failed."
    assert "private" not in repr(error)
    assert "Traceback" not in repr(error)


def test_stop_policy_stops_after_first_execution_failure():
    result = run(
        registry_with(FakeFacade("bad", failure=True), FakeFacade("good")),
        ("bad", "good"), error_policy=ErrorPolicy.STOP,
    )
    assert tuple(item.expert_id for item in result.execution_results) == ("bad",)
    assert result.status is OrchestrationStatus.FAILED


def test_invalid_facade_value_becomes_structured_failure():
    result = run(registry_with(InvalidFacade("invalid")), ("invalid",))
    assert result.errors[0].code == "EXPERT_EXECUTION_FAILED"
    assert result.errors[0].metadata["exception_type"] == "TypeError"


def test_same_request_object_is_passed_and_not_mutated():
    first, second = FakeFacade("first"), FakeFacade("second")
    expert_request = make_request()
    before = expert_request.to_dict()
    CommonExpertOrchestrator(registry_with(first, second)).execute(
        OrchestrationRequest(expert_request, ("first", "second"))
    )
    assert first.seen[0] is expert_request and second.seen[0] is expert_request
    assert expert_request.to_dict() == before


def test_disagreement_is_preserved_without_business_merging():
    result = run(
        registry_with(FakeFacade("one", conclusion="yes"), FakeFacade("two", conclusion="no")),
        ("one", "two"),
    )
    assert [report.conclusions for report in result.reports] == [("yes",), ("no",)]
    assert not hasattr(result.summary, "conclusion")


def test_identical_runs_are_equivalent_and_error_codes_stable():
    registry = registry_with(FakeFacade("stable"))
    one = run(registry, ("unknown", "stable"))
    two = run(registry, ("unknown", "stable"))
    assert one == two
    assert one.errors[0].code == two.errors[0].code == "UNKNOWN_EXPERT"


def test_only_allowed_arch_dependencies_are_imported():
    import automation.orchestrator_common.aggregation as aggregation
    import automation.orchestrator_common.models as models
    import automation.orchestrator_common.orchestrator as orchestrator
    import automation.orchestrator_common.selection as selection

    sources = "\n".join(inspect.getsource(module) for module in (aggregation, models, orchestrator, selection))
    forbidden = ("automation.experts", "automation.connectors", "legacy_orchestrator", "requests", "urllib", "socket")
    assert all(item not in sources for item in forbidden)


def test_public_models_validate_inputs():
    with pytest.raises(TypeError):
        OrchestrationRequest(object())  # type: ignore[arg-type]
