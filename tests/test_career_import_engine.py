"""Offline architecture tests for the Career Import Engine LOT 7."""

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from RETIREMENT_PENIBILITY_ENGINE.career_import_contract import (
    CAREER_IMPORT_SAFETY_CONTRACT,
    CareerImportEngine,
    CareerImportPort,
)
from RETIREMENT_PENIBILITY_ENGINE.career_import_models import (
    ImportBatch,
    ImportConfidence,
    ImportConflictType,
    ImportDocument,
    ImportDocumentType,
    ImportIssueType,
    ImportProvenance,
    ImportReportView,
    ImportSource,
    ImportedCareerRecord,
    ImportedClassification,
    ImportedEmploymentPeriod,
    ImportedEvidence,
    ImportedNightWork,
)
from RETIREMENT_PENIBILITY_ENGINE.career_import_policy import CAREER_IMPORT_POLICY
from RETIREMENT_PENIBILITY_ENGINE.career_import_provenance import ImportProvenanceManager
from RETIREMENT_PENIBILITY_ENGINE.career_timeline_models import CareerEventType, EvidenceLevel


def source(
    source_id: str = "source-1",
    document_type: ImportDocumentType = ImportDocumentType.PAYSLIP,
    version: str = "v1",
    origin: str = "synthetic-origin",
) -> ImportSource:
    return ImportSource(
        source_id,
        document_type,
        "internal-document-1",
        "2026-01-01",
        version,
        origin,
        ImportConfidence.MEDIUM,
    )


def provenance(source_id: str = "source-1", version: str = "v1") -> ImportProvenance:
    return ImportProvenanceManager.from_source(source(source_id, version=version))


def test_contract_is_architecture_only_and_prohibits_real_imports() -> None:
    contract = CAREER_IMPORT_SAFETY_CONTRACT
    assert contract.status == "ARCHITECTURE_ONLY"
    assert contract.enabled is False
    assert contract.file_reading_allowed is False
    assert contract.pdf_parsing_allowed is False
    assert contract.ocr_allowed is False
    assert contract.api_allowed is False
    assert contract.network_allowed is False
    assert contract.automatic_reconstruction_allowed is False


def test_public_methods_are_declared() -> None:
    assert {
        "create_import_batch", "validate_batch", "normalize_batch", "detect_conflicts",
        "build_import_summary", "generate_report", "prepare_timeline_records",
        "prepare_evidence_records",
    } <= set(CareerImportPort.__dict__)


def test_create_batch_is_empty_immutable_and_synthetic() -> None:
    batch = CareerImportEngine().create_import_batch("batch-1")
    assert batch.documents == batch.records == ()
    assert batch.synthetic_only is True
    with pytest.raises(FrozenInstanceError):
        batch.batch_id = "changed"


def test_provenance_contains_all_mandatory_metadata() -> None:
    item = provenance()
    assert item.document_type is ImportDocumentType.PAYSLIP
    assert item.internal_document_id == "internal-document-1"
    assert item.imported_at == "2026-01-01"
    assert item.version == "v1"
    assert item.origin == "synthetic-origin"
    assert item.confidence is ImportConfidence.MEDIUM


def test_incomplete_provenance_is_rejected() -> None:
    incomplete = ImportSource("", ImportDocumentType.OTHER, "", "", "", "")
    with pytest.raises(ValueError, match="provenance"):
        ImportProvenanceManager.from_source(incomplete)


def test_normalization_is_separate_and_preserves_original_values() -> None:
    record = ImportedCareerRecord(
        "record-1",
        "NIGHT_WORK",
        (
            ("start_date", " 2020-01-01 "),
            ("employer", " synthetic employer "),
            ("classification", " level a "),
            ("work_schedule", " night   shift "),
        ),
        provenance(),
    )
    batch = ImportBatch("batch-1", records=(record,))
    normalized = CareerImportEngine().normalize_batch(batch)[0]
    assert record.original_values[0][1] == " 2020-01-01 "
    assert dict(normalized.normalized_values) == {
        "start_date": "2020-01-01",
        "employer": "Synthetic Employer",
        "classification": "LEVEL A",
        "work_schedule": "night shift",
    }
    assert normalized.original_values is record.original_values


