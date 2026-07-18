"""Traceable statements used to separate facts from unverified material."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .enums import StatementKind
from .serialization import contract_to_dict, freeze_metadata, reject_unknown_fields, require_text


@dataclass(frozen=True)
class Statement:
    statement_id: str
    text: str
    kind: StatementKind
    evidence_ids: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "statement_id", require_text(self.statement_id, "statement_id"))
        object.__setattr__(self, "text", require_text(self.text, "text"))
        if not isinstance(self.kind, StatementKind):
            raise TypeError("kind must be a StatementKind")
        object.__setattr__(self, "evidence_ids", tuple(require_text(item, "evidence_id") for item in self.evidence_ids))
        object.__setattr__(self, "metadata", freeze_metadata(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return contract_to_dict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Statement":
        allowed = {"statement_id", "text", "kind", "evidence_ids", "metadata"}
        reject_unknown_fields(value, allowed, "Statement")
        return cls(
            statement_id=str(value.get("statement_id", "")),
            text=str(value.get("text", "")),
            kind=StatementKind(value.get("kind")),
            evidence_ids=tuple(value.get("evidence_ids") or ()),
            metadata=value.get("metadata") or {},
        )
