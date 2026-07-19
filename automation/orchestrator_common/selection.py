"""Deterministic registry-based selection without semantic routing."""

from __future__ import annotations

from dataclasses import dataclass

from automation.expert_facades import ExpertFacadeRegistry, ExpertRegistration, FacadeStatus, UnknownExpertError

from .models import OrchestrationError, OrchestrationRequest


@dataclass(frozen=True)
class SelectionOutcome:
    registrations: tuple[ExpertRegistration, ...]
    errors: tuple[OrchestrationError, ...]


def select_experts(request: OrchestrationRequest, registry: ExpertFacadeRegistry) -> SelectionOutcome:
    if request.requested_experts is None:
        ids = tuple(item.expert_id for item in registry.registrations())
    else:
        ids = tuple(dict.fromkeys(request.requested_experts))
    selected: list[ExpertRegistration] = []
    errors: list[OrchestrationError] = []
    for expert_id in ids:
        try:
            registration = registry.get(expert_id)
        except UnknownExpertError:
            errors.append(_selection_error("UNKNOWN_EXPERT", "Unknown expert.", expert_id, None))
            continue
        status = registration.status
        if status is FacadeStatus.AVAILABLE:
            selected.append(registration)
        elif status is FacadeStatus.PARTIAL and request.allow_partial_experts and registration.facade is not None:
            selected.append(registration)
        else:
            code = {
                FacadeStatus.PARTIAL: "PARTIAL_EXPERT_NOT_ALLOWED",
                FacadeStatus.NOT_READY: "EXPERT_NOT_READY",
                FacadeStatus.DISABLED: "EXPERT_DISABLED",
            }[status]
            errors.append(_selection_error(code, f"Expert is {status.value}.", expert_id, status))
    if not selected and not errors:
        errors.append(_selection_error("NO_EXPERT_SELECTED", "No expert is available for selection.", None, None))
    return SelectionOutcome(tuple(selected), tuple(errors))


def _selection_error(code: str, message: str, expert_id: str | None, status: FacadeStatus | None) -> OrchestrationError:
    metadata = {} if status is None else {"registry_status": status.value}
    return OrchestrationError(code=code, message=message, stage="selection", expert_id=expert_id, metadata=metadata)
