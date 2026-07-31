from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import threading
from typing import Any
import urllib.request
import uuid


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "apps" / "nexus-local-interface" / "server.py"
FORBIDDEN_KEYS = {
    "origin_session_id",
    "case_session_id",
    "plan_id",
    "event_id",
    "query_id",
    "target_id",
    "issue_id",
    "fact_id",
    "document_id",
    "chunk_id",
    "storage_id",
    "internal_id",
    "trace_id",
}


def load_server() -> Any:
    module_name = f"lot4f_server_{uuid.uuid4().hex}"
    sys.path.insert(0, str(SERVER_PATH.parent))
    spec = importlib.util.spec_from_file_location(module_name, SERVER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def unsafe_payload(*, status: str = "READY", with_evidence: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": True,
        "status": status,
        "answer": {
            "query": "Question de test",
            "origin_session_id": "session-private",
            "route": {
                "issue_id": "issue-private",
                "domains": ["droit_travail"],
            },
            "legal_reference": "Code du travail, article L. 3121-1",
        },
        "detailed_analysis": {
            "factual_core": {
                "origin_session_id": "nested-private",
                "facts": [
                    {
                        "fact_id": "fact-private",
                        "statement": "Horaire annoncé par écrit.",
                    }
                ],
            },
            "technical_trace": {
                "trace_id": "trace-private",
                "path": r"C:\tmp\private\index.jsonl",
            },
        },
        "events": [
            {
                "event_id": "event-private",
                "queries": [{"query_id": "query-private", "status": "LOCAL_DOCUMENT"}],
            }
        ],
    }
    if with_evidence:
        payload["public_summary"] = {
            "sources": [
                {
                    "title": "PV CSE — organisation du travail",
                    "excerpt": "Le badgeage fait l'objet d'une information collective.",
                    "document_id": "document-private",
                    "chunk_id": "chunk-private",
                }
            ]
        }
    return payload


def post_payload(
    server_module: Any,
    payload: dict[str, Any],
    *,
    query: str = "Question de test",
) -> tuple[int, dict[str, Any]]:
    original = server_module.analyze_public_question
    server_module.analyze_public_question = lambda *args, **kwargs: payload
    httpd = server_module.ThreadingHTTPServer(
        ("127.0.0.1", 0),
        server_module.NexusHandler,
    )
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{httpd.server_address[1]}/api/analyze",
            data=json.dumps({"query": query}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    finally:
        httpd.shutdown()
        httpd.server_close()
        server_module.analyze_public_question = original


def nested_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(str(key).casefold())
            keys.update(nested_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(nested_keys(item))
    return keys


def assert_no_internal_ids(payload: dict[str, Any]) -> None:
    found = nested_keys(payload)
    assert not (found & FORBIDDEN_KEYS)
    assert not any(
        key.endswith(
            (
                "_session_id",
                "_plan_id",
                "_event_id",
                "_query_id",
                "_target_id",
                "_issue_id",
                "_fact_id",
                "_document_id",
                "_chunk_id",
                "_storage_id",
                "_internal_id",
                "_trace_id",
            )
        )
        for key in found
    )


def test_http_boundary_removes_origin_session_id_at_every_depth() -> None:
    status, payload = post_payload(load_server(), unsafe_payload())

    assert status == 200
    assert_no_internal_ids(payload)
    assert payload["answer"]["legal_reference"] == "Code du travail, article L. 3121-1"
