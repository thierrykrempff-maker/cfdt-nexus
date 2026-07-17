"""In-memory, metadata-only human review queue for ANACT classifications."""
from dataclasses import dataclass, replace

from .anact_classification_models import (
    ClassificationDecision,
    HumanValidationStatus,
    UrlCategory,
    UrlClassification,
)


@dataclass(frozen=True)
class ReviewDecision:
    sequence: int
    status: HumanValidationStatus
    reason: str


@dataclass(frozen=True)
class ReviewItem:
    classification: UrlClassification
    priority: int
    status: HumanValidationStatus
    history: tuple[ReviewDecision, ...] = ()


class AnactReviewQueue:
    """No persistence and no automatic human decision simulation."""

    def __init__(self) -> None:
        self._items: dict[str, ReviewItem] = {}

    def add(self, classification: UrlClassification, *, priority: int | None = None) -> bool:
        if classification.fingerprint in self._items:
            return False
        selected_priority = priority if priority is not None else self._default_priority(classification.decision)
        if selected_priority < 0:
            raise ValueError("priority must be non-negative")
        self._items[classification.fingerprint] = ReviewItem(
            classification,
            selected_priority,
            classification.human_validation_status,
        )
        return True

    def items(
        self,
        *,
        category: UrlCategory | None = None,
        region_id: str | None = None,
        status: HumanValidationStatus | None = None,
    ) -> tuple[ReviewItem, ...]:
        selected = (
            item
            for item in self._items.values()
            if (category is None or item.classification.category is category)
            and (region_id is None or item.classification.region_id == region_id)
            and (status is None or item.status is status)
        )
        return tuple(sorted(selected, key=lambda item: (item.priority, item.classification.fingerprint)))

    def accept(self, fingerprint: str, reason: str) -> ReviewItem:
        return self._record(fingerprint, HumanValidationStatus.ACCEPTED, reason)

    def reject(self, fingerprint: str, reason: str) -> ReviewItem:
        return self._record(fingerprint, HumanValidationStatus.REJECTED, reason)

    def request_recheck(self, fingerprint: str, reason: str) -> ReviewItem:
        return self._record(fingerprint, HumanValidationStatus.RECHECK_REQUESTED, reason)

    def _record(self, fingerprint: str, status: HumanValidationStatus, reason: str) -> ReviewItem:
        if not reason.strip():
            raise ValueError("a human decision reason is required")
        try:
            item = self._items[fingerprint]
        except KeyError as error:
            raise KeyError("unknown review item") from error
        decision = ReviewDecision(len(item.history) + 1, status, reason.strip())
        updated = replace(item, status=status, history=item.history + (decision,))
        self._items[fingerprint] = updated
        return updated

    @staticmethod
    def _default_priority(decision: ClassificationDecision) -> int:
        return {
            ClassificationDecision.HUMAN_REVIEW_REQUIRED: 10,
            ClassificationDecision.UNCLASSIFIED: 20,
            ClassificationDecision.AUTO_ACCEPTED: 30,
            ClassificationDecision.REJECTED: 40,
        }[decision]
