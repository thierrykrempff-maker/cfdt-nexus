"""Explicit Career Reconstruction projections to Nexus Core career concepts."""

from __future__ import annotations

from RETIREMENT_PENIBILITY_ENGINE.career_reconstruction_models import ReconstructionProposal
from NEXUS_CORE import (
    EmployerReference, EmploymentPeriod, EmploymentReference, EntityId, EntityReference,
    Period, PersonReference,
)

from ._identity import stable_retirement_id
from .metadata import RetirementMetadataMapper


class RetirementCareerMapper:
    """Convert only complete proposed periods; never infer missing dates."""

    def __init__(self, metadata: RetirementMetadataMapper | None = None) -> None:
        self._metadata = metadata or RetirementMetadataMapper()

    def map(self, proposal: ReconstructionProposal | None,
            subject: EntityReference) -> tuple[EmploymentPeriod, ...]:
        if proposal is None:
            return ()
        person = PersonReference(EntityId(stable_retirement_id("person", subject.entity_id.value)))
        periods = []
        for item in proposal.proposed_periods:
            start = self._metadata.parse_date(item.start_date.value)
            end = self._metadata.parse_date(item.end_date.value)
            if start is None:
                continue
            employer_key = item.employer or "unknown_employer"
            employment = EmploymentReference(
                EntityId(stable_retirement_id("employment", item.proposal_id)),
                person,
                EmployerReference(EntityId(stable_retirement_id("employer", employer_key))),
            )
            periods.append(EmploymentPeriod(employment, Period(start, end)))
        return tuple(periods)
