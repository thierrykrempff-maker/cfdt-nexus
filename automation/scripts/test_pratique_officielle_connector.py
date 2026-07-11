#!/usr/bin/env python
"""Tests locaux du prototype pratique officielle.

Ces tests n'utilisent pas le reseau: urllib.request.urlopen est remplace par
un faux client local pour couvrir securite URL, HTTP, cache et normalisation.
"""

from __future__ import annotations

import os
import socket
import sys
import tempfile
import time
import urllib.error
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pratique_officielle_connector as connector  # noqa: E402


VALID_HIT = {
    "source": "fiches_service_public",
    "title": "Astreinte dans le secteur prive",
    "description": "Une astreinte est une periode pendant laquelle le salarie reste disponible.",
    "slug": "astreinte-dans-le-secteur-prive",
    "cdtnId": "sp-astreinte",
    "breadcrumbs": [{"label": "Temps de travail", "position": 1, "slug": "temps-travail"}],
}


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200, headers: dict[str, str] | None = None) -> None:
        self.body = body
        self.status = status
        self.headers = headers or {}
        self.offset = 0
        self.closed = False
        self.read_calls: list[int] = []

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        self.closed = True

    def read(self, size: int = -1) -> bytes:
        self.read_calls.append(size)
        if size is None or size < 0:
            size = len(self.body) - self.offset
        chunk = self.body[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk

    def getheader(self, name: str) -> str | None:
        return self.headers.get(name)


class FakeUrlOpen:
    def __init__(self, *responses: Any) -> None:
        self.responses = list(responses)
        self.calls: list[str] = []

    def __call__(self, request: Any, timeout: int | None = None) -> FakeResponse:
        self.calls.append(getattr(request, "full_url", str(request)))
        if not self.responses:
            raise AssertionError("urlopen appele sans reponse simulee")
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def payload_bytes(payload: dict[str, Any]) -> bytes:
    return connector.json.dumps(payload).encode("utf-8")


def valid_payload() -> bytes:
    return payload_bytes({"results": [VALID_HIT]})


def exact_json_body(size: int) -> bytes:
    base = b'{"results":[]}'
    assert len(base) <= size
    return base + (b" " * (size - len(base)))


def client(tmp_path: Path, **kwargs: Any) -> connector.PratiqueOfficielleClient:
    config = connector.PratiqueOfficielleConfig(
        cache_dir=tmp_path,
        cache_ttl_seconds=kwargs.pop("cache_ttl_seconds", 3600),
        max_response_bytes=kwargs.pop("max_response_bytes", 100_000),
        **kwargs,
    )
    return connector.PratiqueOfficielleClient(config)


def cache_key_for(local_client: connector.PratiqueOfficielleClient, query: str) -> str:
    return connector.stable_hash(
        {
            "endpoint": connector.PRESEARCH_ENDPOINT,
            "query": query,
            "api_base_url": local_client.config.api_base_url,
        }
    )


def write_cache(local_client: connector.PratiqueOfficielleClient, query: str, content: str) -> Path:
    path = local_client.response_cache_path(cache_key_for(local_client, query))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def with_urlopen(fake: FakeUrlOpen, func: Any) -> Any:
    original = connector.urllib.request.urlopen
    connector.urllib.request.urlopen = fake
    try:
        return func()
    finally:
        connector.urllib.request.urlopen = original


def assert_valid_source(source: dict[str, Any]) -> None:
    assert source["source_layer"] == connector.SOURCE_LAYER
    assert source["license"] == connector.OFFICIAL_CONTENT_LICENSE
    assert source["attribution"] == connector.OFFICIAL_CONTENT_ATTRIBUTION
    assert source["official_disclaimer"] == connector.OFFICIAL_DISCLAIMER
    assert source["source_officielle"] == "Service-Public.fr"


def assert_rejected_url(url: str) -> None:
    try:
        connector.validate_api_base_url(url)
    except connector.PratiqueOfficielleSecurityError:
        return
    raise AssertionError(f"URL non rejetee: {url}")


def test_normalization_layer_license_attribution() -> None:
    result = connector.normalize_hit(VALID_HIT, "astreinte", "Astreinte")
    assert result["document"] == VALID_HIT["title"]
    assert result["summary"] == VALID_HIT["description"]
    assert_valid_source(result)


def test_url_security_rules() -> None:
    connector.validate_api_base_url("https://code.travail.gouv.fr")
    connector.validate_api_base_url("https://code.travail.gouv.fr/")

    rejected = [
        "http://code.travail.gouv.fr",
        "https://code.travail.gouv.fr.example.com",
        "https://evil-code.travail.gouv.fr",
        "https://code-travail.gouv.fr",
        "https://user:pass@code.travail.gouv.fr",
        "https://code.travail.gouv.fr:444",
        "https://code.travail.gouv.fr:443",
        "https://code.travail.gouv.fr/unexpected/path",
        "https://code.travail.gouv.fr?test=1",
        "https://code.travail.gouv.fr#fragment",
        "http://localhost:8123",
        "http://127.0.0.1:8123",
        "http://[::1]:8000",
        "http://192.168.1.10:8123",
    ]
    for url in rejected:
        assert_rejected_url(url)

    connector.validate_api_base_url("http://localhost:8123", allow_local_test_base_url=True)
    connector.validate_api_base_url("http://127.0.0.1:8123", allow_local_test_base_url=True)
    connector.validate_api_base_url("http://[::1]:8000", allow_local_test_base_url=True)
    assert_rejected_url("http://192.168.1.10:8123")


def test_unknown_source_and_empty_response() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fake = FakeUrlOpen(FakeResponse(payload_bytes({"results": [{"source": "blog", "title": "Hors source"}]})))
        result = with_urlopen(fake, lambda: client(Path(tmp)).search_sources("source inconnue"))
        assert result["available"] is True
        assert result["sources"] == []
        assert result["warnings"]

    with tempfile.TemporaryDirectory() as tmp:
        fake = FakeUrlOpen(FakeResponse(payload_bytes({"results": []})))
        result = with_urlopen(fake, lambda: client(Path(tmp)).search_sources("reponse vide"))
        assert result["available"] is True
        assert result["sources"] == []
        assert "Aucun contenu pratique officiel" in result["warnings"][0]


def test_http_errors_json_network_timeout_and_empty_body() -> None:
    for status in [400, 404, 500]:
        with tempfile.TemporaryDirectory() as tmp:
            response = FakeResponse(b"{}", status=status)
            result = with_urlopen(FakeUrlOpen(response), lambda: client(Path(tmp)).search_sources(f"http {status}"))
            assert result["available"] is False
            assert result["sources"] == []
            assert f"HTTP {status}" in result["warnings"][0]
            assert response.closed

    with tempfile.TemporaryDirectory() as tmp:
        invalid = FakeUrlOpen(FakeResponse(b"{not-json"))
        invalid_result = with_urlopen(invalid, lambda: client(Path(tmp)).search_sources("json invalide"))
        assert invalid_result["available"] is False
        assert "non JSON" in invalid_result["warnings"][0]

    with tempfile.TemporaryDirectory() as tmp:
        empty = FakeUrlOpen(FakeResponse(b""))
        empty_result = with_urlopen(empty, lambda: client(Path(tmp)).search_sources("body vide"))
        assert empty_result["available"] is False
        assert "non JSON" in empty_result["warnings"][0]

    with tempfile.TemporaryDirectory() as tmp:
        network = FakeUrlOpen(urllib.error.URLError("reseau indisponible"))
        network_result = with_urlopen(network, lambda: client(Path(tmp)).search_sources("reseau"))
        assert network_result["available"] is False
        assert "Connexion impossible" in network_result["warnings"][0]

    with tempfile.TemporaryDirectory() as tmp:
        timeout = FakeUrlOpen(socket.timeout("trop lent"))
        timeout_result = with_urlopen(timeout, lambda: client(Path(tmp)).search_sources("timeout"))
        assert timeout_result["available"] is False
        assert "Timeout" in timeout_result["warnings"][0]


def test_response_size_limit_and_closing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        response = FakeResponse(
            valid_payload(),
            headers={"Content-Length": str(connector.DEFAULT_MAX_RESPONSE_BYTES + 1)},
        )
        result = with_urlopen(
            FakeUrlOpen(response),
            lambda: client(Path(tmp), max_response_bytes=connector.DEFAULT_MAX_RESPONSE_BYTES).search_sources(
                "content length"
            ),
        )
        assert result["available"] is False
        assert "Reponse trop volumineuse" in result["warnings"][0]
        assert response.closed
        assert response.read_calls == []

    with tempfile.TemporaryDirectory() as tmp:
        response = FakeResponse(valid_payload())
        result = with_urlopen(FakeUrlOpen(response), lambda: client(Path(tmp)).search_sources("sans content length"))
        assert result["sources"]
        assert response.closed

    with tempfile.TemporaryDirectory() as tmp:
        response = FakeResponse(exact_json_body(64), headers={"Content-Length": "64"})
        result = with_urlopen(
            FakeUrlOpen(response),
            lambda: client(Path(tmp), max_response_bytes=64).search_sources("taille exacte"),
        )
        assert result["available"] is True
        assert result["sources"] == []
        assert response.closed

    with tempfile.TemporaryDirectory() as tmp:
        response = FakeResponse(exact_json_body(65), headers={"Content-Length": "10"})
        result = with_urlopen(
            FakeUrlOpen(response),
            lambda: client(Path(tmp), max_response_bytes=64).search_sources("content length mensonger"),
        )
        assert result["available"] is False
        assert "Reponse trop volumineuse" in result["warnings"][0]
        assert response.closed
        assert len(response.read_calls) >= 2

    with tempfile.TemporaryDirectory() as tmp:
        response = FakeResponse(exact_json_body(96))
        result = with_urlopen(
            FakeUrlOpen(response),
            lambda: client(Path(tmp), max_response_bytes=64).search_sources("progressif trop gros"),
        )
        assert result["available"] is False
        assert "Reponse trop volumineuse" in result["warnings"][0]
        assert response.closed


def test_cache_miss_hit_expired_corrupted_and_invalid_structures() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        fake = FakeUrlOpen(FakeResponse(valid_payload()))
        local_client = client(tmp_path)
        first = with_urlopen(fake, lambda: local_client.search_sources("cache"))
        assert first["sources"]
        assert len(fake.calls) == 1

        second = with_urlopen(fake, lambda: local_client.search_sources("cache"))
        assert second["sources"]
        assert len(fake.calls) == 1

        cache_path = local_client.response_cache_path(cache_key_for(local_client, "cache"))
        old_time = time.time() - 7200
        os.utime(cache_path, (old_time, old_time))
        expired_client = client(tmp_path, cache_ttl_seconds=1)
        expired_fake = FakeUrlOpen(FakeResponse(valid_payload()))
        expired = with_urlopen(expired_fake, lambda: expired_client.search_sources("cache"))
        assert expired["sources"]
        assert len(expired_fake.calls) == 1

    invalid_cache_cases = [
        ("cache corrompu", "{bad-json", "lecture impossible"),
        ("cache liste", "[]", "structure JSON inattendue"),
        ("cache chaine", '"texte"', "structure JSON inattendue"),
        ("cache null", "null", "structure JSON inattendue"),
        ("cache incomplet", '{"items":[]}', "structure incomplete"),
    ]
    for query, content, warning in invalid_cache_cases:
        with tempfile.TemporaryDirectory() as tmp:
            local_client = client(Path(tmp))
            write_cache(local_client, query, content)
            fake = FakeUrlOpen(FakeResponse(valid_payload()))
            result = with_urlopen(fake, lambda: local_client.search_sources(query))
            assert result["sources"]
            assert any(warning in item for item in result["warnings"])
            assert len(fake.calls) == 1


def test_inaccessible_cache_and_write_failure_do_not_crash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        cache_file = Path(tmp) / "not-a-dir"
        cache_file.write_text("block", encoding="utf-8")
        blocked_client = client(cache_file)
        fake = FakeUrlOpen(FakeResponse(valid_payload()))
        result = with_urlopen(fake, lambda: blocked_client.search_sources("cache inaccessible"))
        assert result["sources"]
        assert any("Cache pratique officielle non ecrit" in item for item in result["warnings"])


def test_forbidden_url_never_reuses_old_cache() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        rejected_client = client(Path(tmp), api_base_url="https://example.org")
        cache_path = rejected_client.response_cache_path(cache_key_for(rejected_client, "ancien cache"))
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(connector.json.dumps({"results": [VALID_HIT]}), encoding="utf-8")

        fake = FakeUrlOpen(AssertionError("aucun appel reseau attendu"))
        result = with_urlopen(fake, lambda: rejected_client.search_sources("ancien cache"))
        assert result["available"] is False
        assert result["sources"] == []
        assert "Domaine pratique officielle non autorise" in result["warnings"][0]
        assert fake.calls == []


def main() -> None:
    test_normalization_layer_license_attribution()
    test_url_security_rules()
    test_unknown_source_and_empty_response()
    test_http_errors_json_network_timeout_and_empty_body()
    test_response_size_limit_and_closing()
    test_cache_miss_hit_expired_corrupted_and_invalid_structures()
    test_inaccessible_cache_and_write_failure_do_not_crash()
    test_forbidden_url_never_reuses_old_cache()
    print("OK - tests pratique officielle")


if __name__ == "__main__":
    main()
