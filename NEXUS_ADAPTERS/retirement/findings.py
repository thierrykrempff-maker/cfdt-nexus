"""Explicit mapping of Retirement observations to neutral Nexus findings."""

from __future__ import annotations

from automation.contracts import ExpertReport
from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_models import ReconstructionProposal
from RETIREMENT_PENIBILITY_ENGINE.retirement_models import RetirementReport
from RETIREMENT_PENIBILITY_ENGINE.rule_reasoning_models import ReasoningOutcome
from NEXUS_CORE import Finding, FindingId, FindingSeverity, FindingStatus, FindingType

from ._identity import stable_retirement_id


class RetirementFindingMapper:
    def map(self, report: RetirementReport, reconstruction: ReconstructionProposal | None,
            reasoning: ReasoningOutcome | None,
            expert_report: ExpertReport | None = None) -> tuple[Finding, ...]:
        findings = []
        for item in report.missing_information:
            findings.append(Finding(
                FindingId(stable_retirement_id("finding", report.report_id, "missing", item.missing_id)),
                FindingType.MISSING_INFORMATION,
                FindingSeverity.HIGH if item.blocking else FindingSeverity.MEDIUM,
                FindingStatus.OPEN,
                "RETIREMENT_INFORMATION_MISSING",
            ))
        if reconstruction is not None:
            for item in reconstruction.conflicts:
                findings.append(Finding(
                    FindingId(stable_retirement_id("finding", "reconstruction", item.conflict_id)),
                    FindingType.CONFLICT, FindingSeverity.HIGH, FindingStatus.OPEN,
                    "RETIREMENT_RECONSTRUCTION_CONFLICT",
                ))
            for item in reconstruction.gaps:
                findings.append(Finding(
                    FindingId(stable_retirement_id("finding", "reconstruction", item.gap_id)),
                    FindingType.MISSING_INFORMATION, FindingSeverity.MEDIUM, FindingStatus.OPEN,
                    "RETIREMENT_RECONSTRUCTION_GAP",
                ))
        if reasoning is not None:
            for item in reasoning.findings:
                findings.append(Finding(
                    FindingId(stable_retirement_id("finding", "reasoning", item.finding_id)),
                    FindingType.OBSERVATION, FindingSeverity.INFO, FindingStatus.OPEN,
                    "RETIREMENT_REASONING_FINDING",
                ))
            for item in reasoning.conflicts:
                findings.append(Finding(
                    FindingId(stable_retirement_id("finding", "reasoning", item.conflict_id)),
                    FindingType.CONFLICT, FindingSeverity.HIGH, FindingStatus.OPEN,
                    "RETIREMENT_REASONING_CONFLICT",
                ))
        if expert_report is not None:
            for index, _ in enumerate(expert_report.findings):
                findings.append(Finding(
                    FindingId(stable_retirement_id("finding", expert_report.report_id, "expert", str(index))),
                    FindingType.OBSERVATION, FindingSeverity.INFO, FindingStatus.OPEN,
                    "RETIREMENT_EXPERT_FINDING",
                ))
            for index, _ in enumerate(expert_report.contradictions):
                findings.append(Finding(
                    FindingId(stable_retirement_id("finding", expert_report.report_id, "contradiction", str(index))),
                    FindingType.CONFLICT, FindingSeverity.HIGH, FindingStatus.OPEN,
                    "RETIREMENT_EXPERT_CONTRADICTION",
                ))
        return tuple(findings)
