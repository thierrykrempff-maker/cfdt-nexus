"""Executable privacy controls for synthetic retirement metadata."""

from __future__ import annotations

import ast
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from RETIREMENT_PENIBILITY_ENGINE.career_import_engine import CareerImportEngine
from RETIREMENT_PENIBILITY_ENGINE.career_import_models import (
    ImportBatch,
    ImportConfidence,
    ImportDocumentType,
    ImportProvenance,
    ImportStatus,
    ImportedEmploymentPeriod,
)
from RETIREMENT_PENIBILITY_ENGINE.career_import_pipeline import CareerImportPipeline
from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_engine import CareerReconstructionEngine
from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_models import ReconstructionRequest
from RETIREMENT_PENIBILITY_ENGINE.career_statement_connector import CareerStatementConnector
from RETIREMENT_PENIBILITY_ENGINE.career_statement_models import CareerStatementReportView
from RETIREMENT_PENIBILITY_ENGINE.career_timeline_engine import CareerTimelineEngine
from RETIREMENT_PENIBILITY_ENGINE.career_timeline_models import CareerEvent, CareerEventType, EvidenceLevel
from RETIREMENT_PENIBILITY_ENGINE.employment_contract_connector import EmploymentContractConnector
from RETIREMENT_PENIBILITY_ENGINE.employment_contract_models import EmploymentEmployer
from RETIREMENT_PENIBILITY_ENGINE.kelio_connector import KelioConnector
from RETIREMENT_PENIBILITY_ENGINE.nibelis_connector import NibelisConnector
from RETIREMENT_PENIBILITY_ENGINE.nibelis_models import NibelisEmployer, NibelisPayrollPeriod, NibelisSalaryItem
from RETIREMENT_PENIBILITY_ENGINE.payslip_connector import PayslipConnector
from RETIREMENT_PENIBILITY_ENGINE.payslip_models import PayslipEmployer
from RETIREMENT_PENIBILITY_ENGINE.privacy_gate import (
    PrivacyBlockedError,
    PrivacyInspectionError,
    RetirementPrivacyGate,
)
from RETIREMENT_PENIBILITY_ENGINE.privacy_models import PrivacyCategory, PrivacyStatus


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "RETIREMENT_PENIBILITY_ENGINE"
NIR_13_TEST = "2991299999999"
NIR_15_TEST = "299129999999901"
NIR_SEPARATED_TEST = "2 99 12 99 999 999 01"
IBAN_TEST = "FR76 0000 0000 0000 0000 0000 001"
RIB_TEST = "30004 00550 0000157841Z 25"
EMAIL_TEST = "personne.fictive@example.test"
PHONE_TEST = "06 00 00 00 00"
ADDRESS_TEST = "12 rue de la Fiction"


def gate():
    return RetirementPrivacyGate()


def provenance(origin="synthetic:test"):
    return ImportProvenance(
        "source-test",
        ImportDocumentType.PAYSLIP,
        "document-test",
        "2026-07-21",
        "v1",
        origin,
        ImportConfidence.MEDIUM,
    )


def batch(value="Employeur synthétique", *, status=ImportStatus.CREATED, synthetic_only=True, record_provenance=None):
    return ImportBatch(
        "batch-test",
        records=(
            ImportedEmploymentPeriod(
                "period-test",
                value,
                "2001-01-01",
                "2001-12-31",
                provenance() if record_provenance is None else record_provenance,
            ),
        ),
        status=status,
        synthetic_only=synthetic_only,
    )


def categories(value):
    return {item.category for item in gate().inspect(value).findings}


