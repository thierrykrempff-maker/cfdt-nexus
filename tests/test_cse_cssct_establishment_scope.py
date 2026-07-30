from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine
from tests.cse_cssct_test_support import corpus, pv_query


def test_other_establishment_is_rejected(tmp_path):
    result = CSECSSCTSearchEngine(corpus(tmp_path)).search(
        pv_query("pause", "badgeage", establishment="Sarralbe")
    )
    assert all("Tavaux" not in item.raw_text for item in result.results)
    assert dict(result.rejected_reasons)["ESTABLISHMENT_SCOPE"] == 1
