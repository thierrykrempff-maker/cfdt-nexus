"""Audience-safe reports for proposed career reconstructions."""

from __future__ import annotations

from .career_reconstruction_models import (
    ReconstructionContext,
    ReconstructionProposal,
    ReconstructionReport,
    ReconstructionReportView,
    ReconstructionSummary,
)


class CareerReconstructionReportBuilder:
    """Render deterministic summaries without exposing document content."""

    def build(
        self,
        context: ReconstructionContext,
        proposal: ReconstructionProposal,
        view: ReconstructionReportView,
    ) -> ReconstructionReport:
        summary = ReconstructionSummary(
            proposal.proposal_id,
            proposal.status,
            tuple(item.proposal_id for item in proposal.proposed_periods),
            tuple(item.proposal_id for item in proposal.proposed_events),
            tuple(item.conflict_id for item in proposal.conflicts),
            tuple(item.gap_id for item in proposal.gaps),
            True,
        )
        common = dict(
            view=view,
            summary=summary,
            proposed_periods=tuple(
                self._safe(f"{item.employer or 'Employeur non precise'}: {item.start_date.value or '?'} - {item.end_date.value or '?'}")
                for item in proposal.proposed_periods
            ),
            recognized_information=tuple(
                self._safe(f"{record.record_type}: {record.record_id}")
                for record in proposal.records
            ),
            uncertain_information=tuple(self._safe(item.description) for item in proposal.gaps),
            contradictions=tuple(self._safe(item.description) for item in proposal.conflicts),
            missing_documents=tuple(self._safe(item.description) for item in proposal.gaps),
            questions_to_confirm=tuple(self._safe(item.question) for item in proposal.human_decisions),
            next_steps=("Faire verifier chaque proposition par une personne habilitee.",),
            warnings=("Chronologie proposee uniquement; aucune donnee n'est automatiquement validee.",),
        )
        if view is ReconstructionReportView.EMPLOYEE_VIEW:
            return ReconstructionReport(**common)
        return ReconstructionReport(
            **common,
            imported_sources=tuple(
                dict.fromkeys(
                    self._safe(source.source_id)
                    for batch in context.import_batches
                    for record in batch.records
                    for source in (record.provenance,)
                )
            ),
            provenance=tuple(
                dict.fromkeys(
                    self._safe(source.origin)
                    for record in proposal.records
                    for source in record.provenance
                )
            ),
            matches=tuple(
                self._safe(
                    f"{item.match_type.value}; commun={','.join(item.matching_criteria) or '-'}; "
                    f"divergent={','.join(item.divergent_criteria) or '-'}"
                )
                for item in proposal.matches
            ),
            proposed_merges=tuple(
                self._safe(f"{item.status.value}: {','.join(item.source_record_ids)}")
                for item in proposal.merges
            ),
            confidence_levels=tuple(item.confidence.value for item in proposal.matches),
            timeline_proposal=tuple(item.proposal_id for item in proposal.proposed_events),
            evidence_proposal=tuple(str(item.reference.evidence_id) for item in proposal.proposed_evidence.evidence),
        )

    @staticmethod
    def _safe(value: str) -> str:
        """Redact strings resembling secrets, paths or medical detail."""
        lowered = value.lower()
        forbidden = ("password", "token=", "secret=", "c:\\", "/home/", "diagnostic medical")
        return "[information protegee]" if any(marker in lowered for marker in forbidden) else value