def test_privacy_layer_import_is_independent():
    script = (
        "import sys; before=set(sys.modules); "
        "import RETIREMENT_PENIBILITY_ENGINE.privacy_models; "
        "import RETIREMENT_PENIBILITY_ENGINE.privacy_detector; "
        "import RETIREMENT_PENIBILITY_ENGINE.privacy_gate; "
        "forbidden=('requests','httpx','urllib','ssl','socket'); "
        "loaded=sorted(name for name in set(sys.modules)-before if name.split('.')[0] in forbidden); "
        "assert not loaded, loaded"
    )
    completed = subprocess.run([sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr or completed.stdout


@pytest.mark.parametrize("value", [NIR_13_TEST, NIR_15_TEST, NIR_SEPARATED_TEST])
def test_detects_fictitious_nir_formats(value):
    assert PrivacyCategory.NIR in categories({"reference": value})


def test_detects_fictitious_iban():
    assert PrivacyCategory.IBAN in categories({"reference": IBAN_TEST})


def test_detects_fictitious_structured_rib():
    assert PrivacyCategory.RIB in categories({"reference": RIB_TEST})


@pytest.mark.parametrize("field", ["employee_id", "matricule", "personnel_number", "kelio_id", "nibelis_id"])
def test_detects_non_synthetic_internal_identifiers(field):
    assert PrivacyCategory.INTERNAL_IDENTIFIER in categories({field: "INTERNAL-987"})


def test_allows_explicitly_synthetic_internal_identifier():
    assert gate().inspect({"employee_id": "synthetic-employee-1"}).status is PrivacyStatus.SAFE


def test_detects_direct_identity_only_in_explicit_identity_field():
    assert PrivacyCategory.DIRECT_IDENTITY in categories({"last_name": "Personne Fictive"})
    assert gate().inspect({"employer": "Employeur synthétique"}).status is PrivacyStatus.SAFE


@pytest.mark.parametrize(
    "payload, expected",
    [
        ({"email": EMAIL_TEST}, PrivacyCategory.PERSONAL_EMAIL),
        ({"telephone": PHONE_TEST}, PrivacyCategory.PERSONAL_PHONE),
        ({"postal_address": ADDRESS_TEST}, PrivacyCategory.POSTAL_ADDRESS),
    ],
)
def test_detects_personal_contact_metadata(payload, expected):
    assert expected in categories(payload)


def test_rejects_real_source_and_real_document_markers():
    assert PrivacyCategory.REAL_SOURCE in categories({"source_reference": "production real_export"})
    assert PrivacyCategory.REAL_DOCUMENT in categories({"synthetic_only": False})
    assert PrivacyCategory.REAL_DOCUMENT in categories({"document_path": "C:\\private\\real.pdf"})


def test_safe_diagnostics_never_echo_inspected_values():
    secrets = (NIR_15_TEST, IBAN_TEST, RIB_TEST, EMAIL_TEST, PHONE_TEST, ADDRESS_TEST)
    inspection = gate().inspect({"notes": " | ".join(secrets)})
    diagnostic = gate().sanitize_diagnostic(inspection)
    rendered = repr(inspection)
    assert inspection.status is PrivacyStatus.BLOCKED
    assert all(secret not in diagnostic and secret not in rendered for secret in secrets)


@pytest.mark.parametrize(
    "value",
    [
        "2026",
        "2026-07-21",
        "151.67",
        "3250.42",
        "RUBRIC-12345",
        "COEFFICIENT-450",
        "10.00",
        "synthetic-employee-1",
        "opaque-document-reference",
    ],
)
def test_avoids_false_positives_on_common_metadata(value):
    assert gate().inspect({"declared_value": value}).status is PrivacyStatus.SAFE


def test_statuses_are_deterministic():
    assert gate().inspect({"title": "Fixture synthétique"}).status is PrivacyStatus.SAFE
    assert gate().inspect({"personal_note": "Revue manuelle"}).status is PrivacyStatus.SAFE_WITH_WARNINGS
    assert gate().inspect({"reference": NIR_13_TEST}).status is PrivacyStatus.BLOCKED
    assert gate().inspect(object()).status is PrivacyStatus.INSPECTION_ERROR


def test_missing_gate_and_unknown_input_fail_closed():
    with pytest.raises(PrivacyInspectionError, match="PRIVACY_GATE_REQUIRED"):
        CareerImportPipeline(privacy_gate=None).validate_for_reconstruction(batch())
    with pytest.raises(PrivacyInspectionError, match="PRIVACY_UNSUPPORTED_TYPE"):
        gate().assert_safe(object())


def test_pipeline_blocks_before_career_import():
    class ImportSpy:
        called = False

        def validate_batch(self, value):
            self.called = True
            raise AssertionError("Career Import must not receive blocked metadata")

    import_spy = ImportSpy()
    pipeline = CareerImportPipeline(import_engine=import_spy)
    with pytest.raises(PrivacyBlockedError, match="PRIVACY_NIR_DETECTED"):
        pipeline.validate_for_reconstruction(batch(NIR_13_TEST))
    assert import_spy.called is False


def test_career_import_engine_blocks_in_depth():
    with pytest.raises(PrivacyBlockedError, match="PRIVACY_IBAN_DETECTED"):
        CareerImportEngine().validate_batch(batch(IBAN_TEST))


def test_career_reconstruction_engine_blocks_in_depth():
    engine = CareerReconstructionEngine()
    context = engine.create_reconstruction_context(
        "context-test", ReconstructionRequest("request-test", "Question synthétique")
    )
    with pytest.raises(PrivacyBlockedError, match="PRIVACY_RIB_DETECTED"):
        engine.add_import_batch(context, batch(RIB_TEST, status=ImportStatus.VALIDATED))


def test_missing_provenance_blocks_before_reconstruction():
    invalid = replace(batch(), records=(replace(batch().records[0], provenance=None),))
    with pytest.raises(ValueError, match="PRIVACY_PROVENANCE_REQUIRED"):
        CareerImportPipeline().validate_for_reconstruction(invalid)
    with pytest.raises(ValueError, match="PRIVACY_PROVENANCE_REQUIRED"):
        CareerImportEngine().validate_batch(invalid)


def test_no_connector_report_is_built_after_blocking():
    class ReportSpy:
        called = False

        def build(self, *args):
            self.called = True
            raise AssertionError("Report must not be built")

    report_spy = ReportSpy()
    connector = CareerStatementConnector(report_builder=report_spy)
    source = connector.create_empty_statement("statement-test")
    source = replace(source, metadata=replace(source.metadata, source_reference=NIR_13_TEST))
    with pytest.raises(PrivacyBlockedError):
        connector.generate_import_report(source, CareerStatementReportView.EMPLOYEE_VIEW)
    assert report_spy.called is False


def test_safe_data_is_returned_unchanged_by_gate():
    source = batch()
    gate().assert_safe(source)
    assert source == batch()


def safe_connector_cases():
    statement_connector = CareerStatementConnector()
    payslip_connector = PayslipConnector()
    employment_connector = EmploymentContractConnector()
    kelio_connector = KelioConnector()
    nibelis_connector = NibelisConnector()
    return (
        (statement_connector, statement_connector.create_empty_statement("statement")),
        (
            payslip_connector,
            replace(payslip_connector.create_empty_payslip("payslip"), employer=PayslipEmployer("employer", "Employeur synthétique", "source")),
        ),
        (
            employment_connector,
            replace(employment_connector.create_empty_contract("contract"), employer=EmploymentEmployer("employer", "Employeur synthétique", "source")),
        ),
        (kelio_connector, kelio_connector.create_empty_export("kelio")),
        (
            nibelis_connector,
            replace(nibelis_connector.create_empty_export("nibelis"), employer=NibelisEmployer("employer", "Employeur synthétique", "source")),
        ),
    )


@pytest.mark.parametrize("index", range(5))
def test_five_connectors_accept_current_safe_synthetic_fixtures(index):
    connector, source = safe_connector_cases()[index]
    assert connector.prepare_reconstruction(source).reconstruction_proposal is not None


def test_nibelis_fail_closed_is_preserved():
    connector = NibelisConnector()
    source = replace(
        connector.create_empty_export("nibelis"),
        employer=NibelisEmployer("employer", None, "source"),
        periods=(NibelisPayrollPeriod("period", "employer", "2026-01-01", "2026-01-31"),),
        salary_items=(NibelisSalaryItem("item", "period", "RUBRIC-1", "1.00", None, None, None),),
    )
    assert connector.validate_export(source).valid is False


def test_kelio_anonymization_is_preserved():
    connector = KelioConnector()
    source = connector.create_empty_export("kelio")
    source = replace(source, employee=replace(source.employee, anonymized=False))
    assert connector.validate_export(source).valid is False


def test_timeline_defense_blocks_sensitive_description():
    engine = CareerTimelineEngine()
    timeline = engine.create_empty_timeline("timeline-test")
    event = CareerEvent("event", "2001-01-01", None, CareerEventType.COMPANY_ENTRY, NIR_13_TEST, "synthetic", EvidenceLevel.UNKNOWN)
    with pytest.raises(PrivacyBlockedError):
        engine.add_event(timeline, event)


def test_privacy_implementation_has_no_network_api_ocr_or_file_access():
    forbidden_imports = {"requests", "httpx", "urllib", "ssl", "socket"}
    forbidden_calls = {"open", "urlopen", "request", "get", "post"}
    violations = []
    for filename in ("privacy_models.py", "privacy_detector.py", "privacy_gate.py"):
        tree = ast.parse((PACKAGE / filename).read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in forbidden_imports:
                        violations.append((filename, node.lineno, alias.name))
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".", 1)[0] in forbidden_imports:
                violations.append((filename, node.lineno, node.module))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in forbidden_calls:
                violations.append((filename, node.lineno, node.func.id))
    assert violations == []
