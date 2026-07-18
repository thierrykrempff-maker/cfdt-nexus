"""Operational facade for the historical payroll expert."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from typing import Any

from automation.adapters import (
    ADAPTER_VERSION,
    expert_request_to_legacy_payroll,
    legacy_payroll_report_to_expert_report,
)
from automation.contracts import ExpertReport, ExpertRequest
from automation.experts import paie

from .base import ExpertFacade, MalformedLegacyOutput


PAYROLL_FACADE_VERSION = "1.0"
PAYROLL_EXPERT_ID = "paie"
PAYROLL_CAPABILITIES = (
    "payroll_control",
    "overtime",
    "on_call",
    "paid_leave",
    "salary_maintenance",
    "public_holiday",
    "compensatory_rest",
)


class PayrollFacade(ExpertFacade):
    """Parallel ARCH-03 entry point; historical consumers remain untouched."""

    def __init__(self, executor: Callable[[dict[str, Any]], Mapping[str, Any]] | None = None) -> None:
        super().__init__(PAYROLL_EXPERT_ID, PAYROLL_CAPABILITIES, PAYROLL_FACADE_VERSION)
        self._executor = executor or paie.enrich

    def _execute(self, request: ExpertRequest) -> ExpertReport:
        legacy_request = expert_request_to_legacy_payroll(request)
        if "route" not in legacy_request:
            legacy_request["route"] = {"domains": ["paie_remuneration"]}
        legacy_result = self._executor(legacy_request)
        if not isinstance(legacy_result, Mapping):
            raise MalformedLegacyOutput("The payroll expert result must be a mapping.")
        try:
            report = legacy_payroll_report_to_expert_report(dict(legacy_result), request.request_id)
        except (TypeError, ValueError) as exc:
            raise MalformedLegacyOutput(f"The payroll expert result cannot be adapted: {exc}") from exc

        existing_missing_ids = {item.missing_id for item in report.missing_information}
        missing_information = report.missing_information + tuple(
            item for item in request.missing_information if item.missing_id not in existing_missing_ids
        )
        request_dict = request.to_dict()
        legacy_categories = request_dict.get("metadata", {}).get("legacy_categories", {})
        metadata = report.to_dict().get("metadata", {})
        metadata["payroll_facade"] = {
            "adapter_version": ADAPTER_VERSION,
            "historical_entrypoint": "automation.experts.paie.enrich",
            "historical_input_format": "answer: dict[str, Any]",
            "historical_output_format": "dict[str, Any]",
            "request_categories": {
                "facts": request_dict["facts"],
                "declared_information": request_dict["declared_information"],
                "assumptions": legacy_categories.get("assumptions", []),
                "assumed_intentions": legacy_categories.get("assumed_intentions", []),
                "scenarios": legacy_categories.get("scenarios", []),
                "missing_information": request_dict["missing_information"],
            },
        }
        return replace(report, missing_information=missing_information, metadata=metadata)
