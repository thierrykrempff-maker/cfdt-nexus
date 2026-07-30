from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine, NOT_A_LEGAL_NORM
from tests.cse_cssct_test_support import corpus, pv_query


def test_every_passage_denies_automatic_normative_value(tmp_path):
    result = CSECSSCTSearchEngine(corpus(tmp_path)).search(pv_query("pause"))
    assert result.results
    assert all(NOT_A_LEGAL_NORM in item.does_not_prove for item in result.results)
    assert "accord collectif" not in result.results[0].legal_value
