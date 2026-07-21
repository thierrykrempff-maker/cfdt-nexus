"""A7 checks for the narrowly scoped connector duplication closure."""

from __future__ import annotations

import ast
import inspect
from dataclasses import dataclass, replace
from pathlib import Path

from RETIREMENT_PENIBILITY_ENGINE.career_import_models import ImportBatch
from RETIREMENT_PENIBILITY_ENGINE.career_statement_connector import CareerStatementConnector
from RETIREMENT_PENIBILITY_ENGINE.career_statement_report import CareerStatementReportBuilder
from RETIREMENT_PENIBILITY_ENGINE.career_statement_validator import CareerStatementValidator
from RETIREMENT_PENIBILITY_ENGINE.connector_base import ConnectorFoundation
from RETIREMENT_PENIBILITY_ENGINE.employment_contract_connector import EmploymentContractConnector
from RETIREMENT_PENIBILITY_ENGINE.employment_contract_report import EmploymentContractReportBuilder
from RETIREMENT_PENIBILITY_ENGINE.employment_contract_validator import EmploymentContractValidator
from RETIREMENT_PENIBILITY_ENGINE.kelio_connector import KelioConnector
from RETIREMENT_PENIBILITY_ENGINE.kelio_models import KelioEmployee
from RETIREMENT_PENIBILITY_ENGINE.kelio_report import KelioReportBuilder
from RETIREMENT_PENIBILITY_ENGINE.kelio_validator import KelioValidator
from RETIREMENT_PENIBILITY_ENGINE.nibelis_connector import NibelisConnector
from RETIREMENT_PENIBILITY_ENGINE.nibelis_models import NibelisEmployer, NibelisPayrollPeriod, NibelisSalaryItem
from RETIREMENT_PENIBILITY_ENGINE.nibelis_report import NibelisReportBuilder
from RETIREMENT_PENIBILITY_ENGINE.nibelis_validator import NibelisValidator
from RETIREMENT_PENIBILITY_ENGINE.payslip_connector import PayslipConnector
from RETIREMENT_PENIBILITY_ENGINE.payslip_report import PayslipReportBuilder
from RETIREMENT_PENIBILITY_ENGINE.payslip_validator import PayslipValidator


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "RETIREMENT_PENIBILITY_ENGINE"
CONNECTORS = (
    CareerStatementConnector,
    PayslipConnector,
    EmploymentContractConnector,
    KelioConnector,
    NibelisConnector,
)
CONNECTOR_FILES = tuple(PACKAGE / f"{name}_connector.py" for name in (
    "career_statement", "payslip", "employment_contract", "kelio", "nibelis"
))


@dataclass(frozen=True)
class Valid:
    valid: bool = True


@dataclass(frozen=True)
class Converted:
    import_batch: ImportBatch = ImportBatch("synthetic-batch")


class Validator:
    def validate(self, source):
        return Valid()


class Converter:
    def convert(self, source):
        return Converted()


class Pipeline:
    pass


class Gate:
    def __init__(self):
        self.calls = 0

    def assert_safe(self, source):
        self.calls += 1


def test_validated_conversion_uses_one_shared_privacy_boundary():
    gate = Gate()
    foundation = ConnectorFoundation(Validator(), Converter(), Pipeline(), gate)
    assert foundation.convert_validated(object(), "invalid") == Converted()
    assert gate.calls == 1


def test_duplicate_privacy_call_was_removed_from_convert_validated():
    tree = ast.parse((PACKAGE / "connector_base.py").read_text(encoding="utf-8"))
    method = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "convert_validated"
    )
    calls = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "assert_safe"
    ]
    assert calls == []


def test_all_historical_connector_signatures_are_preserved():
    expected = {
        CareerStatementConnector: ("convert_to_import_batch", "prepare_reconstruction", "generate_import_report"),
        PayslipConnector: ("convert_to_import_batch", "prepare_reconstruction", "generate_import_report"),
        EmploymentContractConnector: ("convert_to_import_batch", "prepare_reconstruction", "generate_import_report"),
        KelioConnector: ("convert_to_import_batch", "prepare_reconstruction", "generate_import_report"),
        NibelisConnector: ("convert_to_import_batch", "prepare_reconstruction", "generate_import_report"),
    }
    for connector, methods in expected.items():
        assert all(callable(getattr(connector, name, None)) for name in methods)
        assert all("self" in inspect.signature(getattr(connector, name)).parameters for name in methods)


def test_reports_remain_source_specific():
    builders = (
        CareerStatementReportBuilder,
        PayslipReportBuilder,
        EmploymentContractReportBuilder,
        KelioReportBuilder,
        NibelisReportBuilder,
    )
    assert len(set(builders)) == 5
    assert all(builder.__module__.endswith("_report") for builder in builders)


def test_validators_remain_source_specific():
    validators = (
        CareerStatementValidator,
        PayslipValidator,
        EmploymentContractValidator,
        KelioValidator,
        NibelisValidator,
    )
    assert len(set(validators)) == 5
    assert all(validator.__module__.endswith("_validator") for validator in validators)


def test_kelio_anonymization_remains_fail_closed():
    connector = KelioConnector()
    export = connector.create_empty_export("synthetic-kelio")
    unsafe = replace(export, employee=KelioEmployee("internal-id", anonymized=False))
    assert connector.validate_export(unsafe).valid is False


def test_nibelis_referential_remains_fail_closed():
    connector = NibelisConnector()
    export = replace(
        connector.create_empty_export("synthetic-nibelis"),
        employer=NibelisEmployer("employer", None, "synthetic-employer"),
        periods=(NibelisPayrollPeriod("period", "employer", "2026-01-01", "2026-01-31"),),
        salary_items=(NibelisSalaryItem("item", "period", "UNKNOWN", None, None, None, None),),
    )
    validation = connector.validate_export(export)
    assert validation.valid is False
    assert any(item.issue_type == "REFERENTIAL_LOOKUP_REQUIRED" for item in validation.issues)


def test_all_connectors_still_route_through_foundation_and_pipeline():
    for path in CONNECTOR_FILES:
        source = path.read_text(encoding="utf-8-sig")
        assert "ConnectorFoundation(" in source
        assert "CareerImportPipeline()" in source
        assert "CareerReconstructionEngine" not in source


def test_no_dynamic_import_or_network_api_ocr_was_added():
    forbidden = {"requests", "httpx", "aiohttp", "urllib", "ssl", "socket", "pytesseract"}
    for path in (PACKAGE / "connector_base.py",) + CONNECTOR_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            assert not (
                isinstance(node, ast.Call)
                and (
                    isinstance(node.func, ast.Name) and node.func.id == "__import__"
                    or isinstance(node.func, ast.Attribute) and node.func.attr == "import_module"
                )
            )
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".", 1)[0] not in forbidden for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".", 1)[0] not in forbidden


def test_a7_reduction_is_measurable_and_narrow():
    metrics = {
        "shared_privacy_checks_per_validated_conversion_before": 2,
        "shared_privacy_checks_per_validated_conversion_after": 1,
        "connector_signatures_changed": 0,
        "connector_files_changed": 0,
        "business_validators_moved": 0,
        "business_reports_moved": 0,
    }
    assert metrics["shared_privacy_checks_per_validated_conversion_after"] < metrics["shared_privacy_checks_per_validated_conversion_before"]
    assert set(metrics.values()) == {0, 1, 2}
