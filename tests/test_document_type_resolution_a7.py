"""A7 fact-aware documentary resolution without legal inference."""

from __future__ import annotations

from RETIREMENT_PENIBILITY_ENGINE.career_import_models import (
    ImportBatch,
    ImportConfidence,
    ImportDocumentType,
    ImportProvenance,
    ImportStatus,
    ImportedCareerRecord,
)
from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_engine import CareerReconstructionEngine
from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_merger import (
    CareerReconstructionMerger,
)
from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_models import (
    DatePrecision,
    ReconstructionDate,
    ReconstructionRecord,
    ReconstructionRequest,
    ReconstructionStatus,
)
from RETIREMENT_PENIBILITY_ENGINE.document_resolution import (
    DocumentResolutionStrategy,
)
from RETIREMENT_PENIBILITY_ENGINE.document_resolution_models import (
    DocumentRole,
    FactFamily,
    FactResolutionStatus,
)


def provenance(document_type, source, confidence=ImportConfidence.MEDIUM):
    return ImportProvenance(
        f"source:{source}",
        document_type,
        f"document:{source}",
        "2026-07-21",
        "v1",
        f"synthetic:{source}",
        confidence,
    )


def record(
    record_id,
    document_type,
    values,
    *,
    confidence=ImportConfidence.MEDIUM,
    record_type="ImportedCareerRecord",
):
    return ReconstructionRecord(
        record_id,
        record_type,
        tuple(values.items()),
        object(),
        (provenance(document_type, record_id, confidence),),
    )


def merge(*records):
    return CareerReconstructionMerger().merge(tuple(records))


def resolution(result, field_name):
    return next(item for item in result.fact_resolutions if item.field_name == field_name)


def test_contract_wins_for_contractual_classification():
    result, conflicts = merge(
        record("payslip", ImportDocumentType.PAYSLIP, {"classification": "Applied", "classification_nature": "CONTRACTUAL"}),
        record("contract", ImportDocumentType.EMPLOYMENT_CONTRACT, {"classification": "Contractual", "classification_nature": "CONTRACTUAL"}),
    )
    item = resolution(result, "classification")
    assert item.fact_family is FactFamily.CONTRACTUAL_CLASSIFICATION
    assert item.selected_value == "Contractual"
    assert item.status is FactResolutionStatus.RESOLVED_WITH_WARNINGS
    assert conflicts


def test_payslip_wins_for_applied_classification():
    result, _ = merge(
        record("contract", ImportDocumentType.EMPLOYMENT_CONTRACT, {"classification": "Contractual", "classification_nature": "APPLIED"}),
        record("payslip", ImportDocumentType.PAYSLIP, {"classification": "Applied", "classification_nature": "APPLIED"}),
    )
    item = resolution(result, "classification")
    assert item.fact_family is FactFamily.APPLIED_CLASSIFICATION
    assert item.selected_value == "Applied"


def test_kelio_wins_only_for_recorded_working_time():
    result, _ = merge(
        record("payslip", ImportDocumentType.PAYSLIP, {"schedule": "Declared", "working_time_nature": "RECORDED"}),
        record("kelio", ImportDocumentType.KELIO_EXPORT, {"schedule": "Recorded", "working_time_nature": "RECORDED"}),
    )
    item = resolution(result, "schedule")
    assert item.fact_family is FactFamily.RECORDED_WORKING_TIME
    assert item.selected_value == "Recorded"


def test_career_statement_wins_for_declared_career_period():
    result, _ = merge(
        record("other", ImportDocumentType.OTHER, {"start_date": "2001-02-01", "end_date": "2001-12-31"}),
        record("statement", ImportDocumentType.CAREER_STATEMENT, {"start_date": "2001-01-01", "end_date": "2001-12-31"}),
    )
    item = resolution(result, "start_date")
    assert item.fact_family is FactFamily.CAREER_PERIOD
    assert item.selected_value == "2001-01-01"


