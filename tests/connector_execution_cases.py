from __future__ import annotations

from SYNDICAL_REASONING_ENGINE import (
    IssueCategory,
    LegalIssue,
    PlanningStatus,
    ResearchPlan,
    ResearchQuery,
    ResearchTarget,
    SourceFamily,
)


def plan_for(
    family: SourceFamily = SourceFamily.LABOUR_CODE,
    *,
    query_text: str = "procédure disciplinaire",
    blocked: bool = False,
    case_session_id: str = "case-session",
) -> ResearchPlan:
    issue = LegalIssue(
        "issue-1",
        case_session_id,
        "Question",
        query_text,
        IssueCategory.DISCIPLINARY_PROCEDURE,
        ("fact-1",),
        (),
        (),
        "NORMAL",
        PlanningStatus.READY,
        "HIGH",
        (query_text,),
        ("test-rule",),
        True,
        family in {
            SourceFamily.INEOS_AGREEMENT,
            SourceFamily.INEOS_INTERNAL_RULE,
            SourceFamily.INEOS_PROCEDURE,
        },
        False,
    )
    target = ResearchTarget(
        "target-1",
        issue.issue_id,
        family,
        1,
        "Vérifier la règle applicable",
        True,
        "référence vérifiable",
        "texte ou métadonnée qualifiée",
        False,
        (),
    )
    status = PlanningStatus.BLOCKED_BY_MISSING_FACTS if blocked else PlanningStatus.READY
    query = ResearchQuery(
        "query-1",
        issue.issue_id,
        target.target_id,
        query_text,
        tuple(query_text.split()),
        ("fact-1",),
        "à la date des faits",
        "Sarralbe",
        "salarié",
        ("STATUTE",),
        "référence",
        "extrait",
        (),
        1,
        True,
        "Question juridique identifiée",
        status,
    )
    return ResearchPlan(
        "plan-1",
        case_session_id,
        (issue,),
        (target,),
        () if blocked else (query,),
        (query,) if blocked else (),
        (),
        (),
        status,
        None,
        "2.0",
    )


def live_document() -> dict[str, object]:
    return {
        "id": "doc-1",
        "title": "Code du travail",
        "article": "L1332-1",
        "excerpt": "Règle applicable.",
        "document_type": "STATUTE",
    }
