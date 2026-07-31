from __future__ import annotations

import json

from tests.test_http_analyze_no_origin_session_id import (
    load_server,
    post_payload,
    unsafe_payload,
)


def test_safe_collective_prevention_response_exposes_no_individual_health_data() -> None:
    source = unsafe_payload(with_evidence=True)
    source["public_summary"]["prevention"] = [
        "Vérifier collectivement la disponibilité et l'adaptation des EPI."
    ]
    source["detailed_analysis"]["technical_trace"]["private_health_note"] = (
        "Diagnostic médical individuel et traitement médical."
    )
    source["detailed_analysis"]["technical_trace"]["internal_id"] = "medical-private"

    status, public = post_payload(load_server(), source)
    encoded = json.dumps(public, ensure_ascii=False).casefold()

    assert status == 200
    assert "diagnostic médical individuel" not in encoded
    assert "traitement médical" not in encoded
    assert "arrêt maladie individuel" not in encoded
    assert "restriction médicale individuelle" not in encoded
    assert "adaptation des epi" in encoded
