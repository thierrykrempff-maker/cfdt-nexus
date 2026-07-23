from dataclasses import dataclass

import pytest

from DOCUMENT_INTELLIGENCE_CENTER import (
    CSEMemoryMetadataAdapter,
    DocumentKind,
)


@dataclass
class Value:
    value: object


@dataclass
class SyntheticRecord:
    document_id: str
    source_relative_path: str
    source_sha256: str
    extraction_status: str
    warnings: list[str]
    metadata: dict[str, Value]


def _record(**changes) -> SyntheticRecord:
    values = {
        "document_id": "technical-source-id",
        "source_relative_path": r"C:\confidential\pv.pdf",
        "source_sha256": "storage-hash-must-not-be-copied",
        "extraction_status": "EXTRACTION_OK",
        "warnings": ["date à confirmer"],
        "metadata": {
            "title": Value("PV CSE synthétique"),
            "instance": Value("CSE"),
            "document_type": Value("CSE_MINUTES"),
            "meeting_date": Value("2026-06-10"),
            "confidence": Value(0.9),
        },
    }
    values.update(changes)
    return SyntheticRecord(**values)


def test_cse_adapter_preserves_safe_metadata_and_pseudonymizes_identity() -> None:
    adapted = CSEMemoryMetadataAdapter().adapt(_record())
    assert adapted is not None
    assert adapted.document_kind is DocumentKind.CSE_MINUTES
    assert adapted.instance == "CSE"
    assert adapted.pseudonymous_id.startswith("cse-")
    serialized = repr(adapted)
    assert "technical-source-id" not in serialized
    assert "confidential" not in serialized
    assert "storage-hash" not in serialized
    assert adapted.warnings == ("date à confirmer",)


def test_cse_adapter_is_stable() -> None:
    adapter = CSEMemoryMetadataAdapter()
    assert adapter.adapt(_record()).pseudonymous_id == adapter.adapt(
        _record()
    ).pseudonymous_id


def test_cse_adapter_ignores_non_indexable_record() -> None:
    assert CSEMemoryMetadataAdapter().adapt(
        _record(extraction_status="ERROR")
    ) is None


def test_cse_adapter_refuses_incomplete_metadata() -> None:
    with pytest.raises(ValueError, match="CSE_METADATA_INCOMPLETE"):
        CSEMemoryMetadataAdapter().adapt(
            _record(metadata={"title": Value("PV incomplet")})
        )
