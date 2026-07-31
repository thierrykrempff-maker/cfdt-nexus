from __future__ import annotations

from tests.test_http_analyze_no_origin_session_id import (
    assert_no_internal_ids,
    load_server,
    post_payload,
    unsafe_payload,
)


def test_http_boundary_recursively_sanitizes_lists_and_mappings() -> None:
    source = unsafe_payload(with_evidence=True)
    source["nested"] = [{"item": {"storage_id": "private", "label": "Source utile"}}]
    source["tuple_evidence"] = (
        {"target_id": "private-target", "reference": "Cass. soc., 1 janvier 2024"},
    )

    status, public = post_payload(load_server(), source)

    assert status == 200
    assert_no_internal_ids(public)
    assert public["nested"][0]["item"]["label"] == "Source utile"
    assert public["tuple_evidence"][0]["reference"] == "Cass. soc., 1 janvier 2024"
