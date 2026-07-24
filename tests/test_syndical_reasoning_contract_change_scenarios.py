from __future__ import annotations

import json
import re

from SYNDICAL_REASONING_ENGINE import (
    ChangeDimension,
    ContractChangeReasoningEngine,
    contract_change_scenarios,
)


def results():
    engine = ContractChangeReasoningEngine()
    return {
        code: engine.analyze(case, scenario_code=code)
        for code, case in contract_change_scenarios().items()
    }


def test_all_five_required_scenarios_exist():
    assert tuple(contract_change_scenarios()) == (
        "day_to_shift",
        "position_removal",
        "major_hours_change",
        "internal_transfer",
        "collective_reorganization",
    )


def test_each_scenario_has_a_distinct_reasoning_profile():
    analyzed = results()
    assert ChangeDimension.DAY_TO_SHIFT in analyzed["day_to_shift"].detected_dimensions
    assert ChangeDimension.POSITION_REMOVAL in analyzed["position_removal"].detected_dimensions
    assert ChangeDimension.WORKING_HOURS in analyzed["major_hours_change"].detected_dimensions
    assert ChangeDimension.POSITION in analyzed["internal_transfer"].detected_dimensions
    assert ChangeDimension.REORGANIZATION in analyzed["collective_reorganization"].detected_dimensions
    profiles = {
        tuple(item.value for item in result.detected_dimensions)
        for result in analyzed.values()
    }
    assert len(profiles) == 5


def test_collective_reorganization_asks_about_cse_and_other_employees():
    questions = " ".join(
        item.question for item in results()["collective_reorganization"].automatic_questions
    )
    assert "D'autres salariés" in questions
    assert "CSE" in questions


def test_internal_transfer_includes_position_and_classification_evidence():
    result = results()["internal_transfer"]
    assert ChangeDimension.POSITION in result.detected_dimensions
    assert {item.document_type for item in result.evidence} >= {
        "employment_contract",
        "job_description",
        "collective_agreement",
    }


def test_scenarios_never_decide_legality():
    rendered = json.dumps(
        {code: result.to_dict() for code, result in results().items()},
        ensure_ascii=False,
    ).lower()
    assert "la décision est légale" not in rendered
    assert "la décision est illégale" not in rendered
    assert re.search(r"\b(?:nir|iban|rib)\b", rendered) is None
    for forbidden in ("c:\\", "/users/", "/home/", "chunk_", "storage_id"):
        assert forbidden not in rendered