def test_nibelis_wins_for_resolved_salary_rubric():
    result, _ = merge(
        record("payslip", ImportDocumentType.PAYSLIP, {"referential_rubric_id": "PAYSLIP-RUBRIC"}),
        record("nibelis", ImportDocumentType.NIBELIS_EXPORT, {"referential_rubric_id": "NIBELIS-RUBRIC"}),
    )
    item = resolution(result, "referential_rubric_id")
    assert item.fact_family is FactFamily.SALARY_ITEM
    assert item.selected_value == "NIBELIS-RUBRIC"


def test_later_amendment_role_wins_over_initial_contract():
    result, _ = merge(
        record("contract", ImportDocumentType.EMPLOYMENT_CONTRACT, {"position": "Initial", "start_date": "2001-01-01"}),
        record("amendment", ImportDocumentType.EMPLOYMENT_AMENDMENT, {"position": "Amended", "start_date": "2002-01-01"}),
    )
    item = resolution(result, "position")
    assert item.selected_record_id == "amendment"
    assert item.selected_value == "Amended"


def test_more_complete_covered_period_breaks_equal_source_tie():
    result, _ = merge(
        record("partial", ImportDocumentType.PAYSLIP, {"employer": "Partial", "start_date": "2001-01-01", "end_date": None}),
        record("complete", ImportDocumentType.PAYSLIP, {"employer": "Complete", "start_date": "2001-01-01", "end_date": "2001-12-31"}),
    )
    assert resolution(result, "employer").selected_value == "Complete"


def test_higher_confidence_breaks_equal_document_role_tie():
    result, _ = merge(
        record("low", ImportDocumentType.PAYSLIP, {"employer": "Low"}, confidence=ImportConfidence.LOW),
        record("high", ImportDocumentType.PAYSLIP, {"employer": "High"}, confidence=ImportConfidence.HIGH),
    )
    assert resolution(result, "employer").selected_value == "High"


def test_equal_rank_different_provenance_remains_conflict():
    result, conflicts = merge(
        record("left", ImportDocumentType.PAYSLIP, {"classification": "Left"}),
        record("right", ImportDocumentType.PAYSLIP, {"classification": "Right"}),
    )
    item = resolution(result, "classification")
    assert item.status is FactResolutionStatus.CONFLICT
    assert item.selected_value is None
    assert result.status is ReconstructionStatus.CONFLICTED
    assert len(item.provenance) == 2
    assert conflicts


def test_different_career_event_types_are_never_silently_merged():
    result, conflicts = merge(
        record("salary", ImportDocumentType.PAYSLIP, {"career_event_type": "SALARY_ITEM", "start_date": "2001-01-01", "end_date": "2001-01-31"}),
        record("absence", ImportDocumentType.PAYSLIP, {"career_event_type": "ABSENCE", "start_date": "2001-01-01", "end_date": "2001-01-31"}),
    )
    item = resolution(result, "career_event_type")
    assert item.status is FactResolutionStatus.CONFLICT
    assert dict(result.merged_values)["career_event_type"] is None
    assert dict(result.alternative_values)["career_event_type"] == ("ABSENCE", "SALARY_ITEM")
    assert conflicts


def test_unknown_conflicting_fact_is_not_overwritten():
    result, _ = merge(
        record("left", ImportDocumentType.PAYSLIP, {"unmapped_fact": "Left"}),
        record("right", ImportDocumentType.NIBELIS_EXPORT, {"unmapped_fact": "Right"}),
    )
    item = resolution(result, "unmapped_fact")
    assert item.status is FactResolutionStatus.UNSUPPORTED_FACT_TYPE
    assert item.selected_value is None


def test_resolution_order_is_stable_independent_of_input_order():
    contract = record("contract", ImportDocumentType.EMPLOYMENT_CONTRACT, {"employer": "Contract"})
    statement = record("statement", ImportDocumentType.CAREER_STATEMENT, {"employer": "Statement"})
    left, _ = merge(contract, statement)
    right, _ = merge(statement, contract)
    assert left.fact_resolutions == right.fact_resolutions
    assert left.resolution_order == right.resolution_order


