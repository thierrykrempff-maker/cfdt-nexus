from __future__ import annotations

from tests.test_http_analyze_no_origin_session_id import (
    assert_no_internal_ids,
    load_server,
    post_payload,
    unsafe_payload,
)


def test_blocked_plan_response_is_sanitized_without_becoming_executable() -> None:
    source = unsafe_payload(status="BLOCKED_BY_MISSING_FACTS")
    source["answer"]["research_plan"] = {
        "plan_id": "blocked-plan",
        "queries": [],
        "blocked_queries": [{"query_id": "blocked-query", "status": "CONDITIONAL_QUERY"}],
    }

    status, public = post_payload(load_server(), source, query="La règle des 10 % s'applique.")

    assert status == 200
    assert public["status"] == "BLOCKED_BY_MISSING_FACTS"
    assert public["answer"]["research_plan"]["queries"] == []
    assert_no_internal_ids(public)
