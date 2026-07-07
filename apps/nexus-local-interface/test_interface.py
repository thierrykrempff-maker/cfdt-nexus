#!/usr/bin/env python
"""HTTP smoke tests for the Nexus local interface."""

from __future__ import annotations

import json
import threading
import urllib.request

from server import NexusHandler, ThreadingHTTPServer


QUESTIONS = [
    "classification",
    "Un salarie en 5x8 peut-il assister a une reunion du CSE pendant son repos, et comment ce temps doit-il etre traite ?",
    "Un salarie d'astreinte intervient la nuit, son repos est interrompu et il reprend ensuite son poste : quels sont ses droits en matiere de repos et comment l'intervention doit-elle apparaitre sur la paie ?",
]


def post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=240) as response:  # noqa: S310 - localhost test.
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), NexusHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        for question in QUESTIONS:
            payload = post_json(f"http://127.0.0.1:{port}/api/analyze", {"query": question, "source_limit": 6})
            assert payload.get("ok") is True
            answer = payload["answer"]
            expert = payload["expert_juriste"]
            assert answer["short_answer"]
            assert answer["sources"]
            assert answer["confidence"]
            assert expert["active"] is True
            if "reunion du CSE" in question:
                assert answer["route"]["main_domain"] == "droit_syndical"
                assert "preparer_cse" not in answer["route"]["intents"]
                assert "mandat" in expert["response_courte"].casefold()
            if "astreinte" in question:
                assert [group["id"] for group in answer["issue_groups"]] == ["repos", "astreinte", "paie"]
        print("Interface locale: 3 questions OK")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
