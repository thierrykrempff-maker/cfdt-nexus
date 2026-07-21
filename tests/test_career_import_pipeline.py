"""Architecture tests for the mandatory Career Import pipeline."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from RETIREMENT_PENIBILITY_ENGINE.career_import_models import (
    ImportBatch,
    ImportConfidence,
    ImportDocumentType,
    ImportProvenance,
    ImportStatus,
    ImportedEmploymentPeriod,
)
from RETIREMENT_PENIBILITY_ENGINE.career_import_pipeline import (
    CAREER_IMPORT_PIPELINE_STAGES,
    CareerImportPipeline,
)
from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_engine import (
    CareerReconstructionEngine,
)
from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_models import (
    ReconstructionRequest,
)
from RETIREMENT_PENIBILITY_ENGINE.career_statement_connector import (
    CareerStatementConnector,
)
from RETIREMENT_PENIBILITY_ENGINE.employment_contract_connector import (
    EmploymentContractConnector,
)
from RETIREMENT_PENIBILITY_ENGINE.employment_contract_models import (
    EmploymentEmployer,
)
from RETIREMENT_PENIBILITY_ENGINE.kelio_connector import KelioConnector
from RETIREMENT_PENIBILITY_ENGINE.nibelis_connector import NibelisConnector
from RETIREMENT_PENIBILITY_ENGINE.nibelis_models import NibelisEmployer
from RETIREMENT_PENIBILITY_ENGINE.payslip_connector import PayslipConnector
from RETIREMENT_PENIBILITY_ENGINE.payslip_models import PayslipEmployer


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "RETIREMENT_PENIBILITY_ENGINE"
CONNECTOR_MODULES = (
    "career_statement_connector.py",
    "payslip_connector.py",
    "employment_contract_connector.py",
    "kelio_connector.py",
    "nibelis_connector.py",
)


def provenance(origin="synthetic:test"):
    return ImportProvenance(
        "source-1",
        ImportDocumentType.PAYSLIP,
        "document-1",
        "2026-07-21",
        "v1",
        origin,
        ImportConfidence.MEDIUM,
    )


def valid_batch():
    return ImportBatch(
        "batch-1",
        records=(
            ImportedEmploymentPeriod(
                "period-1",
                "Employeur synthétique",
                "2001-01-01",
                "2001-12-31",
                provenance(),
            ),
        ),
    )


def context(engine):
    return engine.create_reconstruction_context(
        "context-1", ReconstructionRequest("request-1", "Question synthétique")
    )


class PipelineSpy:
    def __init__(self):
        self.calls = []

    def create_reconstruction_context(self, context_id, request, *args):
        self.calls.append("CAREER_IMPORT")
        return (context_id, request)

    def add_import_batch(self, current, batch):
        assert type(batch) is ImportBatch
        self.calls.append("CAREER_RECONSTRUCTION")
        return current, batch

    def build_reconstruction_proposal(self, current):
        self.calls.append("TIMELINE_EVIDENCE_POTENTIAL_RIGHTS_READY")
        return current


def connector_cases(spy):
    statement_connector = CareerStatementConnector(import_pipeline=spy)
    statement = statement_connector.create_empty_statement("statement")

    payslip_connector = PayslipConnector(import_pipeline=spy)
    payslip = replace(
        payslip_connector.create_empty_payslip("payslip"),
        employer=PayslipEmployer("employer", "Employeur synthétique", "source"),
    )

    employment_connector = EmploymentContractConnector(import_pipeline=spy)
    employment = replace(
        employment_connector.create_empty_contract("contract"),
        employer=EmploymentEmployer("employer", "Employeur synthétique", "source"),
    )

    kelio_connector = KelioConnector(import_pipeline=spy)
    kelio = kelio_connector.create_empty_export("kelio")

    nibelis_connector = NibelisConnector(import_pipeline=spy)
    nibelis = replace(
        nibelis_connector.create_empty_export("nibelis"),
        employer=NibelisEmployer("employer", "Employeur synthétique", "source"),
    )
    return (
        (statement_connector, statement),
        (payslip_connector, payslip),
        (employment_connector, employment),
        (kelio_connector, kelio),
        (nibelis_connector, nibelis),
    )


def test_pipeline_order_is_explicit_and_complete():
    assert CAREER_IMPORT_PIPELINE_STAGES == (
        "CONNECTOR",
        "CAREER_IMPORT",
        "CAREER_RECONSTRUCTION",
        "TIMELINE",
        "EVIDENCE",
        "POTENTIAL_RIGHTS",
    )


def test_connectors_cannot_import_career_reconstruction_directly():
    violations = []
    for filename in CONNECTOR_MODULES:
        tree = ast.parse((PACKAGE / filename).read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "career_reconstruction" in node.module:
                    violations.append((filename, node.lineno, node.module))
    assert violations == []


@pytest.mark.parametrize("connector_index", range(5))
def test_each_connector_routes_reconstruction_through_career_import(connector_index):
    spy = PipelineSpy()
    connector, source = connector_cases(spy)[connector_index]
    prepared = connector.prepare_reconstruction(source)
    assert prepared.reconstruction_proposal is not None
    assert spy.calls == (
        ["CAREER_IMPORT", "CAREER_RECONSTRUCTION", "TIMELINE_EVIDENCE_POTENTIAL_RIGHTS_READY"]
    )


def test_pipeline_validates_and_marks_batch_before_reconstruction():
    pipeline = CareerImportPipeline()
    updated = pipeline.add_import_batch(context(pipeline), valid_batch())
    assert updated.import_batches[0].status is ImportStatus.VALIDATED


@pytest.mark.parametrize("invalid", [object(), (), [], {}])
def test_reconstruction_refuses_every_non_import_batch(invalid):
    engine = CareerReconstructionEngine()
    with pytest.raises(TypeError, match="ImportBatch only"):
        engine.add_import_batch(context(engine), invalid)


def test_reconstruction_refuses_batch_that_bypassed_career_import():
    engine = CareerReconstructionEngine()
    with pytest.raises(ValueError, match="validated by Career Import"):
        engine.add_import_batch(context(engine), valid_batch())


def test_pipeline_requires_provenance():
    invalid = replace(valid_batch(), records=(replace(valid_batch().records[0], provenance=provenance("")),))
    with pytest.raises(ValueError, match="requires provenance"):
        CareerImportPipeline().add_import_batch(context(CareerImportPipeline()), invalid)


def test_pipeline_rejects_real_documents():
    with pytest.raises(ValueError, match="synthetic metadata only"):
        CareerImportPipeline().validate_for_reconstruction(
            replace(valid_batch(), synthetic_only=False)
        )


def test_pipeline_rejects_structurally_invalid_batch():
    invalid = replace(
        valid_batch(),
        records=(replace(valid_batch().records[0], start_date="invalid"),),
    )
    with pytest.raises(ValueError, match="Career Import validation"):
        CareerImportPipeline().validate_for_reconstruction(invalid)


def test_pipeline_modules_have_no_io_or_network_imports():
    forbidden = {"requests", "httpx", "urllib", "ssl", "socket", "pathlib"}
    violations = []
    for filename in ("career_import_pipeline.py", "career_reconstruction_engine.py"):
        tree = ast.parse((PACKAGE / filename).read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                violations.extend(
                    (filename, node.lineno, alias.name)
                    for alias in node.names
                    if alias.name.split(".", 1)[0] in forbidden
                )
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".", 1)[0] in forbidden:
                    violations.append((filename, node.lineno, node.module))
    assert violations == []