def test_validation_detects_required_fields_dates_periods_and_unknowns() -> None:
    records = (
        ImportedEmploymentPeriod("", "UNKNOWN", "2020-99-01", None, provenance()),
        ImportedEmploymentPeriod("period-2", "Synthetic", "2021-02-01", "2021-01-01", provenance()),
    )
    validation = CareerImportEngine().validate_batch(ImportBatch("batch-1", records=records))
    issue_types = {item.issue_type for item in validation.issues}
    assert {
        ImportIssueType.REQUIRED_FIELD,
        ImportIssueType.INVALID_DATE_FORMAT,
        ImportIssueType.INCOHERENT_PERIOD,
        ImportIssueType.UNKNOWN_VALUE,
    } <= issue_types


def test_validation_detects_duplicates() -> None:
    record = ImportedEmploymentPeriod("period-1", "Synthetic", "2020-01-01", "2020-12-31", provenance())
    validation = CareerImportEngine().validate_batch(ImportBatch("batch-1", records=(record, record)))
    assert any(item.issue_type is ImportIssueType.DUPLICATE for item in validation.issues)


def test_validation_detects_overlaps() -> None:
    left = ImportedEmploymentPeriod("left", "Synthetic", "2020-01-01", "2020-12-31", provenance("left-source"))
    right = ImportedEmploymentPeriod("right", "Synthetic", "2020-06-01", "2021-01-01", provenance("right-source"))
    validation = CareerImportEngine().validate_batch(ImportBatch("batch-1", records=(left, right)))
    assert any(item.issue_type is ImportIssueType.OVERLAP for item in validation.issues)


def test_conflicts_are_detected_and_both_records_retained() -> None:
    left = ImportedEmploymentPeriod("left", "Employer A", "2020-01-01", "2020-12-31", provenance("left-source"))
    right = ImportedEmploymentPeriod("right", "Employer B", "2020-01-01", "2020-12-31", provenance("right-source"))
    batch = ImportBatch("batch-1", records=(left, right))
    conflicts = CareerImportEngine().detect_conflicts(batch)
    assert conflicts[0].conflict_type is ImportConflictType.INCOMPATIBLE_EMPLOYERS
    assert batch.records == (left, right)
    assert conflicts[0].provenance_ids == ("left-source", "right-source")


def test_classification_schedule_and_evidence_conflicts() -> None:
    records = (
        ImportedClassification("class-a", "A", "100", "2020-01-01", "2020-12-31", provenance("a")),
        ImportedClassification("class-b", "B", "200", "2020-01-01", "2020-12-31", provenance("b")),
        ImportedNightWork("night-a", "2020-01-01", "2020-12-31", "schedule-a", provenance("c")),
        ImportedNightWork("night-b", "2020-01-01", "2020-12-31", "schedule-b", provenance("d")),
        ImportedEvidence("evidence-1", "PAYSLIP", "PROVIDED", "reference-a", provenance("e")),
        ImportedEvidence("evidence-1", "PAYSLIP", "CONTRADICTED", "reference-b", provenance("f")),
    )
    types = {item.conflict_type for item in CareerImportEngine().detect_conflicts(ImportBatch("batch-1", records=records))}
    assert {
        ImportConflictType.INCOMPATIBLE_CLASSIFICATIONS,
        ImportConflictType.INCOMPATIBLE_SCHEDULES,
        ImportConflictType.CONTRADICTORY_EVIDENCE,
    } <= types


def test_different_documents_and_versions_are_retained() -> None:
    left_source = source("source-left", version="v1")
    right_source = ImportSource(
        "source-right", ImportDocumentType.PAYSLIP, left_source.internal_document_id,
        "2026-02-01", "v2", "synthetic-origin", ImportConfidence.MEDIUM,
    )
    documents = (
        ImportDocument("document-left", left_source, "Synthetic left", declared_record_ids=("record-1",)),
        ImportDocument("document-right", right_source, "Synthetic right", declared_record_ids=("record-1",)),
    )
    conflicts = CareerImportEngine().detect_conflicts(ImportBatch("batch-1", documents=documents))
    assert {item.conflict_type for item in conflicts} == {
        ImportConflictType.DIFFERENT_DOCUMENTS,
        ImportConflictType.DIFFERENT_VERSIONS,
    }


