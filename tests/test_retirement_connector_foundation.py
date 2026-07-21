"""Cross-connector tests for the small shared retirement foundation."""

from __future__ import annotations

import ast
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from RETIREMENT_PENIBILITY_ENGINE.career_import_models import ImportBatch
from RETIREMENT_PENIBILITY_ENGINE.career_statement_connector import (
    CareerStatementConnector,
)
from RETIREMENT_PENIBILITY_ENGINE.career_statement_contract import (
    CAREER_STATEMENT_SAFETY_CONTRACT,
)
from RETIREMENT_PENIBILITY_ENGINE.career_statement_models import (
    CareerStatementReportView,
)
from RETIREMENT_PENIBILITY_ENGINE.connector_contract import RetirementSourceConnector
from RETIREMENT_PENIBILITY_ENGINE.employment_contract_connector import (
    EmploymentContractConnector,
)
from RETIREMENT_PENIBILITY_ENGINE.employment_contract_contract import (
    EMPLOYMENT_CONTRACT_SAFETY_CONTRACT,
)
from RETIREMENT_PENIBILITY_ENGINE.employment_contract_models import (
    EmploymentEmployer,
    EmploymentReportView,
)
from RETIREMENT_PENIBILITY_ENGINE.kelio_connector import KelioConnector
from RETIREMENT_PENIBILITY_ENGINE.kelio_contract import KELIO_SAFETY_CONTRACT
from RETIREMENT_PENIBILITY_ENGINE.kelio_models import KelioReportView
from RETIREMENT_PENIBILITY_ENGINE.nibelis_connector import NibelisConnector
from RETIREMENT_PENIBILITY_ENGINE.nibelis_contract import NIBELIS_SAFETY_CONTRACT
from RETIREMENT_PENIBILITY_ENGINE.nibelis_models import (
    NibelisEmployer,
    NibelisPayrollPeriod,
    NibelisReportView,
    NibelisSalaryItem,
)
from RETIREMENT_PENIBILITY_ENGINE.payslip_connector import PayslipConnector
from RETIREMENT_PENIBILITY_ENGINE.payslip_contract import PAYSLIP_SAFETY_CONTRACT
from RETIREMENT_PENIBILITY_ENGINE.payslip_models import PayslipEmployer, PayslipReportView


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "RETIREMENT_PENIBILITY_ENGINE"
CONNECTOR_MODULES = (
    "career_statement_connector",
    "payslip_connector",
    "employment_contract_connector",
    "kelio_connector",
    "nibelis_connector",
)


@dataclass(frozen=True)
class ConnectorCase:
    name: str
    connector: object
    source: object
    validate_method: str
    report_view: object
    historical_methods: tuple[str, ...]
    safety_contract: object


def _cases() -> tuple[ConnectorCase, ...]:
    statement_connector = CareerStatementConnector()
    statement = statement_connector.create_empty_statement("statement-empty")

    payslip_connector = PayslipConnector()
    payslip = replace(
        payslip_connector.create_empty_payslip("payslip-empty"),
        employer=PayslipEmployer(
            "employer-payslip", "Employeur synthétique", "source-payslip"
        ),
    )

    employment_connector = EmploymentContractConnector()
    employment = replace(
        employment_connector.create_empty_contract("contract-empty"),
        employer=EmploymentEmployer(
            "employer-contract", "Employeur synthétique", "source-contract"
        ),
    )

    kelio_connector = KelioConnector()
    kelio = kelio_connector.create_empty_export("kelio-empty")

    nibelis_connector = NibelisConnector()
    nibelis = replace(
        nibelis_connector.create_empty_export("nibelis-empty"),
        employer=NibelisEmployer(
            "employer-nibelis", "Employeur synthétique", "source-nibelis"
        ),
    )

    return (
        ConnectorCase(
            "career_statement",
            statement_connector,
            statement,
            "validate_statement",
            CareerStatementReportView.EMPLOYEE_VIEW,
            (
                "create_empty_statement",
                "validate_statement",
                "convert_to_import_batch",
                "generate_import_report",
                "extract_metadata",
                "prepare_reconstruction",
            ),
            CAREER_STATEMENT_SAFETY_CONTRACT,
        ),
        ConnectorCase(
            "payslip",
            payslip_connector,
            payslip,
            "validate_payslip",
            PayslipReportView.EMPLOYEE_VIEW,
            (
                "create_empty_payslip",
                "validate_payslip",
                "convert_to_import_batch",
                "extract_payroll_information",
                "prepare_reconstruction",
                "generate_import_report",
            ),
            PAYSLIP_SAFETY_CONTRACT,
        ),
        ConnectorCase(
            "employment_contract",
            employment_connector,
            employment,
            "validate_contract",
            EmploymentReportView.EMPLOYEE_VIEW,
            (
                "create_empty_contract",
                "validate_contract",
                "convert_to_import_batch",
                "extract_contract_information",
                "prepare_reconstruction",
                "generate_import_report",
            ),
            EMPLOYMENT_CONTRACT_SAFETY_CONTRACT,
        ),
        ConnectorCase(
            "kelio",
            kelio_connector,
            kelio,
            "validate_export",
            KelioReportView.EMPLOYEE_VIEW,
            (
                "create_empty_export",
                "validate_export",
                "convert_to_import_batch",
                "extract_working_time",
                "prepare_reconstruction",
                "generate_import_report",
            ),
            KELIO_SAFETY_CONTRACT,
        ),
        ConnectorCase(
            "nibelis",
            nibelis_connector,
            nibelis,
            "validate_export",
            NibelisReportView.EMPLOYEE_VIEW,
            (
                "create_empty_export",
                "validate_export",
                "extract_payroll_data",
                "convert_to_import_batch",
                "prepare_reconstruction",
                "generate_import_report",
            ),
            NIBELIS_SAFETY_CONTRACT,
        ),
    )


