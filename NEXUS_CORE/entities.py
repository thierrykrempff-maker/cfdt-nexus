"""Pseudonymous person and employment references."""

from __future__ import annotations

from dataclasses import dataclass

from .identifiers import EntityId
from .periods import Period
from .privacy import ConfidentialityLevel


@dataclass(frozen=True, slots=True)
class PersonReference:
    """A person represented only by a pseudonymous technical identifier."""

    person_id: EntityId
    confidentiality: ConfidentialityLevel = ConfidentialityLevel.CONFIDENTIAL


@dataclass(frozen=True, slots=True)
class EmployerReference:
    employer_id: EntityId


@dataclass(frozen=True, slots=True)
class EmploymentReference:
    employment_id: EntityId
    person: PersonReference
    employer: EmployerReference


@dataclass(frozen=True, slots=True)
class EmploymentPeriod:
    employment: EmploymentReference
    period: Period


@dataclass(frozen=True, slots=True)
class EntityReference:
    entity_id: EntityId
    entity_type: str
