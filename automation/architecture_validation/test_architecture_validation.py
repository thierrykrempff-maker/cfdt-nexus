"""Tests for the final deterministic architecture freeze validator."""

from __future__ import annotations

import json
from pathlib import Path

from automation.architecture_validation import ArchitectureValidator, validate_architecture


PACKAGES = (
    "automation/contracts",
    "automation/adapters",
    "automation/expert_facades",
    "automation/orchestrator_common",
    "automation/experts",
)


def make_repository(tmp_path: Path) -> Path:
    (tmp_path / "automation").mkdir()
    (tmp_path / "automation" / "__init__.py").write_text("", encoding="utf-8")
    for relative in PACKAGES:
        directory = tmp_path / relative
        directory.mkdir(parents=True)
        (directory / "__init__.py").write_text("", encoding="utf-8")
    return tmp_path


def write(root: Path, relative: str, source: str) -> None:
    (root / relative).write_text(source, encoding="utf-8")


def codes(report) -> tuple[str, ...]:
    return tuple(item.code for item in report.violations)


def test_real_repository_architecture_is_valid():
    report = validate_architecture()
    assert report.architecture_valid is True
    assert report.modules_present == ("ARCH-01", "ARCH-02", "ARCH-03", "ARCH-04")
    assert report.violations == ()


def test_report_is_deterministic_and_json_serializable(tmp_path):
    root = make_repository(tmp_path)
    first = ArchitectureValidator(root).validate().to_dict()
    second = ArchitectureValidator(root).validate().to_dict()
    assert first == second
    assert json.loads(json.dumps(first, sort_keys=True)) == first


def test_missing_module_is_reported(tmp_path):
    root = make_repository(tmp_path)
    (root / "automation" / "orchestrator_common" / "__init__.py").unlink()
    report = validate_architecture(root)
    assert report.architecture_valid is False
    assert report.missing_modules == ("ARCH-04",)
    assert "MISSING_ARCH_MODULE" in codes(report)


def test_arch01_cannot_depend_on_later_layer(tmp_path):
    root = make_repository(tmp_path)
    write(root, "automation/contracts/bad.py", "from automation.adapters import payroll\n")
    report = validate_architecture(root)
    assert "FORBIDDEN_ARCH_DEPENDENCY" in codes(report)
    assert report.dependencies_conform is False


def test_arch02_may_depend_only_on_arch01(tmp_path):
    root = make_repository(tmp_path)
    write(root, "automation/adapters/good.py", "from automation.contracts import requests\n")
    assert validate_architecture(root).architecture_valid is True
    write(root, "automation/adapters/bad.py", "from automation.expert_facades import base\n")
    assert "FORBIDDEN_ARCH_DEPENDENCY" in codes(validate_architecture(root))


def test_arch03_may_depend_on_arch01_and_arch02(tmp_path):
    root = make_repository(tmp_path)
    write(root, "automation/expert_facades/good.py", "from automation.contracts import reports\nfrom automation.adapters import payroll\n")
    assert validate_architecture(root).architecture_valid is True
    write(root, "automation/expert_facades/bad.py", "from automation.orchestrator_common import models\n")
    assert "FORBIDDEN_ARCH_DEPENDENCY" in codes(validate_architecture(root))


def test_arch04_may_depend_on_arch01_and_arch03_but_not_arch02(tmp_path):
    root = make_repository(tmp_path)
    write(root, "automation/orchestrator_common/good.py", "from automation.contracts import reports\nfrom automation.expert_facades import base\n")
    assert validate_architecture(root).architecture_valid is True
    write(root, "automation/orchestrator_common/bad.py", "from automation.adapters import payroll\n")
    assert "FORBIDDEN_ARCH_DEPENDENCY" in codes(validate_architecture(root))


def test_historical_expert_reverse_dependency_is_forbidden(tmp_path):
    root = make_repository(tmp_path)
    write(root, "automation/experts/legacy.py", "from automation.contracts import ExpertRequest\n")
    report = validate_architecture(root)
    assert "HISTORICAL_REVERSE_DEPENDENCY" in codes(report)
    assert report.dependencies_conform is False


def test_network_import_and_call_are_forbidden(tmp_path):
    root = make_repository(tmp_path)
    write(root, "automation/contracts/network.py", "import requests\nrequests.get('synthetic')\n")
    report = validate_architecture(root)
    assert "NETWORK_DEPENDENCY" in codes(report)
    assert "NETWORK_CALL" in codes(report)
    assert report.boundaries_conform is False


def test_connector_and_endpoint_dependencies_are_forbidden(tmp_path):
    root = make_repository(tmp_path)
    write(root, "automation/adapters/bad.py", "import automation.connector_platform\nimport apps.api\n")
    report = validate_architecture(root)
    assert codes(report).count("FORBIDDEN_BOUNDARY_DEPENDENCY") == 2


def test_circular_import_is_reported_deterministically(tmp_path):
    root = make_repository(tmp_path)
    write(root, "automation/contracts/a.py", "from automation.contracts.b import value\n")
    write(root, "automation/contracts/b.py", "from automation.contracts.a import value\n")
    first = validate_architecture(root)
    second = validate_architecture(root)
    assert "CIRCULAR_IMPORT" in codes(first)
    assert first.violations == second.violations


def test_test_modules_do_not_change_production_validation(tmp_path):
    root = make_repository(tmp_path)
    write(root, "automation/contracts/test_fixture.py", "import requests\n")
    assert validate_architecture(root).architecture_valid is True
