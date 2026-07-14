#!/usr/bin/env python
"""Tests for LOT 4F payroll privacy validation.

The values are constructed synthetic examples. Sensitive-looking strings are
assembled at runtime so the source file itself does not become a privacy hit.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from automation.payroll import payroll_data_privacy_validator as privacy  # noqa: E402
from automation.payroll import payroll_referential_validator as referential_validator  # noqa: E402


def sensitive_email() -> str:
    return "personne.alpha" + "@" + "entreprise.invalid"


def sensitive_phone() -> str:
    return "06 " + "12 34 " + "56 78"


def sensitive_iban() -> str:
    return "FR76 " + "3000 6000 " + "0112 3456 " + "7890 189"


def sensitive_nir() -> str:
    return "1 84 " + "12 57 " + "123 456 " + "78"


def sensitive_secret() -> str:
    return "api_key=" + "sk-test-" + "A" * 18


def assert_blocked(report: dict[str, Any], category: str) -> None:
    assert report["status"] == privacy.STATUS_BLOCKED, report
    assert any(item["category"] == category for item in report["findings"]), report


def assert_no_full_value(report: dict[str, Any], value: str) -> None:
    serialized = json.dumps(report, ensure_ascii=False)
    assert value not in serialized, serialized


def test_detects_and_masks_email() -> None:
    value = sensitive_email()
    report = privacy.scan_text(f"Contact {value}", path="$.notes")
    assert_blocked(report, "email")
    assert_no_full_value(report, value)


def test_detects_and_masks_phone() -> None:
    value = sensitive_phone()
    report = privacy.scan_text(f"Telephone {value}", path="$.notes")
    assert_blocked(report, "phone_number")
    assert_no_full_value(report, value)


def test_detects_and_masks_iban() -> None:
    value = sensitive_iban()
    report = privacy.scan_text(f"IBAN {value}", path="$.notes")
    assert_blocked(report, "iban")
    assert_no_full_value(report, value)


def test_detects_and_masks_nir() -> None:
    value = sensitive_nir()
    report = privacy.scan_text(f"NIR {value}", path="$.notes")
    assert_blocked(report, "french_social_security_number")
    assert_no_full_value(report, value)


def test_detects_matricule_in_structured_field() -> None:
    value = "MAT-" + "12345"
    report = privacy.scan_object({"matricule": value})
    assert_blocked(report, "employee_identifier")
    assert_no_full_value(report, value)


def test_detects_birth_date_in_nominative_context() -> None:
    value = "1984" + "-12-01"
    report = privacy.scan_object({"employee_name": "Personne Alpha", "date_naissance": value})
    assert_blocked(report, "birth_date")
    assert_no_full_value(report, value)


def test_detects_medical_nominative_information() -> None:
    value = "diagnostic test a retirer"
    report = privacy.scan_object({"employee_name": "Personne Alpha", "diagnostic": value})
    assert_blocked(report, "medical_or_work_stoppage_data")
    assert_no_full_value(report, value)


def test_detects_secret_or_api_key() -> None:
    value = sensitive_secret()
    report = privacy.scan_text(value, path="$.secret")
    assert_blocked(report, "technical_secret")
    assert_no_full_value(report, value)


def test_detects_risky_filename() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "bulletin_salarie.pdf"
        path.write_bytes(b"")
        report = privacy.check_file_policy(path)
    assert_blocked(report, "payslip_file")


def test_allows_reserved_example_domain() -> None:
    report = privacy.scan_text("Contact personne.alpha@example.com", path="$.notes")
    assert report["status"] == privacy.STATUS_OK, report


def test_allows_explicit_invalid_synthetic_iban() -> None:
    text = "EXEMPLE_SYNTHETIQUE IBAN invalide " + sensitive_iban()
    report = privacy.scan_text(text, path="$.notes")
    assert report["status"] == privacy.STATUS_OK, report


def test_rejects_false_positive_business_codes() -> None:
    report = privacy.scan_text("Le compteur CP_SYN alimente une verification synthetique.")
    assert report["status"] == privacy.STATUS_OK, report


def test_scans_json_file() -> None:
    value = sensitive_email()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "fixture.json"
        path.write_text(json.dumps({"contact": value}), encoding="utf-8")
        report = privacy.scan_file(path)
    assert_blocked(report, "email")
    assert_no_full_value(report, value)


def test_scans_directory() -> None:
    value = sensitive_phone()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "nested"
        path.mkdir()
        (path / "fixture.txt").write_text(f"Numero {value}", encoding="utf-8")
        report = privacy.scan_directory(tmp)
    assert_blocked(report, "phone_number")
    assert_no_full_value(report, value)


def test_precommit_script_returns_non_zero_on_forbidden_data() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "fixture.json"
        path.write_text(json.dumps({"contact": sensitive_email()}), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(ROOT / "automation" / "payroll" / "check_payroll_privacy_before_commit.py"), "--path", str(path), "--json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    assert result.returncode == 1, result.stdout + result.stderr
    assert sensitive_email() not in result.stdout


def test_precommit_script_returns_zero_on_allowed_example() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "fixture.json"
        path.write_text(json.dumps({"contact": "personne.alpha@example.com"}), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(ROOT / "automation" / "payroll" / "check_payroll_privacy_before_commit.py"), "--path", str(path), "--json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    assert result.returncode == 0, result.stdout + result.stderr


def test_referential_validator_uses_privacy_layer() -> None:
    catalog = referential_validator.load_catalog("kelio")
    catalog["counters"][0]["notes"] = ["Matricule: " + "MAT-" + "12345"]
    report = referential_validator.validate_catalog("kelio", catalog=catalog)
    assert not report["valid"], report
    assert any(item["code"] == "sensitive_data_detected" for item in report["errors"]), report


def test_current_referentials_have_no_blocking_privacy_findings() -> None:
    report = privacy.scan_directory(ROOT / "database" / "payroll" / "referentials")
    assert report["blocked_count"] == 0, report


def run_all() -> None:
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            func()
            print(f"OK {name}")


if __name__ == "__main__":
    run_all()