def test_employee_report_contains_received_missing_and_next_steps() -> None:
    document = ImportDocument("document-1", source(), "Synthetic document", complete=False)
    batch = ImportBatch("batch-1", documents=(document,))
    engine = CareerImportEngine()
    validation = engine.validate_batch(batch)
    report = engine.generate_report(
        batch, validation, (), (), ImportReportView.EMPLOYEE_VIEW
    )
    assert report.documents_received == ("Synthetic document",)
    assert report.missing_documents
    assert report.next_steps
    assert report.provenance == report.normalizations == ()


def test_expert_report_contains_sanitized_provenance_normalization_and_conflicts() -> None:
    unsafe_source = source(origin=r"C:\private\secret.pdf")
    item_provenance = ImportProvenanceManager.from_source(unsafe_source)
    record = ImportedCareerRecord(
        "record-1", "NIGHT_WORK", (("work_schedule", " night  shift "),), item_provenance
    )
    batch = ImportBatch("batch-1", records=(record,))
    engine = CareerImportEngine()
    validation = engine.validate_batch(batch)
    normalizations = engine.normalize_batch(batch)
    report = engine.generate_report(
        batch, validation, normalizations, (), ImportReportView.EXPERT_VIEW
    )
    rendered = repr(report)
    assert report.normalizations
    assert report.provenance == ("[REDACTED]",)
    assert "C:\\private" not in rendered
    assert "secret" not in rendered.lower()


def test_prepare_timeline_uses_only_explicitly_typed_records() -> None:
    record = ImportedCareerRecord(
        "event-1",
        "NIGHT_WORK",
        (("start_date", "2020-01-01"), ("end_date", "2020-12-31")),
        provenance(),
    )
    batch = ImportBatch("batch-1", records=(record,))
    engine = CareerImportEngine()
    timeline = engine.prepare_timeline_records(batch, engine.normalize_batch(batch))
    assert timeline.events[0].event_type is CareerEventType.NIGHT_WORK
    assert timeline.events[0].evidence_level is EvidenceLevel.UNKNOWN
    assert timeline.synthetic_only is True


def test_prepare_evidence_uses_references_only() -> None:
    record = ImportedEvidence(
        "evidence-1", "PAYSLIP", "PROVIDED", "opaque-reference", provenance()
    )
    bundle = CareerImportEngine().prepare_evidence_records(ImportBatch("batch-1", records=(record,)))
    assert bundle.evidence[0].reference.reference == "opaque-reference"
    assert not hasattr(bundle.evidence[0].reference, "content")
    assert bundle.synthetic_only is True


def test_document_type_validation_and_conflict_catalogs_are_complete() -> None:
    assert len(ImportDocumentType) == 12
    assert len(ImportIssueType) == 8
    assert len(ImportConflictType) == 7
    assert len(CAREER_IMPORT_POLICY) == 7


def test_lot_has_no_network_pdf_ocr_api_or_file_reading_imports() -> None:
    root = Path(__file__).parents[1] / "RETIREMENT_PENIBILITY_ENGINE"
    paths = tuple(root.glob("career_import_*.py"))
    forbidden = {
        "aiohttp", "bs4", "cv2", "html.parser", "http.client", "openai", "pdfplumber",
        "pypdf", "pytesseract", "requests", "scrapy", "socket", "ssl", "urllib",
        "urllib.request", "xml.etree.ElementTree",
    }
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        assert forbidden.isdisjoint(imports), path.name
        source_text = path.read_text(encoding="utf-8")
        assert "urlopen(" not in source_text
        assert "open(" not in source_text
        assert "automation.official_knowledge.connectors" not in source_text
