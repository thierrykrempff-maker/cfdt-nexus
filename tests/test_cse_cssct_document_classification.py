from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine, MeetingBody, PassageNature
from tests.cse_cssct_test_support import corpus, pv_query


def test_cse_cssct_and_ce_are_not_conflated(tmp_path):
    engine = CSECSSCTSearchEngine(corpus(tmp_path))
    result = engine.search(pv_query("gants", "EPI", bodies=(MeetingBody.CSSCT,)))
    assert result.results
    assert {item.meeting_body for item in result.results} == {MeetingBody.CSSCT}


def test_annex_is_a_document_reference_not_a_meeting_discussion(tmp_path):
    engine = CSECSSCTSearchEngine(corpus(tmp_path))
    query = pv_query("horaires", "effectifs")
    query = type(query)(
        query.query_id, query.issue_id, query.target_id, query.case_session_id,
        query.concepts, query.variants, query.exact_phrases, query.negative_terms,
        query.temporal_scope, query.body_scope, query.establishment_scope,
        ("annexe",), query.min_score, query.max_results, query.purpose,
        query.blocked, query.reason,
    )
    result = engine.search(query)
    assert result.results[0].passage_nature is PassageNature.DOCUMENT_REFERENCE