def test_foundation_import_is_independent_of_concrete_connectors():
    script = (
        "import importlib,sys; import RETIREMENT_PENIBILITY_ENGINE; "
        "before=set(sys.modules); "
        "importlib.import_module('RETIREMENT_PENIBILITY_ENGINE.connector_contract'); "
        "importlib.import_module('RETIREMENT_PENIBILITY_ENGINE.connector_base'); "
        f"forbidden={CONNECTOR_MODULES!r}; "
        "loaded=sorted(name for name in sys.modules if name not in before "
        "and name.rsplit('.',1)[-1] in forbidden); assert not loaded, loaded"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_foundation_has_no_concrete_connector_or_io_dependency():
    forbidden_modules = {
        *CONNECTOR_MODULES,
        "requests",
        "httpx",
        "urllib",
        "ssl",
        "socket",
        "subprocess",
    }
    violations = []
    for path in (PACKAGE / "connector_contract.py", PACKAGE / "connector_base.py"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module.rsplit(".", 1)[-1]
                if module in forbidden_modules:
                    violations.append((path.name, node.lineno, module))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in forbidden_modules:
                        violations.append((path.name, node.lineno, alias.name))
    assert violations == []


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case.name)
def test_connectors_keep_common_and_historical_public_methods(case: ConnectorCase):
    assert isinstance(case.connector, RetirementSourceConnector)
    assert all(callable(getattr(case.connector, name, None)) for name in case.historical_methods)


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case.name)
def test_empty_sources_validate_convert_reconstruct_and_report(case: ConnectorCase):
    validation = getattr(case.connector, case.validate_method)(case.source)
    assert validation.valid is True
    batch = case.connector.convert_to_import_batch(case.source)
    assert isinstance(batch, ImportBatch)
    prepared = case.connector.prepare_reconstruction(case.source)
    assert prepared.reconstruction_proposal is not None
    report = case.connector.generate_import_report(case.source, case.report_view)
    assert report.view is case.report_view


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case.name)
def test_provenance_and_synthetic_metadata_remain_mandatory(case: ConnectorCase):
    without_provenance = replace(
        case.source,
        metadata=replace(case.source.metadata, source_reference=""),
    )
    real_data = replace(
        case.source,
        metadata=replace(case.source.metadata, synthetic_only=False),
    )
    assert getattr(case.connector, case.validate_method)(without_provenance).valid is False
    assert getattr(case.connector, case.validate_method)(real_data).valid is False


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case.name)
def test_safety_contracts_still_disable_acquisition_capabilities(case: ConnectorCase):
    prohibited = (
        "network_allowed",
        "api_allowed",
        "ocr_allowed",
        "file_reading_allowed",
        "real_documents_allowed",
        "real_payslips_allowed",
        "real_exports_allowed",
    )
    assert all(
        getattr(case.safety_contract, name) is False
        for name in prohibited
        if hasattr(case.safety_contract, name)
    )


def test_nibelis_remains_fail_closed_without_referential_lookup():
    connector = NibelisConnector()
    source = replace(
        connector.create_empty_export("nibelis-fail-closed"),
        employer=NibelisEmployer("employer", None, "source-employer"),
        periods=(NibelisPayrollPeriod("period", "employer", "2026-01-01", "2026-01-31"),),
        salary_items=(
            NibelisSalaryItem(
                "salary-item",
                "period",
                "RUBRIC-REFERENCE",
                "1.00",
                None,
                None,
                None,
            ),
        ),
    )
    validation = connector.validate_export(source)
    assert validation.valid is False
    assert "REFERENTIAL_LOOKUP_REQUIRED" in {
        issue.issue_type for issue in validation.issues
    }


def test_kelio_anonymization_remains_mandatory():
    connector = KelioConnector()
    source = connector.create_empty_export("kelio-anonymization")
    source = replace(source, employee=replace(source.employee, anonymized=False))
    validation = connector.validate_export(source)
    assert validation.valid is False
    assert "IDENTITY_PROHIBITED" in {issue.issue_type for issue in validation.issues}
