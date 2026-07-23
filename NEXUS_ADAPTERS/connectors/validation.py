"""Non-blocking structural validation and sensitive-value detection."""

from __future__ import annotations

import json
import re

from NEXUS_CORE import to_primitive

from .identity import stable_connector_id
from .models import (
    ConnectorAdapterDiagnostics, ConnectorAdapterInput, ConnectorAdapterResult,
    ConnectorValidationReport,
)


_SECRET = re.compile(r"(?i)(bearer\s+[a-z0-9._-]+|api[_-]?key\s*[:=]|client[_-]?secret\s*[:=]|password\s*[:=])")
_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
_PHONE = re.compile(r"(?:\+33|0)[1-9](?:[ .-]?\d{2}){4}")
_NIR = re.compile(r"\b[12]\d{12,14}\b")


class ConnectorAdapterValidator:
    def validate(self, source: ConnectorAdapterInput,
                 result: ConnectorAdapterResult) -> ConnectorValidationReport:
        violations = []
        diagnostics = []
        if not source.descriptor.connector_id or not source.source.source_id:
            violations.append("CONNECTOR_IDENTITY_MISSING")
        document_ids = [item.document_id.value for item in result.documents]
        if len(document_ids) != len(set(document_ids)):
            violations.append("DOCUMENT_IDENTIFIERS_NOT_UNIQUE")
        if self._contains_sensitive(source):
            diagnostics.append(ConnectorAdapterDiagnostics(
                "CONNECTOR_SENSITIVE_VALUE_DETECTED", "confidentiality", "high"
            ))
        try:
            json.dumps(to_primitive(result), sort_keys=True, ensure_ascii=True)
            serializable = True
        except (TypeError, ValueError):
            serializable = False
            violations.append("RESULT_NOT_SERIALIZABLE")
        rendered_once = json.dumps(to_primitive(result), sort_keys=True, default=str)
        rendered_twice = json.dumps(to_primitive(result), sort_keys=True, default=str)
        deterministic = rendered_once == rendered_twice
        return ConnectorValidationReport(
            not violations,
            tuple(violations),
            tuple(diagnostics),
            deterministic,
            serializable,
        )

    @staticmethod
    def _contains_sensitive(source: ConnectorAdapterInput) -> bool:
        values = [
            source.descriptor.connector_id, source.source.source_id,
            source.source.source_url or "", source.query.query_code,
            *(str(value) for _, value in source.query.parameters),
            *(item.content or "" for item in source.response.documents),
            *(item.excerpt or "" for item in source.response.documents),
        ]
        return any(
            pattern.search(value)
            for value in values
            for pattern in (_SECRET, _EMAIL, _PHONE, _NIR)
        )
