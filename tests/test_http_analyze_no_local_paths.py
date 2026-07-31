from __future__ import annotations

import json

from tests.test_http_analyze_no_origin_session_id import (
    load_server,
    post_payload,
    unsafe_payload,
)


def test_http_response_contains_no_windows_or_posix_local_path() -> None:
    source = unsafe_payload()
    source["more"] = {
        "windows": r"D:\secret\corpus\document.pdf",
        "posix": "/home/user/private/document.pdf",
        "temporary": "/tmp/nexus/private.json",
    }

    status, public = post_payload(load_server(), source)
    encoded = json.dumps(public, ensure_ascii=False).casefold()

    assert status == 200
    assert "c:\\" not in encoded
    assert "d:\\" not in encoded
    assert "/home/" not in encoded
    assert "/tmp/" not in encoded
