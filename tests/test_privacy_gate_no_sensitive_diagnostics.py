"""Privacy Gate diagnostics must never reproduce inspected keys or values."""

from __future__ import annotations

import re

import pytest

from RETIREMENT_PENIBILITY_ENGINE.privacy_gate import (
    PrivacyBlockedError,
    PrivacyInspectionError,
    RetirementPrivacyGate,
)
from RETIREMENT_PENIBILITY_ENGINE.privacy_models import (
    PrivacyCategory,
    PrivacyFinding,
    PrivacyInspection,
    PrivacySeverity,
    PrivacyStatus,
)


NIR_FIXTURE = "299129999999901"
IBAN_FIXTURE = "FR76 0000 0000 0000 0000 0000 001"
RIB_FIXTURE = "30004 00550 0000157841Z 25"
INTERNAL_ID_FIXTURE = "INTERNAL-987"
EMAIL_FIXTURE = "personne.fictive@example.test"
PHONE_FIXTURE = "06 00 00 00 00"
ADDRESS_FIXTURE = "12 rue de la Fiction"


def blocked_diagnostic(payload) -> tuple[str, PrivacyInspection]:
    gate = RetirementPrivacyGate()
    inspection = gate.inspect(payload)
    assert inspection.status in {PrivacyStatus.BLOCKED, PrivacyStatus.INSPECTION_ERROR}
    return gate.sanitize_diagnostic(inspection), inspection


@pytest.mark.parametrize(
    "payload, secret, category",
    [
        ({"reference": NIR_FIXTURE}, NIR_FIXTURE, PrivacyCategory.NIR),
        ({"reference": IBAN_FIXTURE}, IBAN_FIXTURE, PrivacyCategory.IBAN),
        ({"reference": RIB_FIXTURE}, RIB_FIXTURE, PrivacyCategory.RIB),
        ({"employee_id": INTERNAL_ID_FIXTURE}, INTERNAL_ID_FIXTURE, PrivacyCategory.INTERNAL_IDENTIFIER),
        ({"email": EMAIL_FIXTURE}, EMAIL_FIXTURE, PrivacyCategory.PERSONAL_EMAIL),
        ({"telephone": PHONE_FIXTURE}, PHONE_FIXTURE, PrivacyCategory.PERSONAL_PHONE),
        ({"postal_address": ADDRESS_FIXTURE}, ADDRESS_FIXTURE, PrivacyCategory.POSTAL_ADDRESS),
    ],
)
def test_sensitive_values_are_absent_from_diagnostics(payload, secret, category):
    diagnostic, inspection = blocked_diagnostic(payload)
    assert secret not in diagnostic
    assert secret not in repr(inspection)
    assert category.value in diagnostic


@pytest.mark.parametrize(
    "sensitive_key",
    [
        NIR_FIXTURE,
        IBAN_FIXTURE,
        RIB_FIXTURE,
        INTERNAL_ID_FIXTURE,
        EMAIL_FIXTURE,
        PHONE_FIXTURE,
        ADDRESS_FIXTURE,
        "employee_id",
        "matricule",
        "personal_email",
    ],
)
def test_mapping_keys_and_sensitive_variable_names_are_neutralized(sensitive_key):
    diagnostic, inspection = blocked_diagnostic({sensitive_key: object()})
    assert sensitive_key not in diagnostic
    assert sensitive_key not in repr(inspection)
    assert inspection.findings[0].field_path == "$.entry[0]"


def test_dataclass_field_name_is_not_exposed_in_diagnostic():
    finding = PrivacyFinding(
        PrivacyCategory.INTERNAL_IDENTIFIER,
        PrivacySeverity.CRITICAL,
        "$.employee_id",
        "PRIVACY_INTERNAL_ID_DETECTED",
        "Generic explanation.",
        "Reject input.",
    )
    diagnostic = RetirementPrivacyGate.sanitize_diagnostic(
        PrivacyInspection(PrivacyStatus.BLOCKED, (finding,))
    )
    assert "employee_id" not in diagnostic
    assert diagnostic == (
        "PRIVACY_INTERNAL_ID_DETECTED "
        "category=INTERNAL_IDENTIFIER severity=CRITICAL"
    )


def test_diagnostic_contains_only_stable_codes_categories_and_severity():
    diagnostic, _ = blocked_diagnostic(
        {"reference": f"{NIR_FIXTURE} {IBAN_FIXTURE} {EMAIL_FIXTURE}"}
    )
    assert re.fullmatch(
        r"PRIVACY_[A-Z_]+ category=[A-Z_]+ severity=[A-Z_]+"
        r"(?:; PRIVACY_[A-Z_]+ category=[A-Z_]+ severity=[A-Z_]+)*",
        diagnostic,
    )


def test_assert_safe_keeps_fail_closed_behavior_without_echoing_secret():
    gate = RetirementPrivacyGate()
    with pytest.raises(PrivacyBlockedError) as error:
        gate.assert_safe({"reference": NIR_FIXTURE})
    assert NIR_FIXTURE not in str(error.value)
    assert "PRIVACY_NIR_DETECTED" in str(error.value)

    with pytest.raises(PrivacyInspectionError) as inspection_error:
        gate.assert_safe({NIR_FIXTURE: object()})
    assert NIR_FIXTURE not in str(inspection_error.value)
    assert "PRIVACY_UNSUPPORTED_TYPE" in str(inspection_error.value)


def test_safe_and_warning_decisions_are_unchanged():
    gate = RetirementPrivacyGate()
    assert gate.inspect({"title": "Fixture synthétique"}).status is PrivacyStatus.SAFE
    assert gate.inspect({"personal_note": "Revue manuelle"}).status is PrivacyStatus.SAFE_WITH_WARNINGS
    assert gate.inspect({"reference": NIR_FIXTURE}).status is PrivacyStatus.BLOCKED
    assert gate.inspect(object()).status is PrivacyStatus.INSPECTION_ERROR
