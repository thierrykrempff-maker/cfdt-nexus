from SYNDICAL_REASONING_ENGINE import build_case_factual_core


def test_isolated_generic_words_do_not_select_specialized_domains() -> None:
    questions = (
        "Le mot nuit figure dans le titre d'un document.",
        "Je cherche la définition du mot coefficient.",
        "Une réunion amicale est prévue un jour de repos.",
        "La procédure de connexion au site internet est lente.",
    )

    assert all(
        build_case_factual_core(question).event_category == "GENERAL_EMPLOYEE_QUESTION"
        for question in questions
    )
