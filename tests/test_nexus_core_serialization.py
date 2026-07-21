"""Deterministic and privacy-safe Nexus Core serialization."""

from datetime import date, datetime, timezone

from NEXUS_CORE import (
    AnalysisId,
    AnalysisReport,
    AnalysisStatus,
    DataSensitivity,
    Diagnostic,
    DocumentType,
    MetadataEntry,
    RedactionStatus,
    TextEvidenceValue,
    to_json,
    to_primitive,
)


def test_enum_and_dates_use_stable_public_values():
    payload = to_primitive(
        (
            DocumentType.EMPLOYMENT_CONTRACT,
            date(2026, 7, 21),
            datetime(2026, 7, 21, 12, 30, tzinfo=timezone.utc),
        )
    )
    assert payload == ["employment_contract", "2026-07-21", "2026-07-21T12:30:00+00:00"]


def test_json_is_deterministic_and_carries_schema_version():
    report = AnalysisReport(AnalysisId("analysis-json-1"), AnalysisStatus.COMPLETED)
    first = to_json(report)
    second = to_json(report)
    assert first == second
    assert '"schema_version":"1.0"' in first
    assert "0x" not in first


def test_sensitive_metadata_is_redacted_by_default_and_hidden_from_repr():
    secret = "synthetic-sensitive-value"
    entry = MetadataEntry("employee_reference", secret, DataSensitivity.PERSONAL)
    serialized = to_json(entry)
    assert secret not in serialized
    assert secret not in repr(entry)
    assert '"value":"<redacted>"' in serialized
    assert f'"redaction_status":"{RedactionStatus.REDACTED.value}"' in serialized


def test_evidence_value_repr_and_safe_serialization_never_expose_value():
    secret = "synthetic-evidence-secret"
    value = TextEvidenceValue(secret)
    assert secret not in repr(value)
    assert secret not in to_json(value)


def test_diagnostic_model_has_no_free_form_sensitive_payload():
    diagnostic = Diagnostic("PRIVACY_BLOCKED", "personal_data", "high", "trace-safe-1")
    serialized = to_json(diagnostic)
    assert serialized == (
        '{"category":"personal_data","code":"PRIVACY_BLOCKED",'
        '"severity":"high","technical_reference":"trace-safe-1"}'
    )


def test_identifiers_serialize_as_technical_values_only():
    serialized = to_json(AnalysisId("analysis-technical-1"))
    assert serialized == '{"value":"analysis-technical-1"}'
