from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine, SpeakerRole
from tests.cse_cssct_test_support import corpus, pv_query


def test_explicit_management_statement_gets_management_role(tmp_path):
    result = CSECSSCTSearchEngine(corpus(tmp_path)).search(pv_query("pause", "badgeage"))
    assert result.results[0].speaker_role is SpeakerRole.MANAGEMENT
