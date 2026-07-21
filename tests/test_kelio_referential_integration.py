"""Integration tests for the shared Kelio payroll referential."""

from __future__ import annotations

import ast
import copy
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from automation.payroll import payroll_referential_validator
from RETIREMENT_PENIBILITY_ENGINE.career_import_engine import CareerImportEngine
from RETIREMENT_PENIBILITY_ENGINE.career_import_models import ImportBatch, ImportedEvidence
from RETIREMENT_PENIBILITY_ENGINE.kelio_connector import KelioConnector
from RETIREMENT_PENIBILITY_ENGINE.kelio_contract import KELIO_SAFETY_CONTRACT
from RETIREMENT_PENIBILITY_ENGINE.kelio_converter import KelioReferentialResolutionError
from RETIREMENT_PENIBILITY_ENGINE.kelio_models import (
    KelioConfidence,
    KelioCounter,
    KelioEmployee,
    KelioExport,
    KelioMetadata,
    KelioReportView,
)
from RETIREMENT_PENIBILITY_ENGINE.kelio_referential_adapter import PayrollKelioReferentialLookup
from RETIREMENT_PENIBILITY_ENGINE.kelio_referential_contract import KelioReferentialLookup
from RETIREMENT_PENIBILITY_ENGINE.kelio_referential_models import (
    KelioCounterMetadata,
    KelioCounterResolution,
    KelioResolutionStatus,
)
from RETIREMENT_PENIBILITY_ENGINE.privacy_gate import PrivacyBlockedError


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "RETIREMENT_PENIBILITY_ENGINE"
CATALOG = payroll_referential_validator.load_catalog("kelio")
COUNTER_IDS = tuple(item["counter_id"] for item in CATALOG["counters"])
COUNTER_TYPES = {item["counter_type"] for item in CATALOG["counters"]}


def export(counter_id="KELIO_HS_SYN", value="10.00"):
    return KelioExport(
        KelioMetadata(
            "export-test",
            "synthetic:kelio-export",
            "2026-07-21",
            "v1",
            KelioConfidence.MEDIUM,
        ),
        KelioEmployee("synthetic-employee-test"),
        counters=(KelioCounter(counter_id, "Compteur synthétique", value, "2026-07-21"),),
    )


def metadata(counter_id="KELIO_HS_SYN", status=KelioResolutionStatus.RESOLVED):
    return KelioCounterMetadata(
        "kelio-counters-synthetic-v1:1.1.0",
        counter_id,
        "overtime",
        "KELIO_COUNTER_REFERENTIAL",
        status,
        "WORKING_TIME",
        True,
        False,
        "payroll-referential:kelio-counters-synthetic-v1:1.1.0",
    )


class InMemoryLookup:
    def __init__(self, known=("KELIO_HS_SYN",), *, error=False, order=None):
        self.known = frozenset(known)
        self.error = error
        self.order = order

    def resolve_counter(self, counter_id):
        if self.order is not None:
            self.order.append("lookup")
        if self.error:
            raise RuntimeError("synthetic lookup failure")
        if counter_id not in self.known:
            return KelioCounterResolution(counter_id, KelioResolutionStatus.UNKNOWN, code="KELIO_COUNTER_UNKNOWN")
        item = metadata(counter_id)
        return KelioCounterResolution(counter_id, KelioResolutionStatus.RESOLVED, item)

    def is_known_counter(self, counter_id):
        return counter_id in self.known

    def get_counter_metadata(self, counter_id):
        return metadata(counter_id) if counter_id in self.known else None

    def list_supported_counter_ids(self):
        return tuple(sorted(self.known))


def adapter_for(catalog, validator=lambda value: {"valid": True}):
    return PayrollKelioReferentialLookup(lambda: copy.deepcopy(catalog), validator)


