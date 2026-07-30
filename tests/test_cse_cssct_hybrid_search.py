from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine, PVSearchMode
from tests.cse_cssct_test_support import corpus, pv_query


def test_local_hybrid_search_uses_variants_and_scores(tmp_path):
    result = CSECSSCTSearchEngine(corpus(tmp_path)).search(
        pv_query("pause", "badgeage", "tourniquet")
    )
    assert result.search_mode is PVSearchMode.HYBRID_LOCAL
    assert result.results[0].final_score > 0.5
    assert "badgeage" in result.results[0].matched_concepts
