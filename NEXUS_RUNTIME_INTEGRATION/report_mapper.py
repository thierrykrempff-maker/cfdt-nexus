"""Optional Core section for the existing report, leaving legacy sections intact."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import RuntimeCoreIntegrationResult, RuntimeMode
from .cse_memory_runtime import RuntimeCSEMemoryMode, RuntimeCSEMemoryResult
from .retirement_runtime import RuntimeRetirementMode, RuntimeRetirementResult
from .protection_sociale_runtime import (
    RuntimeProtectionSocialeMode,
    RuntimeProtectionSocialeResult,
)
from .syndical_reasoning_runtime import (
    RuntimeSyndicalReasoningMode,
    RuntimeSyndicalReasoningResult,
)


class RuntimeCoreReportMapper:
    def map(self, report: dict[str, Any], integration: RuntimeCoreIntegrationResult) -> dict[str, Any]:
        if integration.runtime_mode is not RuntimeMode.CORE_V3:
            return report
        result = deepcopy(report)
        sections = list(result.get("sections") or ())
        sections.append({
            "id": "core_v3_runtime",
            "title": "Synthèse Nexus Core V3",
            "items": list(integration.report_items),
        })
        result["sections"] = sections
        generated = list(result.get("generated_from") or ())
        generated.extend([
            "NEXUS_ADAPTERS/payroll/adapter.py: PayrollAdapter",
            "NEXUS_CORE/orchestration: PipelineExecutor",
            "automation/orchestrator_common/orchestrator.py: CommonExpertOrchestrator",
        ])
        result["generated_from"] = list(dict.fromkeys(generated))
        markdown = str(result.get("markdown") or "")
        if markdown:
            markdown += "\n\n## Synthèse Nexus Core V3\n\n"
            markdown += "\n".join(f"- {item}" for item in integration.report_items)
            result["markdown"] = markdown
        return result


class RuntimeCSEMemoryReportMapper:
    """Add only a bounded metadata summary; fallback returns the exact prior report."""

    def map(self, report: dict[str, Any], integration: RuntimeCSEMemoryResult) -> dict[str, Any]:
        if integration.mode is not RuntimeCSEMemoryMode.SUCCEEDED:
            return report
        result = deepcopy(report)
        sections = list(result.get("sections") or ())
        sections.append({
            "id": "cse_memory_runtime",
            "title": "Mémoire documentaire CSE",
            "items": list(integration.report_items),
        })
        result["sections"] = sections
        generated = list(result.get("generated_from") or ())
        generated.extend([
            "automation/cse_memory: LOT_1D prepared chunks",
            "NEXUS_ADAPTERS/cse/adapter.py: CSEAdapter",
            "NEXUS_CORE/orchestration: PipelineExecutor",
            "automation/orchestrator_common/orchestrator.py: CommonExpertOrchestrator",
        ])
        result["generated_from"] = list(dict.fromkeys(generated))
        return result


class RuntimeRetirementReportMapper:
    """Append a bounded non-decisional summary; fallback preserves identity."""

    def map(self, report: dict[str, Any], integration: RuntimeRetirementResult) -> dict[str, Any]:
        if integration.mode is not RuntimeRetirementMode.SUCCEEDED:
            return report
        result = deepcopy(report)
        sections = list(result.get("sections") or ())
        sections.append({
            "id": "retirement_runtime",
            "title": "Retraite et pénibilité",
            "items": list(integration.report_items),
        })
        result["sections"] = sections
        generated = list(result.get("generated_from") or ())
        generated.extend((
            "Retirement Domain",
            "Retirement Adapter",
            "Nexus Core V3",
            "Common Expert Orchestrator",
        ))
        result["generated_from"] = list(dict.fromkeys(generated))
        return result


class RuntimeProtectionSocialeReportMapper:
    """Add a bounded metadata summary; fallback returns the exact prior report."""

    def map(
        self, report: dict[str, Any], integration: RuntimeProtectionSocialeResult
    ) -> dict[str, Any]:
        if integration.mode is not RuntimeProtectionSocialeMode.SUCCEEDED:
            return report
        result = deepcopy(report)
        sections = list(result.get("sections") or ())
        sections.append({
            "id": "protection_sociale_runtime",
            "title": "Protection sociale",
            "items": list(integration.report_items),
        })
        result["sections"] = sections
        generated = list(result.get("generated_from") or ())
        generated.extend((
            "Protection Sociale LOT 1D metadata",
            "Generic Connector Adapter",
            "Nexus Core V3",
            "Common Expert Orchestrator",
        ))
        result["generated_from"] = list(dict.fromkeys(generated))
        return result


class RuntimeSyndicalReasoningReportMapper:
    """Append the short union-reasoning view without altering legacy sections."""

    def map(
        self, report: dict[str, Any], integration: RuntimeSyndicalReasoningResult
    ) -> dict[str, Any]:
        if (
            integration.mode is not RuntimeSyndicalReasoningMode.SUCCEEDED
            or integration.report is None
        ):
            return report
        result = deepcopy(report)
        sections = list(result.get("sections") or ())
        short_view = integration.report.short_view()
        sections.append(
            {
                "id": "syndical_reasoning_runtime",
                "title": "Aide au raisonnement syndical",
                "items": [
                    short_view["situation"],
                    short_view["strategie"],
                    *short_view["incertitudes"],
                ],
            }
        )
        result["sections"] = sections
        generated = list(result.get("generated_from") or ())
        generated.append("Syndical Reasoning Engine R0")
        result["generated_from"] = list(dict.fromkeys(generated))
        return result
