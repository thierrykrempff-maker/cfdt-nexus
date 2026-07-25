from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from NEXUS_RUNTIME_INTEGRATION.config import (
    RuntimeExpertPaieV2Config,
    RuntimeFinalAssistantConfig,
)
from tools.run_nexus_controlled_validation import flag_matrix, load_cases, run_campaign


ROOT = Path(__file__).resolve().parents[1]


def test_production_defaults_remain_disabled() -> None:
    assert RuntimeFinalAssistantConfig.from_env({}).enabled is False
    assert RuntimeExpertPaieV2Config.from_env({}).enabled is False


def test_all_four_flag_configurations_are_explicit() -> None:
    rows = flag_matrix()
    assert [row["configuration"] for row in rows] == ["A", "B", "C", "D"]
    assert rows[0]["response"] == "historical_runtime"
    assert rows[1]["expert_paie_v2_loaded"] is False
    assert rows[2]["expert_paie_v2_loaded"] is True
    assert rows[3]["final_assistant_loaded"] is False
    assert all(row["contamination"] is False for row in rows)


def test_importing_runtime_does_not_eagerly_load_optional_engines() -> None:
    script = (
        "import json,sys;import NEXUS_RUNTIME_INTEGRATION;"
        "print(json.dumps({'final': 'NEXUS_FINAL_ASSISTANT' in sys.modules,"
        "'payroll': 'EXPERT_PAIE_V2' in sys.modules}))"
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-c", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout) == {"final": False, "payroll": False}


def test_disabled_final_assistant_keeps_historical_mode() -> None:
    campaign = run_campaign(load_cases()[:1], final_enabled=False)
    assert campaign["historical_runtime_cases"] == 1
    assert campaign["results"][0]["mode"] == "HISTORICAL"


def test_final_without_payroll_does_not_call_payroll_engine() -> None:
    payroll_case = next(case for case in load_cases() if case["category"] == "PAYROLL")
    from tools.run_nexus_controlled_validation import execute_case

    result = execute_case(payroll_case, final_enabled=True, payroll_enabled=False)
    assert "expert_paie_v2" not in result["engines_called"]
