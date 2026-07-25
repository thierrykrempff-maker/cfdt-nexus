"""Merge, classify and bound questions from all engines."""

from __future__ import annotations

from .models import FusedQuestion, NormalizedEngineResult, QuestionPriority
from .normalization import normalize_text


def merge_questions(
    results: tuple[NormalizedEngineResult, ...],
    answered_facts: tuple[str, ...],
) -> tuple[FusedQuestion, ...]:
    answered = normalize_text(" ".join(answered_facts))
    candidates: dict[str, FusedQuestion] = {}
    for result in results:
        for text in (*result.missing_information, *result.questions):
            cleaned = " ".join(text.split())
            key = normalize_text(cleaned).rstrip(" ?.")
            if not key or key in answered:
                continue
            priority = (
                QuestionPriority.CRITICAL
                if any(marker in key for marker in ("date", "periode", "document", "montant"))
                else QuestionPriority.PRIORITY
            )
            candidates.setdefault(
                key,
                FusedQuestion(cleaned, priority, "Nécessaire pour sécuriser la qualification."),
            )
    ordered = sorted(
        candidates.values(),
        key=lambda item: (
            0 if item.priority is QuestionPriority.CRITICAL else 1,
            normalize_text(item.text),
        ),
    )
    critical = [item for item in ordered if item.priority is QuestionPriority.CRITICAL][:3]
    priority = [item for item in ordered if item.priority is QuestionPriority.PRIORITY][:5]
    return tuple((*critical, *priority))
