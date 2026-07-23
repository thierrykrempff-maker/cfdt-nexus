"""Regression tests for pseudonymous Runtime identifiers at the Core privacy boundary."""

from __future__ import annotations

import pytest

from NEXUS_CORE import (
    AnalysisId,
    ConflictId,
    CorrelationId,
    DocumentId,
    EntityId,
    EvidenceId,
    FindingId,
    RecommendationId,
)


IDENTIFIER_TYPES = (
    EntityId,
    CorrelationId,
    AnalysisId,
    DocumentId,
    EvidenceId,
    FindingId,
    RecommendationId,
    ConflictId,
)

HASHED_RUNTIME_IDENTIFIERS = (
    "runtime-subject-abcdef1234567890abcdef12",
    "runtime-document-a1234567890bcdef1234567f",
    "runtime-evidence-12abcdef1234567890abcdef",
)

DIRECT_SENSITIVE_IDENTIFIERS = (
    "299129999999901",
    "FR7630006000011234567890189",
    "person@example.invalid",
    "runtime-subject-299129999999901",
)


@pytest.mark.parametrize("identifier_type", IDENTIFIER_TYPES)
@pytest.mark.parametrize("value", HASHED_RUNTIME_IDENTIFIERS)
def test_explicit_runtime_hashes_are_accepted(identifier_type, value):
    assert identifier_type(value).value == value


@pytest.mark.parametrize("identifier_type", IDENTIFIER_TYPES)
@pytest.mark.parametrize("value", DIRECT_SENSITIVE_IDENTIFIERS)
def test_direct_sensitive_identifiers_remain_blocked(identifier_type, value):
    with pytest.raises(ValueError, match="personal data"):
        identifier_type(value)


@pytest.mark.parametrize(
    "value",
    (
        "runtime-subject-123456789012345678901234",
        "runtime-299129999999901-abcdef1234567890abcdef12",
        "runtime-subject-abcdef1234567890abcdef1",
    ),
)
def test_lookalikes_without_a_valid_pseudonymous_hash_remain_blocked(value):
    with pytest.raises(ValueError, match="personal data"):
        EntityId(value)
