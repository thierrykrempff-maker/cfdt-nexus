from __future__ import annotations

import importlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from automation.experts import paie
from automation.payroll import payroll_referential_integration


ROOT = Path(__file__).resolve().parents[1]


def _isolated_import(module: str, forbidden: tuple[str, ...]) -> list[str]:
    script = (
        "import importlib,json,sys;"
        f"importlib.import_module({module!r});"
        f"forbidden={forbidden!r};"
        "print(json.dumps(sorted(name for name in sys.modules if name.startswith(forbidden))))"
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-c", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_payroll_adapter_import_remains_architecture_isolated() -> None:
    assert _isolated_import(
        "automation.adapters.payroll",
        ("automation.connector_platform", "automation.cse_memory", "automation.protection_sociale"),
    ) == []


def test_contract_import_remains_domain_independent() -> None:
    assert _isolated_import(
        "automation.contracts",
        ("automation.experts", "automation.payroll", "automation.connector_platform"),
    ) == []


def test_referential_failure_preserves_historical_payroll_payload() -> None:
    original = payroll_referential_integration.load_safe_catalogs

    def fail() -> dict[str, dict[str, Any]]:
        raise ValueError("SYNTHETIC_CATALOG_FAILURE")

    payroll_referential_integration.load_safe_catalogs = fail
    try:
        payload = paie.enrich(
            {
                "query": "Mes heures supplémentaires ne sont pas payées.",
                "route": {"domains": ["paie_remuneration"]},
                "sources": [{"document": "Source synthétique"}],
                "payroll_rule_context": {
                    "documents": ["bulletin synthétique"],
                    "variables": {"overtime_hours": 2},
                },
            }
        )
    finally:
        payroll_referential_integration.load_safe_catalogs = original
    assert payload["active"] is True
    assert payload["payroll_rule_analysis"]
    assert payload["payroll_referential_analysis"]["available"] is False
    assert payload["elements_du_bulletin_concernes"]
    assert "traceback" not in repr(payload).casefold()
