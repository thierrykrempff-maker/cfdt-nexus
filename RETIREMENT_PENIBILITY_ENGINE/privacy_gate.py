"""Fail-closed privacy facade with safe deterministic diagnostics."""

from __future__ import annotations

from .privacy_detector import PrivacyDetector
from .privacy_models import PrivacyInspection, PrivacySeverity, PrivacyStatus


class PrivacyBlockedError(ValueError):
    """Raised without retaining or echoing the inspected value."""


class PrivacyInspectionError(ValueError):
    """Raised when input cannot be inspected reliably."""


class RetirementPrivacyGate:
    """Block prohibited personal or real-document data before processing."""

    def __init__(self, detector=None) -> None:
        self._detector = detector or PrivacyDetector()

    def inspect(self, value) -> PrivacyInspection:
        try:
            findings = self._detector.inspect(value)
        except Exception:
            return PrivacyInspection(PrivacyStatus.INSPECTION_ERROR)
        if any(item.code.startswith("PRIVACY_UNSUPPORTED") or item.code == "PRIVACY_CYCLE_DETECTED" for item in findings):
            status = PrivacyStatus.INSPECTION_ERROR
        elif any(item.severity is PrivacySeverity.CRITICAL for item in findings):
            status = PrivacyStatus.BLOCKED
        elif findings:
            status = PrivacyStatus.SAFE_WITH_WARNINGS
        else:
            status = PrivacyStatus.SAFE
        return PrivacyInspection(status, findings)

    def validate(self, value) -> PrivacyInspection:
        return self.inspect(value)

    def assert_safe(self, value) -> PrivacyInspection:
        inspection = self.inspect(value)
        if inspection.status is PrivacyStatus.INSPECTION_ERROR:
            raise PrivacyInspectionError(self.sanitize_diagnostic(inspection))
        if inspection.status is PrivacyStatus.BLOCKED:
            raise PrivacyBlockedError(self.sanitize_diagnostic(inspection))
        return inspection

    @staticmethod
    def sanitize_diagnostic(inspection: PrivacyInspection) -> str:
        if not inspection.findings:
            return "PRIVACY_INSPECTION_ERROR"
        return "; ".join(
            f"{item.code} at {item.field_path}" for item in inspection.findings
        )


def require_privacy_gate(gate):
    """Fail closed when a protected component has no configured gate."""

    if gate is None or not callable(getattr(gate, "assert_safe", None)):
        raise PrivacyInspectionError("PRIVACY_GATE_REQUIRED")
    return gate


__all__ = (
    "PrivacyBlockedError",
    "PrivacyInspectionError",
    "RetirementPrivacyGate",
    "require_privacy_gate",
)
