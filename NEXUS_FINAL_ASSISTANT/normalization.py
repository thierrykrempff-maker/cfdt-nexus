"""Deterministic request normalization."""

from __future__ import annotations

import unicodedata

from .models import AssistantRequest, Fact


def normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(plain.lower().split())


def normalize_request(request: AssistantRequest) -> AssistantRequest:
    facts = tuple(
        Fact(" ".join(item.statement.split()), item.documented, item.source)
        for item in request.facts
        if item.statement.strip()
    )
    return AssistantRequest(
        question=" ".join(request.question.split()),
        context=tuple(sorted(set(request.context))),
        user_type=request.user_type.strip().lower() or "employee",
        union_role=request.union_role.strip() if request.union_role else None,
        collective_case=request.collective_case,
        facts=facts,
        available_documents=tuple(dict.fromkeys(request.available_documents)),
        period=request.period,
        declared_urgency=request.declared_urgency,
        expected_output=request.expected_output,
        requested_detail=request.requested_detail,
        allowed_engines=tuple(dict.fromkeys(request.allowed_engines)),
        prohibited_data=tuple(dict.fromkeys(request.prohibited_data)),
        confidential_mode=request.confidential_mode,
        history_available=request.history_available,
        route_domains=tuple(dict.fromkeys(request.route_domains)),
    )
