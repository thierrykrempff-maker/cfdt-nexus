from __future__ import annotations

from pathlib import Path

from tests.test_http_analyze_no_origin_session_id import (
    assert_no_internal_ids,
    load_server,
    post_payload,
    unsafe_payload,
)


def test_flags_enabled_response_is_safe_and_announces_controlled_pilot(monkeypatch) -> None:
    server = load_server()
    monkeypatch.setenv("NEXUS_CONTROLLED_PILOT_MODE", "true")
    monkeypatch.setenv("NEXUS_RETRIEVAL_TO_FINAL_RESPONSE_ENABLED", "true")
    monkeypatch.setenv("NEXUS_SOURCE_EXECUTION_COORDINATOR_ENABLED", "true")
    monkeypatch.setenv("NEXUS_SOURCE_EXECUTION_NETWORK_ENABLED", "false")

    status, payload = post_payload(server, unsafe_payload(with_evidence=True))

    assert status == 200
    assert_no_internal_ids(payload)
    assert payload["controlled_pilot"]["enabled"] is True
    assert "VALIDATION HUMAINE OBLIGATOIRE" in payload["controlled_pilot"]["title"]
    html = (Path(server.APP_DIR) / "index.html").read_text(encoding="utf-8")
    assert html.count("PILOTE LOCAL — VALIDATION HUMAINE OBLIGATOIRE") >= 3
    assert 'id="pilotBannerInput"' in html
    assert 'id="pilotBannerResult"' in html
    assert 'id="pilotBannerReport"' in html
    script = (Path(server.APP_DIR) / "app.js").read_text(encoding="utf-8")
    assert "applyControlledPilotMode(health.controlled_pilot)" in script
    assert "lines.unshift(...pilotLines)" in script


def test_controlled_pilot_is_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("NEXUS_CONTROLLED_PILOT_MODE", raising=False)
    status, payload = post_payload(load_server(), unsafe_payload())

    assert status == 200
    assert "controlled_pilot" not in payload
