from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine
from tests.cse_cssct_test_support import corpus, pv_query


def test_passages_keep_query_issue_and_case_scopes(tmp_path):
    engine = CSECSSCTSearchEngine(corpus(tmp_path))
    first = engine.search(pv_query("pause", query_id="q-a", issue_id="i-a", case_id="a"))
    second = engine.search(pv_query("laboratoire", query_id="q-b", issue_id="i-b", case_id="b"))
    assert {item.query_id for item in first.results} == {"q-a"}
    assert {item.issue_id for item in second.results} == {"i-b"}
    assert {item.passage_id for item in first.results}.isdisjoint(
        {item.passage_id for item in second.results}
    )
