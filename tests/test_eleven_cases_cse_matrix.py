from SYNDICAL_REASONING_ENGINE import CSECSSCTSearchEngine, MeetingBody
from tests.cse_cssct_test_support import corpus, pv_query


CASES = {
    "case-01": ("conflit", "messagerie", "RPS"),
    "case-02": ("pause", "badgeage", "tourniquet"),
    "case-03": ("souffrance", "RPS", "médiation"),
    "case-04": ("laboratoire", "personnel posté", "réorganisation"),
    "case-05": ("réunion CSSCT", "délégation"),
    "case-06": ("règle 10 pour cent",),
    "case-07": ("EPI", "gants", "risque chimique"),
    "case-08": ("3x8", "fatigue", "horaires"),
    "case-09": ("procédure", "version", "diffusion"),
    "case-10": ("alcoolémie", "contre-expertise", "CSSCT"),
    "case-11": ("fatigue", "travail de nuit", "RPS"),
}


def test_eleven_case_queries_are_isolated_and_blocked_cases_do_not_run(tmp_path):
    engine = CSECSSCTSearchEngine(corpus(tmp_path))
    executions = {}
    for case_id, concepts in CASES.items():
        blocked = case_id in {"case-05", "case-06"}
        bodies = (MeetingBody.CSSCT,) if case_id == "case-07" else (
            MeetingBody.CSE, MeetingBody.CE, MeetingBody.CSSCT
        )
        executions[case_id] = engine.search(
            pv_query(*concepts, query_id=f"query-{case_id}", case_id=case_id,
                     blocked=blocked, bodies=bodies)
        )
    assert len(executions) == 11
    assert executions["case-05"].documents_scanned == 0
    assert executions["case-06"].documents_scanned == 0
    assert executions["case-02"].results
    assert executions["case-04"].results
    assert executions["case-07"].results
    assert executions["case-09"].results
    passage_ids = [
        item.passage_id for execution in executions.values() for item in execution.results
    ]
    assert len(passage_ids) == len(set(passage_ids))
