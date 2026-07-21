"""Deterministic Career Reconstruction Engine producing proposals only."""

from __future__ import annotations

from dataclasses import fields, replace
from datetime import date

from .career_evidence_models import EvidenceBundle, EvidenceStatus
from .career_import_engine import CareerImportEngine
from .career_import_models import (
    ImportBatch,
    ImportedCareerRecord,
    ImportedEmploymentPeriod,
)
from .career_reconstruction_matcher import CareerReconstructionMatcher
from .career_reconstruction_merger import CareerReconstructionMerger
from .career_reconstruction_models import (
    DatePrecision,
    HumanValidationRequirement,
    ReconstructionCandidate,
    ReconstructionConflict,
    ReconstructionConflictType,
    ReconstructionContext,
    ReconstructionDate,
    ReconstructionDecision,
    ReconstructionGap,
    ReconstructionMatch,
    ReconstructionMatchType,
    ReconstructionMerge,
    ReconstructionProposal,
    ReconstructionRecord,
    ReconstructionReport,
    ReconstructionReportView,
    ReconstructionRequest,
    ReconstructionStatus,
    ReconstructedCareerEvent,
    ReconstructedCareerPeriod,
)
from .career_reconstruction_report import CareerReconstructionReportBuilder
from .career_reconstruction_validator import CareerReconstructionValidator


