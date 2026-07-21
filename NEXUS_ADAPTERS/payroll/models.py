"""Immutable result and diagnostic models for the payroll adapter."""

from __future__ import annotations

from dataclasses import dataclass

from NEXUS_CORE import DocumentReference, Evidence, Finding, Recommendation
from NEXUS_CORE.identifiers import EntityId


def _technical_code(value: str, label: str) -> None:
    if not value or not value.replace("_", "").isalnum():
        raise ValueError(f"{label} must be a stable technical code")


@dataclass(frozen=True, slots=True)
class PayrollAdapterDiagnostics:
    code: str
    category: str
    severity: str
    technical_reference: EntityId | None = None
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        for value in (self.code, self.category, self.severity):
            _technical_code(value, "diagnostic field")


@dataclass(frozen=True, slots=True)
class PayrollAdapterResult:
    evidence: tuple[Evidence, ...]
    findings: tuple[Finding, ...]
    recommendations: tuple[Recommendation, ...]
    documents: tuple[DocumentReference, ...]
    diagnostics: tuple[PayrollAdapterDiagnostics, ...]
    source_schema_version: str
    schema_version: str = "1.0"
