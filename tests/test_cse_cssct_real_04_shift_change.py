from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine
from tests.cse_cssct_test_support import corpus, pv_query


def test_shift_change_finds_laboratory_reorganisation(tmp_path):
    result = CSECSSCTSearchEngine(corpus(tmp_path)).search(
        pv_query("laboratoire", "personnel de jour", "personnel posté", "réorganisation")
    )
    assert result.results
    assert "laboratoire" in result.results[0].excerpt.lower()
