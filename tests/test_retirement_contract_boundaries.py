"""Deterministic checks for implementation-independent retirement contracts."""

from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "RETIREMENT_PENIBILITY_ENGINE"
CONTRACT_FILES = tuple(sorted(PACKAGE.glob("*_contract.py")))
FORBIDDEN_SUFFIXES = (
    "_connector",
    "_engine",
    "_validator",
    "_converter",
    "_report",
    "_policy",
)

IMPLEMENTATIONS = (
    ("retirement_contract", "RetirementAssessmentPort", "retirement_platform", "RetirementPlatform"),
    ("career_timeline_contract", "CareerTimelinePort", "career_timeline_engine", "CareerTimelineEngine"),
    ("career_evidence_contract", "CareerEvidencePort", "career_evidence_engine", "CareerEvidenceEngine"),
    ("document_knowledge_contract", "DocumentKnowledgePort", "document_knowledge_engine", "DocumentKnowledgeEngine"),
    ("rule_reasoning_contract", "RetirementRuleReasoningPort", "rule_reasoning_engine", "RetirementRuleReasoningEngine"),
    ("potential_rights_contract", "PotentialRightsPort", "potential_rights_engine", "PotentialRightsEngine"),
    ("career_import_contract", "CareerImportPort", "career_import_engine", "CareerImportEngine"),
    ("career_reconstruction_contract", "CareerReconstructionPort", "career_reconstruction_engine", "CareerReconstructionEngine"),
    ("career_statement_contract", "CareerStatementPort", "career_statement_connector", "CareerStatementConnector"),
    ("payslip_contract", "PayslipPort", "payslip_connector", "PayslipConnector"),
    ("employment_contract_contract", "EmploymentContractPort", "employment_contract_connector", "EmploymentContractConnector"),
    ("kelio_contract", "KelioPort", "kelio_connector", "KelioConnector"),
    ("nibelis_contract", "NibelisPort", "nibelis_connector", "NibelisConnector"),
)


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))


def _relative_dependencies(path: Path) -> set[str]:
    dependencies: set[str] = set()
    for node in ast.walk(_tree(path)):
        if not isinstance(node, ast.ImportFrom) or node.level != 1:
            continue
        if node.module:
            dependencies.add(node.module.split(".", 1)[0])
        else:
            dependencies.update(alias.name.split(".", 1)[0] for alias in node.names)
    return dependencies


def test_all_contract_modules_are_in_scope():
    assert len(CONTRACT_FILES) == 16


@pytest.mark.parametrize("path", CONTRACT_FILES, ids=lambda path: path.stem)
def test_contract_imports_only_neutral_modules(path: Path):
    violations = []
    for node in ast.walk(_tree(path)):
        modules = []
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        for module in modules:
            leaf = module.rsplit(".", 1)[-1]
            if leaf.endswith(FORBIDDEN_SUFFIXES):
                violations.append((node.lineno, module))
    assert violations == []


@pytest.mark.parametrize("path", CONTRACT_FILES, ids=lambda path: path.stem)
def test_contract_defines_no_concrete_facade(path: Path):
    forbidden_class_suffixes = (
        "Connector",
        "Engine",
        "Validator",
        "Converter",
        "ReportBuilder",
    )
    classes = [
        node.name
        for node in _tree(path).body
        if isinstance(node, ast.ClassDef)
        and node.name.endswith(forbidden_class_suffixes)
        and not any(ast.unparse(base).startswith("Protocol") for base in node.bases)
    ]
    assert classes == []


@pytest.mark.parametrize("path", CONTRACT_FILES, ids=lambda path: path.stem)
def test_contract_import_is_independent(path: Path):
    module_name = f"RETIREMENT_PENIBILITY_ENGINE.{path.stem}"
    script = (
        "import importlib,sys; import RETIREMENT_PENIBILITY_ENGINE; "
        "before=set(sys.modules); "
        f"importlib.import_module({module_name!r}); "
        "prefix='RETIREMENT_PENIBILITY_ENGINE.'; "
        f"suffixes={FORBIDDEN_SUFFIXES!r}; "
        "loaded=sorted(name for name in sys.modules "
        "if name not in before and name.startswith(prefix) "
        "and name.rsplit('.',1)[-1].endswith(suffixes)); "
        "assert not loaded, loaded"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_retirement_package_has_no_import_cycle():
    modules = {path.stem for path in PACKAGE.glob("*.py")}
    graph = {
        path.stem: _relative_dependencies(path) & modules
        for path in PACKAGE.glob("*.py")
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(module: str, trail: tuple[str, ...] = ()) -> None:
        if module in visiting:
            raise AssertionError(" -> ".join(trail + (module,)))
        if module in visited:
            return
        visiting.add(module)
        for dependency in sorted(graph[module]):
            visit(dependency, trail + (module,))
        visiting.remove(module)
        visited.add(module)

    for module in sorted(graph):
        visit(module)


@pytest.mark.parametrize(
    "contract_name,port_name,implementation_name,implementation_class",
    IMPLEMENTATIONS,
)
def test_protocol_is_implemented_structurally(
    contract_name: str,
    port_name: str,
    implementation_name: str,
    implementation_class: str,
):
    contract = importlib.import_module(f"RETIREMENT_PENIBILITY_ENGINE.{contract_name}")
    implementation = importlib.import_module(
        f"RETIREMENT_PENIBILITY_ENGINE.{implementation_name}"
    )
    port = getattr(contract, port_name)
    concrete = getattr(implementation, implementation_class)
    methods = {
        name
        for name, member in vars(port).items()
        if inspect.isfunction(member) and not name.startswith("_")
    }
    assert methods
    assert all(callable(getattr(concrete, name, None)) for name in methods)


@pytest.mark.parametrize("path", CONTRACT_FILES, ids=lambda path: path.stem)
def test_protocol_annotations_resolve_without_concrete_imports(path: Path):
    module_name = f"RETIREMENT_PENIBILITY_ENGINE.{path.stem}"
    script = (
        "import importlib,inspect,sys,typing; import RETIREMENT_PENIBILITY_ENGINE; "
        "before=set(sys.modules); "
        f"module=importlib.import_module({module_name!r}); "
        "protocols=[item for _,item in inspect.getmembers(module,inspect.isclass) "
        "if item.__module__==module.__name__ and getattr(item,'_is_protocol',False)]; "
        "[typing.get_type_hints(method,globalns=vars(module)) "
        "for protocol in protocols for name,method in vars(protocol).items() "
        "if inspect.isfunction(method) and not name.startswith('_')]; "
        "prefix='RETIREMENT_PENIBILITY_ENGINE.'; "
        f"suffixes={FORBIDDEN_SUFFIXES!r}; "
        "loaded=sorted(name for name in sys.modules "
        "if name not in before and name.startswith(prefix) "
        "and name.rsplit('.',1)[-1].endswith(suffixes)); "
        "assert not loaded, loaded"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