def test_no_single_global_priority_decides_all_fact_families():
    strategy = DocumentResolutionStrategy()
    contract = record("contract", ImportDocumentType.EMPLOYMENT_CONTRACT, {"classification": "C", "classification_nature": "APPLIED", "schedule": "C", "working_time_nature": "RECORDED"})
    payslip = record("payslip", ImportDocumentType.PAYSLIP, {"classification": "P", "classification_nature": "APPLIED", "schedule": "P", "working_time_nature": "RECORDED"})
    kelio = record("kelio", ImportDocumentType.KELIO_EXPORT, {"schedule": "K", "working_time_nature": "RECORDED"})
    assert strategy.resolve("classification", (contract, payslip)).selected_record_id == "payslip"
    assert strategy.resolve("schedule", (contract, payslip, kelio)).selected_record_id == "kelio"


def test_document_roles_provenance_and_confidence_are_preserved():
    result, _ = merge(
        record("contract", ImportDocumentType.EMPLOYMENT_CONTRACT, {"position": "Contract"}, confidence=ImportConfidence.HIGH),
        record("payslip", ImportDocumentType.PAYSLIP, {"position": "Payslip"}, confidence=ImportConfidence.LOW),
    )
    item = resolution(result, "position")
    assert item.document_roles == (DocumentRole.EMPLOYMENT_CONTRACT, DocumentRole.PAYSLIP)
    assert item.confidences == (ImportConfidence.HIGH, ImportConfidence.LOW)
    assert len(item.provenance) == 2
    assert result.provenance == item.provenance


def test_real_reconstruction_pipeline_marks_different_event_types_conflicted():
    source = provenance(ImportDocumentType.PAYSLIP, "pipeline")
    records = (
        ImportedCareerRecord("salary", "SALARY_ITEM", (("start_date", "2001-01-01"), ("end_date", "2001-01-31")), source),
        ImportedCareerRecord("absence", "ABSENCE", (("start_date", "2001-01-01"), ("end_date", "2001-01-31")), source),
    )
    engine = CareerReconstructionEngine()
    context = engine.create_reconstruction_context(
        "context", ReconstructionRequest("request", "Synthetic question")
    )
    context = engine.add_import_batch(
        context,
        ImportBatch("batch", records=records, status=ImportStatus.VALIDATED),
    )
    proposal = engine.build_reconstruction_proposal(context)
    assert proposal.status is ReconstructionStatus.CONFLICTED
    event_resolution = resolution(proposal.merges[0], "career_event_type")
    assert event_resolution.status is FactResolutionStatus.CONFLICT
    assert event_resolution.selected_value is None


def test_more_precise_date_wins_for_equal_document_role():
    exact = record(
        "exact",
        ImportDocumentType.CAREER_STATEMENT,
        {"start_date": ReconstructionDate("2001-01-01", DatePrecision.EXACT), "end_date": "2001-12-31"},
    )
    approximate = record(
        "approximate",
        ImportDocumentType.CAREER_STATEMENT,
        {"start_date": ReconstructionDate("2001", DatePrecision.APPROXIMATE), "end_date": "2001-12-31"},
    )
    result, _ = merge(approximate, exact)
    assert resolution(result, "start_date").selected_record_id == "exact"


def test_corroborated_value_wins_between_otherwise_equal_sources():
    result, _ = merge(
        record("first", ImportDocumentType.PAYSLIP, {"employer": "Corroborated"}),
        record("second", ImportDocumentType.PAYSLIP, {"employer": "Corroborated"}),
        record("third", ImportDocumentType.PAYSLIP, {"employer": "Isolated"}),
    )
    item = resolution(result, "employer")
    assert item.status is FactResolutionStatus.RESOLVED_WITH_WARNINGS
    assert item.selected_value == "Corroborated"
