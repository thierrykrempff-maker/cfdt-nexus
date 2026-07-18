"""Explicit facade registry. It performs no expert selection or business routing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from automation.contracts import ExpertReport, ExpertRequest, ReportStatus

from .base import ExpertFacade, FacadeErrorCode, structured_error_report
from .payroll import PayrollFacade


class FacadeStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    NOT_READY = "NOT_READY"
    DISABLED = "DISABLED"


class DuplicateExpertError(ValueError):
    pass


class UnknownExpertError(LookupError):
    pass


class FacadeUnavailableError(LookupError):
    pass


@dataclass(frozen=True)
class ExpertRegistration:
    expert_id: str
    status: FacadeStatus
    capabilities: tuple[str, ...]
    facade: ExpertFacade | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.expert_id, str) or not self.expert_id.strip():
            raise ValueError("expert_id must be a non-empty string")
        if not isinstance(self.status, FacadeStatus):
            raise TypeError("status must be a FacadeStatus")
        if self.facade is not None and self.facade.expert_id != self.expert_id:
            raise ValueError("registration expert_id must match facade expert_id")
        if self.status is FacadeStatus.AVAILABLE and self.facade is None:
            raise ValueError("AVAILABLE registration requires a facade")


class ExpertFacadeRegistry:
    def __init__(self) -> None:
        self._registrations: dict[str, ExpertRegistration] = {}

    def register(self, facade: ExpertFacade, status: FacadeStatus = FacadeStatus.AVAILABLE, reason: str = "") -> None:
        if not isinstance(facade, ExpertFacade):
            raise TypeError("facade must be an ExpertFacade")
        self._add(ExpertRegistration(facade.expert_id, status, facade.capabilities, facade, reason))

    def declare(
        self,
        expert_id: str,
        status: FacadeStatus,
        capabilities: tuple[str, ...] = (),
        reason: str = "",
    ) -> None:
        if status is FacadeStatus.AVAILABLE:
            raise ValueError("AVAILABLE experts must be registered with a facade")
        self._add(ExpertRegistration(expert_id, status, tuple(capabilities), None, reason))

    def _add(self, registration: ExpertRegistration) -> None:
        if registration.expert_id in self._registrations:
            raise DuplicateExpertError(f"expert_id already registered: {registration.expert_id}")
        self._registrations[registration.expert_id] = registration

    def get(self, expert_id: str) -> ExpertRegistration:
        try:
            return self._registrations[expert_id]
        except KeyError as exc:
            raise UnknownExpertError(f"unknown expert_id: {expert_id}") from exc

    def resolve(self, expert_id: str) -> ExpertFacade:
        registration = self.get(expert_id)
        if registration.facade is None or registration.status not in {FacadeStatus.AVAILABLE, FacadeStatus.PARTIAL}:
            raise FacadeUnavailableError(f"expert {expert_id} is {registration.status.value}")
        return registration.facade

    def registrations(self) -> tuple[ExpertRegistration, ...]:
        return tuple(self._registrations[key] for key in sorted(self._registrations))

    def list_capabilities(self) -> dict[str, tuple[str, ...]]:
        return {item.expert_id: tuple(item.capabilities) for item in self.registrations()}

    def execute(self, expert_id: str, request: ExpertRequest) -> ExpertReport:
        """Execute the exact caller-provided id; no selection or inference occurs."""
        try:
            registration = self.get(expert_id)
        except UnknownExpertError as exc:
            return structured_error_report(
                request_id=getattr(request, "request_id", "invalid-request"),
                producer="expert_facade_registry",
                code=FacadeErrorCode.UNKNOWN_EXPERT,
                message=str(exc),
            )
        if registration.facade is None or registration.status not in {FacadeStatus.AVAILABLE, FacadeStatus.PARTIAL}:
            disabled = registration.status is FacadeStatus.DISABLED
            return structured_error_report(
                request_id=getattr(request, "request_id", "invalid-request"),
                producer=expert_id,
                code=FacadeErrorCode.EXPERT_DISABLED if disabled else FacadeErrorCode.EXPERT_NOT_READY,
                message=f"expert {expert_id} is {registration.status.value}",
                status=ReportStatus.REFUSED if disabled else ReportStatus.FAILED,
                metadata={"registry_status": registration.status.value, "reason": registration.reason},
            )
        return registration.facade.execute(request)


def build_default_registry() -> ExpertFacadeRegistry:
    registry = ExpertFacadeRegistry()
    registry.register(PayrollFacade())
    registry.declare(
        "juriste_travail",
        FacadeStatus.PARTIAL,
        ("labor_law", "employee_defense", "collective_bargaining", "cse_cssct"),
        "Historical expert exists, but no validated ARCH-01 report adapter is available yet.",
    )
    registry.declare(
        "cse_memory",
        FacadeStatus.NOT_READY,
        ("document_memory", "cse_corpus"),
        "Document memory pipeline; it is not an autonomous expert entry point.",
    )
    registry.declare(
        "protection_sociale",
        FacadeStatus.NOT_READY,
        ("document_import", "protection_sociale_corpus"),
        "Document pipeline only; no executable expert is exposed.",
    )
    registry.declare(
        "local_law",
        FacadeStatus.NOT_READY,
        ("local_law_guard", "alsace_moselle"),
        "Applicability and reasoning guards exist, not an autonomous expert.",
    )
    registry.declare(
        "sante_securite",
        FacadeStatus.NOT_READY,
        ("cse_cssct",),
        "No standalone executable safety expert exists; the topic is handled by Juriste Travail.",
    )
    return registry
