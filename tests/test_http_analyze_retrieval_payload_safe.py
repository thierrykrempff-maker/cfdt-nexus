from __future__ import annotations

from tests.test_http_analyze_no_origin_session_id import (
    assert_no_internal_ids,
    load_server,
    post_payload,
    unsafe_payload,
)


def test_local_document_retrieval_response_keeps_evidence_without_internal_ids() -> None:
    source = unsafe_payload(with_evidence=True)
    source["retrieval"] = {
        "status": "LOCAL_DOCUMENT",
        "network_call_executed": False,
        "fallback_used": False,
        "document_id": "private-document",
        "results": [{"chunk_id": "private-chunk", "title": "PV CSE — badgeage"}],
    }

    status, public = post_payload(load_server(), source)

    assert status == 200
    assert public["retrieval"]["status"] == "LOCAL_DOCUMENT"
    assert public["retrieval"]["network_call_executed"] is False
    assert public["retrieval"]["results"][0]["title"] == "PV CSE — badgeage"
    assert_no_internal_ids(public)
