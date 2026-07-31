from __future__ import annotations

from copy import deepcopy

from NEXUS_RUNTIME_INTEGRATION.public_payload import sanitize_http_public_payload
from tests.test_http_analyze_no_origin_session_id import assert_no_internal_ids, unsafe_payload


def test_final_http_sanitizer_does_not_mutate_the_technical_trace() -> None:
    technical = unsafe_payload(with_evidence=True)
    original = deepcopy(technical)

    public = sanitize_http_public_payload(technical)

    assert technical == original
    assert technical["detailed_analysis"]["factual_core"]["origin_session_id"]
    assert technical["events"][0]["event_id"]
    assert_no_internal_ids(public)
