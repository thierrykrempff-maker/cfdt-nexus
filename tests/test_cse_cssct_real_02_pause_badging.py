from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine
from tests.cse_cssct_test_support import corpus, pv_query


def test_pause_badging_concepts_find_the_relevant_passage(tmp_path):
    result = CSECSSCTSearchEngine(corpus(tmp_path)).search(
        pv_query("pause", "cigarette", "badgeage", "pointage", "tourniquet")
    )
    assert result.passages_retained == 1
    assert {"pause", "cigarette", "badgeage", "tourniquet"}.intersection(
        result.results[0].matched_concepts
    )
