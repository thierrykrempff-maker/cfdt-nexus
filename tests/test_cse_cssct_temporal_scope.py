from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine
from tests.cse_cssct_test_support import corpus, pv_query


def test_out_of_period_document_is_rejected(tmp_path):
    result = CSECSSCTSearchEngine(corpus(tmp_path)).search(
        pv_query("procédure", "version", temporal="2023-2026")
    )
    assert not result.results
    assert dict(result.rejected_reasons)["TEMPORAL_SCOPE"] == 1
