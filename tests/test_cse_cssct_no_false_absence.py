from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine
from tests.cse_cssct_test_support import corpus, pv_query


def test_no_result_never_claims_cse_was_not_informed(tmp_path):
    public = CSECSSCTSearchEngine(corpus(tmp_path)).search(
        pv_query("concept totalement absent")
    ).to_dict(public=True)
    assert public["results_retained"] == 0
    assert "ne prouve pas" in public["message"]
    assert "jamais été informé" not in public["message"]
