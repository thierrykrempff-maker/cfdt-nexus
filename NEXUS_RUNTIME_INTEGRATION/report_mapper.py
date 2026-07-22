"""Optional Core section for the existing report, leaving legacy sections intact."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import RuntimeCoreIntegrationResult, RuntimeMode


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
