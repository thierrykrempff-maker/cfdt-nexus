"""Common, deterministic boundary for progressively migrated Nexus experts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import replace
from enum import Enum
from typing import Any

from automation.contracts import ExpertReport, ExpertRequest, ReportStatus


FACADE_API_VERSION = "1.0"


class FacadeErrorCode(str, Enum):
    INVALID_REQUEST = "INVALID_REQUEST"
    LEGACY_BUSINESS_REFUSAL = "LEGACY_BUSINESS_REFUSAL"
    MALFORMED_LEGACY_OUTPUT = "MALFORMED_LEGACY_OUTPUT"
    UNKNOWN_EXPERT = "UNKNOWN_EXPERT"
    EXPERT_NOT_READY = "EXPERT_NOT_READY"
    EXPERT_DISABLED = "EXPERT_DISABLED"


class LegacyBusinessRefusal(Exception):
    """Expected business refusal explicitly raised by a historical expert."""


class MalformedLegacyOutput(Exception):
    """Expected boundary error when a historical result cannot be adapted."""


def structured_error_report(
    *,
    request_id: str,
    producer: str,
    code: FacadeErrorCode,
    message: str,
    status: ReportStatus = ReportStatus.FAILED,
    metadata: dict[str, Any] | None = None,
) -> ExpertReport:
    """Build a stable report for a known boundary or business error."""
    safe_request_id = request_id.strip() if isinstance(request_id, str) and request_id.strip() else "invalid-request"
    safe_producer = producer.strip() if isinstance(producer, str) and producer.strip() else "expert_facade"
    details = dict(metadata or {})
    details["facade_error"] = {"code": code.value, "message": str(message)}
    return ExpertReport(
        report_id=f"{safe_request_id}:{safe_producer}:{code.value.lower()}",
        request_id=safe_request_id,
        producer=safe_producer,
        errors=(str(message),),
        status=status,
        metadata=details,
    )


class ExpertFacade(ABC):
    """Stable ARCH-03 API. Subclasses only implement the historical call."""

    def __init__(self, expert_id: str, capabilities: tuple[str, ...], facade_version: str = "1.0") -> None:
        if not isinstance(expert_id, str) or not expert_id.strip():
            raise ValueError("expert_id must be a non-empty string")
        if not isinstance(facade_version, str) or not facade_version.strip():
            raise ValueError("facade_version must be a non-empty string")
        normalized = tuple(str(item).strip() for item in capabilities)
        if any(not item for item in normalized):
            raise ValueError("capabilities must contain non-empty strings")
        if len(normalized) != len(set(normalized)):
            raise ValueError("capabilities must not contain duplicates")
        self.expert_id = expert_id.strip()
        self.capabilities = normalized
        self.facade_version = facade_version.strip()

    def execute(self, request: ExpertRequest) -> ExpertReport:
        """Execute one explicitly chosen expert without selecting or routing it."""
        if not isinstance(request, ExpertRequest):
            return structured_error_report(
                request_id=getattr(request, "request_id", "invalid-request"),
                producer=self.expert_id,
                code=FacadeErrorCode.INVALID_REQUEST,
                message="request must be an ExpertRequest",
            )
        before = request.to_dict()
        try:
            report = self._execute(request)
        except LegacyBusinessRefusal as exc:
            report = structured_error_report(
                request_id=request.request_id,
                producer=self.expert_id,
                code=FacadeErrorCode.LEGACY_BUSINESS_REFUSAL,
                message=str(exc) or "The historical expert refused the request.",
                status=ReportStatus.REFUSED,
            )
        except MalformedLegacyOutput as exc:
            report = structured_error_report(
                request_id=request.request_id,
                producer=self.expert_id,
                code=FacadeErrorCode.MALFORMED_LEGACY_OUTPUT,
                message=str(exc) or "The historical expert returned a malformed result.",
            )
        if not isinstance(report, ExpertReport):
            report = structured_error_report(
                request_id=request.request_id,
                producer=self.expert_id,
                code=FacadeErrorCode.MALFORMED_LEGACY_OUTPUT,
                message="The facade did not produce an ExpertReport.",
            )
        report.validate_for_request(request)
        if request.to_dict() != before:
            raise RuntimeError("an expert facade mutated its ExpertRequest")
        metadata = report.to_dict().get("metadata", {})
        metadata["facade"] = {
            "api_version": FACADE_API_VERSION,
            "facade_version": self.facade_version,
            "expert_id": self.expert_id,
            "capabilities": list(self.capabilities),
        }
        return replace(report, metadata=metadata)

    @abstractmethod
    def _execute(self, request: ExpertRequest) -> ExpertReport:
        """Call and adapt the historical expert. Unexpected programming errors propagate."""
