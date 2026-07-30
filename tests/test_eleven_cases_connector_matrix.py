import json
from pathlib import Path

from SYNDICAL_REASONING_ENGINE import (
    RetrievalStatus, SourceExecutionCoordinator, build_case_factual_core,
    build_research_plan, default_metadata_executors,
)


ROOT = Path(__file__).resolve().parent / "fixtures" / "real_business_cases"
FILES = (
    ROOT / "insulting-emails-alcohol.json",
    ROOT / "smoking-breaks-seveso-badge.json",
    ROOT / "tag-on-installation.example.json",
    ROOT / "forced-day-to-shift-laboratory.json",
    ROOT / "delegation-hours-cssct-incomplete.json",
    ROOT / "annual-leave-ten-percent-rule-unresolved.json",
    ROOT / "second_set" / "safety-ppe-unavailable-or-unsuitable.json",
    ROOT / "second_set" / "chemical-recipe-outdated-procedure.json",
    ROOT / "second_set" / "positive-alcohol-test-high-risk-position.json",
    ROOT / "second_set" / "temporary-day-to-three-shift-refusal.json",
    ROOT / "second_set" / "insults-supervisor-fatigue-context.json",
)


def test_real_case_plans_never_execute_blocked_queries_or_claim_fake_live_results() -> None:
    assert len(FILES) == 11
    for index, path in enumerate(FILES, start=1):
        payload = json.loads(path.read_text(encoding="utf-8"))
        question = payload.get("question") or payload.get("employee_question") or payload.get("prompt")
        if not question:
            case_input = payload.get("case_input", {})
            statements = (
                *case_input.get("facts_provided", ()),
                *case_input.get("facts_recognized", ()),
                *case_input.get("facts_contested", ()),
                *case_input.get("facts_alleged", ()),
                *(
                    item.get("item", "")
                    for item in case_input.get("missing_information", ())
                    if isinstance(item, dict)
                ),
            )
            question = " ".join(str(item) for item in statements if item)
        assert question
        plan = build_research_plan(
            build_case_factual_core(question, origin_session_id=f"lot3-case-{index}")
        )
        summary = SourceExecutionCoordinator(default_metadata_executors()).execute(plan)
        assert summary.blocked_queries == len(plan.blocked_queries)
        assert all(
            event.status not in {
                RetrievalStatus.LIVE_SEARCH_EXECUTED,
                RetrievalStatus.LIVE_RESULT_OBTAINED,
                RetrievalStatus.LIVE_NO_RELEVANT_RESULT,
            }
            for event in summary.events
        )
