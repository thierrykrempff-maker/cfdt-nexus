"""Deterministic connector adaptation reporting."""

from __future__ import annotations

import json

from .models import ConnectorAdapterInput, ConnectorAdapterReport, ConnectorAdapterResult


class ConnectorAdapterReportBuilder:
    def build(self, source: ConnectorAdapterInput,
              result: ConnectorAdapterResult) -> ConnectorAdapterReport:
        return ConnectorAdapterReport(
            source.descriptor.connector_id,
            source.descriptor.version,
            len(source.response.documents),
            len(source.response.records),
            len(result.evidence),
            len(result.documents),
            len(result.findings),
            result.diagnostics,
            result.ignored_data_codes,
            "VALID" if not any(item.severity == "high" for item in result.diagnostics)
            else "REVIEW_REQUIRED",
            source.response.duration_ms,
        )


class JsonConnectorAdapterReporter:
    def render(self, report: ConnectorAdapterReport) -> str:
        payload = {
            "connector": report.connector_id,
            "version": report.connector_version,
            "received_documents": report.received_document_count,
            "received_records": report.received_record_count,
            "evidence": report.evidence_count,
            "document_references": report.document_reference_count,
            "findings": report.finding_count,
            "diagnostics": [
                {
                    "code": item.code,
                    "category": item.category,
                    "severity": item.severity,
                    "technical_reference": (
                        item.technical_reference.value if item.technical_reference else None
                    ),
                }
                for item in report.diagnostics
            ],
            "ignored_data": list(report.ignored_data_codes),
            "status": report.status,
            "duration_ms": report.duration_ms,
            "schema_version": report.schema_version,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