def test_lookup_contract_import_is_independent():
    script = (
        "import sys; before=set(sys.modules); "
        "import RETIREMENT_PENIBILITY_ENGINE.kelio_referential_contract; "
        "assert 'RETIREMENT_PENIBILITY_ENGINE.kelio_referential_adapter' not in sys.modules; "
        "assert 'automation.payroll.payroll_referential_validator' not in set(sys.modules)-before"
    )
    completed = subprocess.run([sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_contract_has_no_implementation_dependency():
    tree = ast.parse((PACKAGE / "kelio_referential_contract.py").read_text(encoding="utf-8-sig"))
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert not any(module and "adapter" in module for module in imports)


def test_existing_catalog_is_loaded_and_validated_by_existing_validator():
    report = payroll_referential_validator.validate_catalog("kelio")
    assert report["valid"] is True
    assert report["records_count"] == 17
    assert len(PayrollKelioReferentialLookup().list_supported_counter_ids()) == 17


def test_lookup_implements_public_contract():
    assert isinstance(PayrollKelioReferentialLookup(), KelioReferentialLookup)


@pytest.mark.parametrize("counter_id", COUNTER_IDS)
def test_all_existing_synthetic_counters_resolve(counter_id):
    resolution = PayrollKelioReferentialLookup().resolve_counter(counter_id)
    assert resolution.status is KelioResolutionStatus.RESOLVED
    assert resolution.metadata.canonical_counter_id == counter_id
    assert resolution.metadata.synthetic_only is True
    assert resolution.metadata.calculation_allowed is False


@pytest.mark.parametrize("category", sorted(COUNTER_TYPES))
def test_existing_counter_categories_are_preserved(category):
    record = next(item for item in CATALOG["counters"] if item["counter_type"] == category)
    resolved = PayrollKelioReferentialLookup().resolve_counter(record["counter_id"])
    assert resolved.metadata.category == category


def test_counter_code_resolves_to_canonical_identifier():
    result = PayrollKelioReferentialLookup().resolve_counter("HS_SYN")
    assert result.metadata.canonical_counter_id == "KELIO_HS_SYN"


def test_enrichment_is_technical_and_keeps_raw_value_unchanged():
    source = export(value="12.50")
    information = KelioConnector().extract_working_time(source)
    resolution = information.counter_resolutions[0]
    assert source.counters[0].declared_value == "12.50"
    assert resolution.metadata.category == "overtime"
    assert resolution.metadata.evidence_kind == "WORKING_TIME"
    assert resolution.metadata.provenance.startswith("payroll-referential:")


def test_empty_identifier_is_unknown_and_connector_refuses_it():
    result = PayrollKelioReferentialLookup().resolve_counter("")
    assert result.status is KelioResolutionStatus.UNKNOWN
    source = replace(export(), counters=(replace(export().counters[0], counter_id=""),))
    with pytest.raises(ValueError):
        KelioConnector().convert_to_import_batch(source)


def test_unknown_counter_is_refused_without_fallback():
    with pytest.raises(KelioReferentialResolutionError, match="KELIO_COUNTER_UNKNOWN"):
        KelioConnector().convert_to_import_batch(export("KELIO_UNKNOWN"))


def test_ambiguous_counter_is_refused():
    catalog = copy.deepcopy(CATALOG)
    duplicate = copy.deepcopy(catalog["counters"][0])
    duplicate["counter_code"] = duplicate["counter_id"]
    catalog["counters"].append(duplicate)
    lookup = adapter_for(catalog)
    result = lookup.resolve_counter(duplicate["counter_id"])
    assert result.status is KelioResolutionStatus.LOOKUP_ERROR
    assert result.code == "KELIO_COUNTER_AMBIGUOUS"


@pytest.mark.parametrize(
    "loader, validator",
    [
        (lambda: (_ for _ in ()).throw(FileNotFoundError()), lambda value: {"valid": True}),
        (lambda: copy.deepcopy(CATALOG), lambda value: {"valid": False}),
        (lambda: None, lambda value: {"valid": True}),
    ],
)
def test_missing_or_invalid_referential_fails_closed(loader, validator):
    result = PayrollKelioReferentialLookup(loader, validator).resolve_counter("KELIO_HS_SYN")
    assert result.status is KelioResolutionStatus.LOOKUP_ERROR


def test_lookup_exception_is_safely_refused():
    with pytest.raises(KelioReferentialResolutionError, match="KELIO_REFERENTIAL_LOOKUP_ERROR"):
        KelioConnector(referential_lookup=InMemoryLookup(error=True)).convert_to_import_batch(export())


@pytest.mark.parametrize(
    "change, expected_code",
    [
        ({"synthetic_only": False}, "KELIO_COUNTER_NOT_SYNTHETIC"),
        ({"calculation_allowed": True}, "KELIO_COUNTER_CALCULATION_PROHIBITED"),
        ({"validation_status": "rejected"}, "KELIO_COUNTER_REJECTED"),
        ({"confidentiality": "private"}, "KELIO_COUNTER_CONFIDENTIAL"),
    ],
)
def test_incompatible_counter_metadata_is_refused(change, expected_code):
    catalog = copy.deepcopy(CATALOG)
    catalog["counters"][0].update(change)
    result = adapter_for(catalog).resolve_counter(catalog["counters"][0]["counter_id"])
    assert result.status is KelioResolutionStatus.INCOMPATIBLE
    assert result.code == expected_code


@pytest.mark.parametrize("validation_status", ["draft", "to_verify"])
def test_review_status_resolves_with_warnings(validation_status):
    catalog = copy.deepcopy(CATALOG)
    catalog["counters"][0]["validation_status"] = validation_status
    result = adapter_for(catalog).resolve_counter(catalog["counters"][0]["counter_id"])
    assert result.status is KelioResolutionStatus.RESOLVED_WITH_WARNINGS
    assert result.warnings == ("KELIO_COUNTER_REQUIRES_HUMAN_REVIEW",)


def test_absent_or_invalid_injected_lookup_fails_closed():
    with pytest.raises(KelioReferentialResolutionError, match="KELIO_REFERENTIAL_REQUIRED"):
        KelioConnector(referential_lookup=None).convert_to_import_batch(export())
    with pytest.raises(KelioReferentialResolutionError, match="KELIO_REFERENTIAL_INVALID"):
        KelioConnector(referential_lookup=object()).convert_to_import_batch(export())


def test_in_memory_lookup_is_injectable():
    connector = KelioConnector(referential_lookup=InMemoryLookup())
    assert connector.convert_to_import_batch(export()).records


def test_privacy_gate_runs_before_lookup():
    class LookupSpy(InMemoryLookup):
        called = False

        def resolve_counter(self, counter_id):
            self.called = True
            return super().resolve_counter(counter_id)

    lookup = LookupSpy()
    unsafe = replace(export(), counters=(replace(export().counters[0], label="2991299999999"),))
    with pytest.raises(PrivacyBlockedError):
        KelioConnector(referential_lookup=lookup).convert_to_import_batch(unsafe)
    assert lookup.called is False


def test_lookup_runs_before_career_import_pipeline():
    order = []

    class PipelineSpy:
        def create_reconstruction_context(self, *args):
            order.append("career_import")
            return args

        def add_import_batch(self, context, batch):
            return context

        def build_reconstruction_proposal(self, context):
            return context

    KelioConnector(
        referential_lookup=InMemoryLookup(order=order),
        import_pipeline=PipelineSpy(),
    ).prepare_reconstruction(export())
    assert order == ["lookup", "career_import"]


def test_connector_has_no_direct_reconstruction_import():
    source = (PACKAGE / "kelio_connector.py").read_text(encoding="utf-8-sig")
    assert "career_reconstruction_engine" not in source
    assert "CareerReconstructionEngine" not in source


def test_anonymization_and_synthetic_guards_remain_active():
    connector = KelioConnector()
    anonymous = replace(export(), employee=replace(export().employee, anonymized=False))
    real = replace(export(), metadata=replace(export().metadata, synthetic_only=False))
    assert connector.validate_export(anonymous).valid is False
    assert connector.validate_export(real).valid is False


def test_existing_reports_remain_compatible_and_show_canonical_counter():
    connector = KelioConnector()
    employee = connector.generate_import_report(export(), KelioReportView.EMPLOYEE_VIEW)
    expert = connector.generate_import_report(export(), KelioReportView.EXPERT_VIEW)
    assert employee.resolved_counter_ids == ()
    assert expert.resolved_counter_ids == ("KELIO_HS_SYN",)
    assert expert.counters == ("Compteur synthétique:10.00",)


def test_import_batch_contains_referential_evidence_only():
    batch = KelioConnector().convert_to_import_batch(export())
    evidence = tuple(item for item in batch.records if isinstance(item, ImportedEvidence))
    assert len(evidence) == 1
    assert evidence[0].reference == "KELIO_HS_SYN"
    assert not hasattr(evidence[0], "content")


def test_reconstruction_and_downstream_compatibility_flags_remain_active():
    prepared = KelioConnector().prepare_reconstruction(export())
    assert isinstance(prepared.import_batch, ImportBatch)
    assert prepared.reconstruction_proposal is not None
    assert CareerImportEngine().prepare_evidence_records(
        replace(prepared.import_batch, status=prepared.import_batch.status)
    ).synthetic_only is True
    assert all(
        (
            KELIO_SAFETY_CONTRACT.career_timeline_compatible,
            KELIO_SAFETY_CONTRACT.career_evidence_compatible,
            KELIO_SAFETY_CONTRACT.potential_rights_compatible,
        )
    )


def test_adapter_has_no_network_api_ocr_or_real_document_reader():
    source = (PACKAGE / "kelio_referential_adapter.py").read_text(encoding="utf-8-sig")
    forbidden = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "HTMLParser",
        "ElementTree",
        "pytesseract",
        "pdfplumber",
        "pypdf",
        "open(",
    )
    assert not any(marker in source for marker in forbidden)
