from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

from NEXUS_RUNTIME_INTEGRATION import get_nexus_version
from NEXUS_RUNTIME_INTEGRATION.config import (
    RuntimeCSEMemoryConfig,
    RuntimeConnectorConfig,
    RuntimeExpertPaieV2Config,
    RuntimeFinalAssistantConfig,
    RuntimeIntegrationConfig,
    RuntimeOfficialConnectorsConfig,
    RuntimeProtectionSocialeConfig,
    RuntimeRetirementConfig,
    RuntimeSyndicalReasoningConfig,
)


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "nexus-local-interface"


def _server_module():
    path = APP / "server.py"
    sys.path.insert(0, str(APP))
    spec = importlib.util.spec_from_file_location("nexus_release_server", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_version_100_has_one_repository_source() -> None:
    assert get_nexus_version() == "1.0.0"
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "1.0.0"
    module = (APP / "module.json").read_text(encoding="utf-8")
    assert '"version_file": "../../VERSION"' in module
    assert '"version": "2.1.0"' not in module


def test_all_advanced_feature_flags_remain_disabled_by_default() -> None:
    configs = (
        RuntimeIntegrationConfig.from_env({}),
        RuntimeConnectorConfig.from_env({}),
        RuntimeCSEMemoryConfig.from_env({}),
        RuntimeRetirementConfig.from_env({}),
        RuntimeProtectionSocialeConfig.from_env({}),
        RuntimeOfficialConnectorsConfig.from_env({}),
        RuntimeSyndicalReasoningConfig.from_env({}),
        RuntimeExpertPaieV2Config.from_env({}),
        RuntimeFinalAssistantConfig.from_env({}),
    )
    assert all(config.enabled is False for config in configs)


def test_optional_dependencies_are_reported_without_being_imported() -> None:
    status = _server_module().optional_dependency_status()
    assert set(status) == {"pdf_test_fixture", "pptx_import", "xlsx_import"}
    assert {item["package"] for item in status.values()} == {
        "reportlab",
        "python-pptx",
        "openpyxl",
    }
    assert all(isinstance(item["available"], bool) for item in status.values())


def test_router_subprocess_receives_repository_root_without_external_bootstrap() -> None:
    environment = _server_module().router_environment()
    assert environment["PYTHONPATH"].split(os.pathsep)[0] == str(ROOT)


def test_launcher_supports_degraded_mode_and_clean_shutdown() -> None:
    launcher = (APP / "start-nexus-local.bat").read_text(encoding="utf-8")
    stopper = (APP / "stop-nexus-local.bat").read_text(encoding="utf-8")
    assert "Nexus demarrera en mode degrade" in launcher
    missing_block = launcher.split('if not exist "%NEXUS_LOCAL_CONFIG%" (', 1)[1].split(
        ") else (", 1
    )[0]
    assert "exit /b 1" not in missing_block
    assert "CFDT_NEXUS_PYTHON" in launcher
    assert "Python est indisponible" in launcher
    assert "/health" in stopper
    assert "nexus-local-interface" in stopper
    assert "Stop-Process" in stopper


def test_interface_exposes_version_print_and_optional_capabilities() -> None:
    html = (APP / "index.html").read_text(encoding="utf-8")
    script = (APP / "app.js").read_text(encoding="utf-8")
    styles = (APP / "styles.css").read_text(encoding="utf-8")
    assert 'id="nexusVersionValue"' in html
    assert 'id="printReportButton"' in html
    assert 'fetchJson("/health")' in script
    assert "window.print()" in script
    assert "Version CFDT Nexus" in script
    assert "body * { visibility: hidden !important; }" in styles
    assert ".report-details" in styles


def test_release_documentation_and_dependency_manifests_exist() -> None:
    expected = (
        "README.md",
        "V1_USER_GUIDE.md",
        "V1_TECHNICAL_GUIDE.md",
        "V1_KNOWN_LIMITATIONS.md",
        "V1_RELEASE_AUDIT.md",
        "V1_PRIVACY_AND_CONFIDENTIALITY_REPORT.md",
        "V1_RELEASE_READINESS_REPORT.md",
        "CHANGELOG.md",
        "requirements.txt",
        "requirements-optional.txt",
    )
    assert all((ROOT / name).is_file() for name in expected)
