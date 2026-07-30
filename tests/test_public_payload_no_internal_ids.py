import json

from NEXUS_RUNTIME_INTEGRATION import sanitize_public_payload


def test_all_known_internal_identifiers_are_removed_recursively() -> None:
    identifiers = {
        "event_id": "event-secret",
        "query_id": "query-secret",
        "target_id": "target-secret",
        "issue_id": "issue-secret",
        "fact_id": "fact-secret",
        "document_id": "document-secret",
        "chunk_id": "chunk-secret",
        "plan_id": "plan-secret",
    }
    public = sanitize_public_payload({"ok": True, "answer": {"trace": identifiers}})
    encoded = json.dumps(public)

    assert not any(name in encoded for name in identifiers)
