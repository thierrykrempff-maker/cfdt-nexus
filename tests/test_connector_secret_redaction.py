import json

from SYNDICAL_REASONING_ENGINE import redact_endpoint, redact_mapping, redact_public_value


def test_secrets_urls_headers_and_local_paths_are_redacted() -> None:
    payload = redact_mapping({
        "Authorization": "Bearer abcdefghijklmnop",
        "error": "token=abcdefghijklmnop C:\\private\\secret.txt /home/user/private",
    })
    rendered = json.dumps(payload)
    assert "abcdefghijklmnop" not in rendered
    assert "C:\\private" not in rendered
    assert "/home/user" not in rendered
    assert "real" not in (redact_endpoint("https://example.test/a?access_token=real") or "")
    assert "secret" not in (redact_public_value("Authorization: secret") or "").lower()