class CareerReconstructionEngine:
    """Build distinct proposals without mutating Timeline or Evidence inputs."""

    def __init__(
        self,
        matcher: CareerReconstructionMatcher | None = None,
        merger: CareerReconstructionMerger | None = None,
        validator: CareerReconstructionValidator | None = None,
        report_builder: CareerReconstructionReportBuilder | None = None,
    ) -> None:
        self._matcher = matcher or CareerReconstructionMatcher()
        self._merger = merger or CareerReconstructionMerger()
        self._validator = validator or CareerReconstructionValidator()
        self._report_builder = report_builder or CareerReconstructionReportBuilder()

    def create_reconstruction_context(
        self,
        context_id: str,
        request: ReconstructionRequest,
        existing_timeline=None,
        existing_evidence=None,
    ) -> ReconstructionContext:
        return ReconstructionContext(context_id, request, (), existing_timeline, existing_evidence)

    def add_import_batch(
        self, context: ReconstructionContext, batch: ImportBatch
    ) -> ReconstructionContext:
        return replace(context, import_batches=context.import_batches + (batch,))

    def build_candidates(
        self, context: ReconstructionContext
    ) -> tuple[ReconstructionCandidate, ...]:
        records = self._records(context)
        return tuple(
            ReconstructionCandidate(
                f"candidate:{left.record_id}:{right.record_id}",
                left.record_id,
                right.record_id,
            )
            for index, left in enumerate(records)
            for right in records[index + 1 :]
            if left.record_type == right.record_type
        )

    def match_records(
        self, context: ReconstructionContext
    ) -> tuple[ReconstructionMatch, ...]:
        records = {item.record_id: item for item in self._records(context)}
        return tuple(
            self._matcher.match(records[item.left_record_id], records[item.right_record_id])
            for item in self.build_candidates(context)
        )

    def merge_compatible_records(
        self, context: ReconstructionContext
    ) -> tuple[ReconstructionMerge, ...]:
        records = {item.record_id: item for item in self._records(context)}
        results = []
        for match in self.match_records(context):
            if match.match_type in {
                ReconstructionMatchType.NO_MATCH,
                ReconstructionMatchType.CONTRADICTORY_SOURCE,
            }:
                continue
            merge, _ = self._merger.merge(tuple(records[item] for item in match.record_ids))
            results.append(merge)
        return tuple(results)

    def detect_conflicts(
        self, context: ReconstructionContext
    ) -> tuple[ReconstructionConflict, ...]:
        records = {item.record_id: item for item in self._records(context)}
        conflicts: list[ReconstructionConflict] = []
        for match in self.match_records(context):
            pair = tuple(records[item] for item in match.record_ids)
            _, merge_conflicts = self._merger.merge(pair)
            conflicts.extend(merge_conflicts)
            if match.match_type is ReconstructionMatchType.POSSIBLE_DUPLICATE:
                conflicts.append(
                    ReconstructionConflict(
                        f"duplicate:{':'.join(match.record_ids)}",
                        ReconstructionConflictType.DUPLICATE_CONFLICT,
                        match.record_ids,
                        (),
                        tuple(item for record in pair for item in record.provenance),
                        "Possible duplicate retained for human review.",
                    )
                )
        return tuple(dict.fromkeys(conflicts))

    def detect_gaps(self, context: ReconstructionContext) -> tuple[ReconstructionGap, ...]:
        records = self._records(context)
        gaps: list[ReconstructionGap] = []
        for record in records:
            values = dict(record.values)
            for key, gap_type, description in (
                ("employer", "MISSING_EMPLOYER", "Period without an identified employer."),
                ("end_date", "MISSING_END_DATE", "Period without an end date."),
                ("classification", "MISSING_CLASSIFICATION", "Classification is missing."),
                ("schedule", "UNKNOWN_SCHEDULE", "Work schedule is unknown."),
            ):
                if key in values and self._unknown(values[key]):
                    gaps.append(ReconstructionGap(f"gap:{record.record_id}:{key}", gap_type, (record.record_id,), description))
            if values.get("night_work") is True and values.get("night_work_confirmed") is not True:
                gaps.append(ReconstructionGap(f"gap:{record.record_id}:night", "UNCONFIRMED_NIGHT_WORK", (record.record_id,), "Night work remains unconfirmed."))
            if values.get("five_shift") is True and values.get("five_shift_confirmed") is not True:
                gaps.append(ReconstructionGap(f"gap:{record.record_id}:five-shift", "UNCONFIRMED_FIVE_SHIFT", (record.record_id,), "Five-shift work remains unconfirmed."))
        periods = sorted(
            (record for record in records if record.record_type == "ImportedEmploymentPeriod"),
            key=lambda item: self._exact_date(dict(item.values).get("start_date")) or date.max,
        )
        for left, right in zip(periods, periods[1:]):
            left_end = self._exact_date(dict(left.values).get("end_date"))
            right_start = self._exact_date(dict(right.values).get("start_date"))
            if left_end and right_start and (right_start - left_end).days > 1:
                gaps.append(ReconstructionGap(f"gap:chronology:{left.record_id}:{right.record_id}", "UNEXPLAINED_INTERRUPTION", (left.record_id, right.record_id), "An unexplained interval exists between declared periods."))
        return tuple(gaps)

    def build_reconstruction_proposal(
        self, context: ReconstructionContext
    ) -> ReconstructionProposal:
        records = self._records(context)
        matches = self.match_records(context)
        merges = self.merge_compatible_records(context)
        conflicts = self.detect_conflicts(context)
        gaps = self.detect_gaps(context)
        events = self.prepare_timeline_proposal(context)
        evidence = self.prepare_evidence_proposal(context)
        decisions = tuple(
            ReconstructionDecision(f"decision:{index}", subject_id, "Confirm or reject the proposed reconstruction item.")
            for index, subject_id in enumerate(
                tuple(item.conflict_id for item in conflicts)
                + tuple(item.gap_id for item in gaps)
                + tuple(item.proposal_id for item in events),
                1,
            )
        )
        requirement = HumanValidationRequirement(
            "human-validation-1",
            "Every reconstruction proposal requires explicit human validation.",
            tuple(item.decision_id for item in decisions),
        )
        status = ReconstructionStatus.CONFLICTED if conflicts else ReconstructionStatus.REQUIRES_HUMAN_VALIDATION
        proposal = ReconstructionProposal(
            f"proposal:{context.context_id}",
            status,
            records,
            matches,
            merges,
            events,
            self._period_proposals(records),
            evidence,
            conflicts,
            gaps,
            decisions,
            requirement,
        )
        validation_issues = self._validator.validate(proposal)
        if validation_issues:
            raise ValueError("; ".join(validation_issues))
        return proposal

    def prepare_timeline_proposal(
        self, context: ReconstructionContext
    ) -> tuple[ReconstructedCareerEvent, ...]:
        events = []
        for record in self._records(context):
            values = dict(record.values)
            event_type = values.get("career_event_type")
            if not event_type:
                continue
            events.append(
                ReconstructedCareerEvent(
                    f"event-proposal:{record.record_id}",
                    str(event_type),
                    self._as_date(values.get("start_date")),
                    self._as_date(values.get("end_date")),
                    str(values.get("description") or "Proposed synthetic career event"),
                    record.provenance,
                )
            )
        return tuple(events)

    def prepare_evidence_proposal(self, context: ReconstructionContext) -> EvidenceBundle:
        batches = context.import_batches
        evidence = tuple(
            replace(item, status=EvidenceStatus.UNVERIFIED)
            for batch in batches
            for item in CareerImportEngine().prepare_evidence_records(batch).evidence
        )
        return EvidenceBundle(
            f"evidence-proposal:{context.context_id}",
            evidence=evidence,
            synthetic_only=all(batch.synthetic_only for batch in batches),
        )

    def generate_reconstruction_report(
        self,
        context: ReconstructionContext,
        proposal: ReconstructionProposal,
        view: ReconstructionReportView,
    ) -> ReconstructionReport:
        return self._report_builder.build(context, proposal, view)

    def _records(self, context: ReconstructionContext) -> tuple[ReconstructionRecord, ...]:
        return tuple(self._to_record(record) for batch in context.import_batches for record in batch.records)

    def _to_record(self, record) -> ReconstructionRecord:
        if isinstance(record, ImportedCareerRecord):
            values = (("career_event_type", record.career_event_type),) + tuple(
                (key, self._date_if_needed(key, value)) for key, value in record.original_values
            )
        else:
            values = tuple(
                (field.name, self._date_if_needed(field.name, getattr(record, field.name)))
                for field in fields(record)
                if field.name not in {"record_id", "evidence_id", "provenance"}
                and isinstance(getattr(record, field.name), (str, bool, type(None)))
            )
        return ReconstructionRecord(
            record.record_id,
            type(record).__name__,
            values,
            record,
            (record.provenance,),
        )

    def _period_proposals(self, records):
        return tuple(
            ReconstructedCareerPeriod(
                f"period-proposal:{record.record_id}",
                dict(record.values).get("employer"),
                self._as_date(dict(record.values).get("start_date")),
                self._as_date(dict(record.values).get("end_date")),
                record.provenance,
            )
            for record in records
            if record.record_type == "ImportedEmploymentPeriod"
        )

    @staticmethod
    def _date_if_needed(key, value):
        if not key.endswith("_date"):
            return value
        if value is None:
            return ReconstructionDate(None, DatePrecision.UNKNOWN)
        if len(value) == 4 and value.isdigit():
            return ReconstructionDate(value, DatePrecision.YEAR_ONLY, f"{value}-01-01", f"{value}-12-31")
        if len(value) == 7:
            return ReconstructionDate(value, DatePrecision.MONTH_ONLY)
        try:
            date.fromisoformat(value)
            return ReconstructionDate(value, DatePrecision.EXACT, value, value)
        except ValueError:
            return ReconstructionDate(value, DatePrecision.APPROXIMATE)

    @staticmethod
    def _as_date(value):
        return value if isinstance(value, ReconstructionDate) else ReconstructionDate(None, DatePrecision.UNKNOWN)

    @staticmethod
    def _unknown(value):
        return value is None or (
            isinstance(value, ReconstructionDate)
            and value.precision is DatePrecision.UNKNOWN
        )

    @staticmethod
    def _exact_date(value):
        if not isinstance(value, ReconstructionDate) or value.precision is not DatePrecision.EXACT or not value.value:
            return None
        return date.fromisoformat(value.value)
