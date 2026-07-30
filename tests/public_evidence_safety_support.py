from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace


@dataclass(frozen=True)
class FakeBundle:
    title: str
    excerpt: str
    issue_id: str = "issue-1"
    query_id: str = "query-1"
    fact_ids: tuple[str, ...] = ("fact-1",)
    reference: str = "page 1"
    research_objective: str = (
        "Rechercher uniquement un précédent ou un contexte interne concernant : "
        "Finalité du badgeage"
    )

    def to_dict(self, *, public: bool = False):
        return {
            "title": self.title,
            "reference": self.reference,
            "excerpt": self.excerpt,
            "source_type": "CSE_CSSCT_MINUTES",
            "retrieval_status": "LOCAL_DOCUMENT",
            "usable_in_public_response": True,
        }


def selection_result(
    bundle: FakeBundle,
    *,
    issue: str = (
        "Le tourniquet peut-il être utilisé pour reconstituer les pauses au "
        "regard de la finalité déclarée du badgeage ?"
    ),
    factual_scope: tuple[str, ...] = (
        "La direction utilise les données du badgeage au tourniquet.",
    ),
):
    plan = SimpleNamespace(
        issues=(SimpleNamespace(issue_id="issue-1", legal_question=issue),),
        queries=(
            SimpleNamespace(
                query_id="query-1",
                factual_scope=factual_scope,
            ),
        ),
        blocked_queries=(),
    )
    return SimpleNamespace(
        plan=plan,
        selection=SimpleNamespace(selected=(bundle,)),
    )


def applicable_source(bundle: FakeBundle):
    return {
        "source_title": bundle.title,
        "article_or_clause": bundle.reference,
        "precise_excerpt": bundle.excerpt,
        "citation_ready": True,
        "rejection_reason": None,
    }
