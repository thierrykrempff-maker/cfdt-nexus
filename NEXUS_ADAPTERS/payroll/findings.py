"""Explicit mapping of payroll observations to neutral Core findings."""

from __future__ import annotations

from automation.contracts import ExpertReport
from NEXUS_CORE import (
    Finding,
    FindingId,
    FindingSeverity,
    FindingStatus,
    FindingType,
    Period,
)

from ._identity import stable_payroll_id
from .evidence import PayrollEvidenceMapper
from .metadata import PayrollMetadataMapper


class PayrollFindingMapper:
    def __init__(
        self,
        evidence: PayrollEvidenceMapper | None = None,
        metadata: PayrollMetadataMapper | None = None,
    ) -> None:
        self._metadata = metadata or PayrollMetadataMapper()
        self._evidence = evidence or PayrollEvidenceMapper(self._metadata)

    def map(
        self, report: ExpertReport, period: Period | None = None
    ) -> tuple[Finding, ...]:
        findings = []
        for index, _ in enumerate(report.findings):
            findings.append(
                self._finding(
                    report,
                    "finding",
                    index,
                    FindingType.OBSERVATION,
                    FindingSeverity.INFO,
                    "PAYROLL_OBSERVATION",
                    period,
                )
            )
        for index, _ in enumerate(report.contradictions):
            findings.append(
                self._finding(
                    report,
                    "contradiction",
                    index,
                    FindingType.CONFLICT,
                    FindingSeverity.HIGH,
                    "PAYROLL_CONTRADICTION",
                    period,
                )
            )
        for index, item in enumerate(report.missing_information):
            findings.append(
                self._finding(
                    report,
                    "missing",
                    index,
                    FindingType.MISSING_INFORMATION,
                    self._metadata.severity(item.criticality),
                    "PAYROLL_INFORMATION_MISSING",
                    period,
                )
            )
        for index, item in enumerate(report.risks):
            findings.append(
                self._finding(
                    report,
                    "risk",
                    index,
                    FindingType.RISK,
                    self._metadata.severity(item.level),
                    "PAYROLL_RISK_REPORTED",
                    period,
                )
            )
        return tuple(findings)

    def _finding(self, report, category, index, finding_type, severity, code, period):
        return Finding(
            FindingId(stable_payroll_id("finding", report.report_id, category, str(index))),
            finding_type,
            severity,
            FindingStatus.OPEN,
            code,
            (self._evidence.evidence_id(report, category, index),),
            period,
        )
