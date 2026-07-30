from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine, MeetingBody
from tests.cse_cssct_test_support import corpus, pv_query


def test_ppe_query_is_scoped_to_cssct(tmp_path):
    result = CSECSSCTSearchEngine(corpus(tmp_path)).search(
        pv_query("EPI", "gants", "visière", "risque chimique", bodies=(MeetingBody.CSSCT,))
    )
    assert result.results
    assert all(item.meeting_body is MeetingBody.CSSCT for item in result.results)
