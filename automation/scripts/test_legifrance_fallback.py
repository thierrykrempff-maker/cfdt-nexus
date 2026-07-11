#!/usr/bin/env python
"""Targeted regression tests for the Legifrance fallback qualification."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import assistant_ds_router as router  # noqa: E402


def code_source(article: str, excerpt: str, score: int = 90) -> dict[str, Any]:
    return {
        "document": "Code du travail",
        "document_type": "code_travail",
        "source_layer": "code_travail",
        "article": article,
        "article_or_section": article,
        "official_id": f"LEGI-{article}",
        "legifrance_id": f"LEGI-{article}",
        "etat": "VIGUEUR",
        "is_in_force": True,
        "retrieved_at": "2026-07-10T00:00:00Z",
        "url": "https://www.legifrance.gouv.fr/codes/article_lc/test",
        "excerpt": excerpt,
        "chunk_id": f"LEGI-{article}",
        "score": score,
        "ranking_reasons": ["Source officielle Legifrance via API PISTE"],
    }


class FakeLegifrance:
    def __init__(self, result: dict[str, Any] | None, available: bool = True) -> None:
        self._result = result
        self._available = available

    def status_from_env(self) -> dict[str, Any]:
        return {"detected": True, "available": self._available, "reason": "fake Legifrance"}

    def LegifranceClient(self) -> Any:  # noqa: N802 - mimic module API.
        result = self._result

        class Client:
            def search_code_sources(self, query: str, limit: int = 3) -> dict[str, Any]:
                return result or {"available": True, "sources": [], "warnings": []}

        return Client()


@contextmanager
def patched_connectors(legifrance_module: Any) -> Any:
    previous = (router.legifrance, router.judilibre, router.cdtn, router.bridge)
    router.legifrance = legifrance_module
    router.judilibre = None
    router.cdtn = None
    router.bridge = None
    try:
        yield
    finally:
        router.legifrance, router.judilibre, router.cdtn, router.bridge = previous


def code_sources(answer: dict[str, Any]) -> list[dict[str, Any]]:
    return [source for source in answer.get("sources", []) if source.get("source_layer") == "code_travail"]


def latest_status(answer: dict[str, Any]) -> str:
    audits = answer.get("legifrance_audit") or []
    assert audits
    return str(audits[-1]["status"])


def ask_with_fake_legifrance(query: str, result: dict[str, Any] | None, available: bool = True) -> dict[str, Any]:
    with patched_connectors(FakeLegifrance(result, available=available)):
        return router.ask(query, limit=4, source_limit=6)


def assert_select_final_sources_protects_only_qualified_code() -> None:
    route = router.route_query("Ai-je droit a une prime panier ?")
    rejected = router.normalize_source(
        code_source("L3121-28", "Les heures supplementaires ouvrent droit a une majoration salariale."),
        "legifrance_code_travail",
    )
    rejected["legifrance_relevance_status"] = "rejected"
    local = router.normalize_source(
        {
            "document": "Accord prime panier",
            "source_layer": "accord_entreprise",
            "document_type": "accord_entreprise",
            "article": "Article test",
            "excerpt": "prime panier indemnite panier",
            "score": 80,
        },
        "bible_accords",
    )
    selected = router.select_final_sources([rejected, local], route, 6)
    assert not code_sources({"sources": selected})


def test_unit_merge_statuses() -> None:
    route = router.route_query("Que dit le Code du travail sur une sanction disciplinaire ?")
    base = {
        "route": route,
        "sources": [],
        "warnings": [],
        "legifrance_audit": [],
        "findings": [],
        "documents_to_request": [],
        "questions_to_ask": [],
    }
    for result, expected in [
        ({"available": True, "sources": [], "warnings": []}, "empty"),
        ({"available": False, "sources": [], "warnings": ["timeout"]}, "api_error"),
    ]:
        answer = {**base, "sources": [], "warnings": [], "legifrance_audit": []}
        router.merge_legifrance_result(answer, result)
        assert latest_status(answer) == expected
        assert not code_sources(answer)


def test_filter_synonym_cases() -> None:
    cases = [
        (
            {"query": "La direction peut-elle me mettre a pied ?", "domains": ["bible_accords", "disciplinaire"]},
            code_source("L1332-2", "La sanction disciplinaire impose une procedure et un entretien prealable."),
        ),
    ]
    for route, source in cases:
        normalized = router.normalize_source(source, "legifrance_code_travail")
        assert router.legifrance_relevance_evaluation(normalized, route)["accepted"]


def test_ask_disciplinaire_mise_a_pied() -> None:
    query = "La direction peut-elle me mettre a pied ?"
    retained = ask_with_fake_legifrance(
        query,
        {
            "available": True,
            "sources": [code_source("L1332-2", "La sanction disciplinaire impose une procedure et un entretien prealable.")],
            "warnings": [],
        },
    )
    assert "disciplinaire" in retained["route"]["domains"]
    assert "legifrance_code_travail" in retained["route"]["engines"]
    assert latest_status(retained) == "retained"
    assert code_sources(retained)

    weak = ask_with_fake_legifrance(
        query,
        {
            "available": True,
            "sources": [code_source("L3121-28", "Les heures supplementaires ouvrent droit a une majoration salariale.")],
            "warnings": [],
        },
    )
    audit = weak["legifrance_audit"][-1]
    assert audit["status"] == "weak"
    assert audit["sources_received"] == 1
    assert audit["sources_retained"] == 0
    assert audit["rejected_sources"]
    assert audit["warnings"]
    assert not code_sources(weak)


def test_ask_integration_and_synonyms() -> None:
    retained_cases = [
        (
            "Comment sont payees mes heures en plus ?",
            "L3121-28",
            "Les heures supplementaires ouvrent droit a une majoration salariale.",
        ),
        (
            "Combien de temps de repos dois-je avoir entre deux postes ?",
            "L3131-1",
            "Tout salarie beneficie d'un repos quotidien d'une duree minimale de onze heures consecutives.",
        ),
        (
            "Je veux faire changer mon coefficient.",
            "L0000-1",
            "La classification conventionnelle et le coefficient doivent correspondre aux fonctions exercees.",
        ),
    ]
    for query, article, excerpt in retained_cases:
        answer = ask_with_fake_legifrance(query, {"available": True, "sources": [code_source(article, excerpt)], "warnings": []})
        assert latest_status(answer) == "retained", query
        assert code_sources(answer), query

    weak = ask_with_fake_legifrance(
        "Ai-je droit a une prime panier ?",
        {
            "available": True,
            "sources": [code_source("L3121-28", "Les heures supplementaires ouvrent droit a une majoration salariale.")],
            "warnings": [],
        },
    )
    assert latest_status(weak) == "weak"
    assert not code_sources(weak)


def test_not_configured_and_response_depth() -> None:
    query = "Combien de temps de repos dois-je avoir entre deux postes ?"
    expected_depth = router.response_depth(router.route_query(query))
    answer = ask_with_fake_legifrance(query, None, available=False)
    assert latest_status(answer) == "not_configured"
    assert answer["response_depth"] == expected_depth
    assert not code_sources(answer)


def main() -> None:
    assert_select_final_sources_protects_only_qualified_code()
    test_unit_merge_statuses()
    test_filter_synonym_cases()
    test_ask_disciplinaire_mise_a_pied()
    test_ask_integration_and_synonyms()
    test_not_configured_and_response_depth()
    print("OK - tests cibles fallback Legifrance")


if __name__ == "__main__":
    main()
