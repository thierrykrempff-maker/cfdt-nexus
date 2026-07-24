from __future__ import annotations

import inspect

from EXPERT_PAIE_V2 import ExpertPaieV2Engine, expert_paie_v2_scenarios
import EXPERT_PAIE_V2.calculation as calculation
import EXPERT_PAIE_V2.comparisons as comparisons
import EXPERT_PAIE_V2.engine as engine
import EXPERT_PAIE_V2.normalization as normalization
import EXPERT_PAIE_V2.rules as rules
import EXPERT_PAIE_V2.scenarios as scenarios
import EXPERT_PAIE_V2.validation as validation


def test_sources_have_no_network_import_or_real_document_loader():
    source = "\n".join(
        inspect.getsource(module)
        for module in (calculation, comparisons, engine, normalization, rules, scenarios, validation)
    ).lower()
    for forbidden in ("import requests", "import httpx", "import urllib", "import socket", "open(", "read_text(", "read_bytes("):
        assert forbidden not in source


def test_all_fixtures_are_synthetic_and_default_rules_do_not_calculate():
    payloads = expert_paie_v2_scenarios()
    assert all(payload.employee.synthetic for payload in payloads.values())
    assert all("synthetic" in payload.employee.employee_id.lower() for payload in payloads.values())
    forbidden_codes = {"to_verify_rule", "calculation_forbidden"}
    assert all(
        not any(rule.calculation_allowed for rule in payloads[code].rules)
        for code in forbidden_codes
    )


def test_public_results_never_expose_personal_or_bank_data():
    rendered = " ".join(
        str(ExpertPaieV2Engine().analyze(payload).to_dict()).lower()
        for payload in expert_paie_v2_scenarios().values()
    )
    for forbidden in ("nir réel", "iban", "rib bancaire", "matricule réel", "vrai bulletin", "vrai salaire", "nom du salarié"):
        assert forbidden not in rendered
