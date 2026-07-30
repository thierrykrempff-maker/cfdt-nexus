from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine
from tests.cse_cssct_test_support import corpus, pv_query


def test_excerpt_is_an_exact_source_substring_when_no_redaction(tmp_path):
    result = CSECSSCTSearchEngine(corpus(tmp_path)).search(pv_query("laboratoire", "poste"))
    passage = result.results[0]
    assert passage.excerpt in passage.raw_text
    assert passage.page
    assert passage.document_id
