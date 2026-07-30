import json

from NEXUS_RUNTIME_INTEGRATION import sanitize_public_payload


def test_origin_and_case_session_ids_never_cross_public_boundary() -> None:
    payload = {
        "ok": True,
        "answer": {
            "nested": {
                "origin_session_id": "session-private",
                "case_session_id": "case-private",
            }
        },
    }
    encoded = json.dumps(sanitize_public_payload(payload))

    assert "origin_session_id" not in encoded
    assert "case_session_id" not in encoded
