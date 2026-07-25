"""Transversal privacy gate for user input, output and technical traces."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .models import AssistantRequest, PrivacyDecision

_BLOCK_PATTERNS = (
    re.compile(r"\b[12]\d{12}\b"),
    re.compile(r"\bFR\d{2}(?:\s?[A-Z0-9]){23}\b", re.IGNORECASE),
)
_ANONYMIZE_PATTERNS = (
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"(?<!\d)(?:\+33|0)[1-9](?:[ .-]?\d{2}){4}(?!\d)"),
    re.compile(r"\b(?:matricule|identifiant\s+(?:kelio|nibelis|rh))\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\b(?:salaire|net à payer)\s*[:=]?\s*\d+(?:[.,]\d+)?\s*(?:€|euros?)", re.IGNORECASE),
)
_FORBIDDEN_OUTPUT = ("chunk_id", "storage_id", "local_path", "c:\\", "/home/", "/users/", "/tmp/")


@dataclass(frozen=True, slots=True)
class PrivacyAssessment:
    decision: PrivacyDecision
    sanitized_question: str
    codes: tuple[str, ...] = ()


class PrivacyGate:
    def assess(self, request: AssistantRequest) -> PrivacyAssessment:
        text = request.question
        for pattern in _BLOCK_PATTERNS:
            if pattern.search(text):
                return PrivacyAssessment(
                    PrivacyDecision.BLOCKED,
                    "Donnée sensible bloquée.",
                    ("SENSITIVE_IDENTIFIER_BLOCKED",),
                )
        sanitized = text
        changed = False
        for pattern in _ANONYMIZE_PATTERNS:
            sanitized, count = pattern.subn("<redacted>", sanitized)
            changed = changed or count > 0
        decision = PrivacyDecision.ANONYMIZE if changed else PrivacyDecision.ALLOWED
        return PrivacyAssessment(decision, sanitized, ("SENSITIVE_VALUE_REDACTED",) if changed else ())

    def public_output_is_safe(self, rendered: str) -> bool:
        lowered = rendered.lower()
        return not any(marker in lowered for marker in _FORBIDDEN_OUTPUT)
