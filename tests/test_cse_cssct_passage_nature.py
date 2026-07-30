from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine, PassageNature
from tests.cse_cssct_test_support import corpus, pv_query


def test_question_is_not_misrepresented_as_management_response(tmp_path):
    result = CSECSSCTSearchEngine(corpus(tmp_path)).search(pv_query("gants", bodies=()))
    assert result.results
    assert result.results[0].passage_nature in {
        PassageNature.EMPLOYEE_REPRESENTATIVE_QUESTION,
        PassageNature.MANAGEMENT_RESPONSE,
    }
    assert result.results[0].qualification_reason
