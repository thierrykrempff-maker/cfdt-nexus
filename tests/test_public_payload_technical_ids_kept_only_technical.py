from NEXUS_RUNTIME_INTEGRATION import sanitize_public_payload


def test_public_sanitization_does_not_mutate_internal_trace() -> None:
    internal = {
        "ok": True,
        "answer": {
            "trace": {
                "query_id": "query-internal",
                "fact_id": "fact-internal",
            }
        },
    }

    public = sanitize_public_payload(internal)

    assert internal["answer"]["trace"]["query_id"] == "query-internal"
    assert public["answer"]["trace"] == {}
