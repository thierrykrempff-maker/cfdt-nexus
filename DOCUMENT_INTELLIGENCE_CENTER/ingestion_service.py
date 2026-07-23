"""Controlled, idempotent ingestion into the documentary graph."""

from __future__ import annotations

from collections.abc import Iterable

from .graph import DocumentGraph, DocumentGraphError
from .ingestion_models import (
    AgreementMetadataInput,
    DocumentMetadataInput,
    IngestionBatchResult,
    IngestionDecision,
    IngestionIssue,
    IngestionResult,
    IssueSeverity,
    MeetingMinutesMetadataInput,
)
from .metadata_index import MetadataIndex, MetadataQuery
from .models import (
    DocumentDescriptor,
    DocumentKind,
    DocumentRelation,
    RelationKind,
)
from .versioning import AgreementVersionManager


IngestionInput = (
    DocumentMetadataInput | AgreementMetadataInput | MeetingMinutesMetadataInput
)


def _issue(
    code: str,
    severity: IssueSeverity,
    document_id: str | None,
    decision: IngestionDecision,
    graph_state: str,
) -> IngestionIssue:
    descriptions = {
        "DUPLICATE_METADATA": "Equivalent metadata already exists.",
        "DOCUMENT_TYPE_CONFLICT": "The stable identity has a conflicting type.",
        "AGREEMENT_VERSION_DATE_CONFLICT": (
            "An agreement version has contradictory dates."
        ),
        "AGREEMENT_STATUS_CONFLICT": (
            "An agreement version has contradictory statuses."
        ),
        "RELATION_TARGET_MISSING": "An explicit relation target is unknown.",
        "RELATION_INCOMPATIBLE": "The explicit relation is incompatible.",
        "AGREEMENT_PARENT_INCONSISTENT": (
            "The agreement parent belongs to another family."
        ),
        "AGREEMENT_VERSION_CYCLE": "The relation creates a version cycle.",
        "SOURCE_METADATA_WARNING": "The source reported a metadata quality warning.",
    }
    return IngestionIssue(
        code=code,
        description=descriptions[code],
        severity=severity,
        document_id=document_id,
        decision=decision,
        graph_state=graph_state,
    )


class DocumentIngestionService:
    """Validate, deduplicate and ingest documentary metadata."""

    def __init__(
        self,
        graph: DocumentGraph | None = None,
        index: MetadataIndex | None = None,
    ) -> None:
        self.graph = graph or DocumentGraph()
        self.index = index or MetadataIndex(self.graph.documents())

    def ingest(self, value: IngestionInput) -> IngestionResult:
        return self.ingest_batch((value,)).results[0]

    def ingest_batch(
        self,
        values: Iterable[IngestionInput],
    ) -> IngestionBatchResult:
        normalized = tuple(self._normalize(value) for value in values)
        results: list[IngestionResult] = []
        accepted_inputs: dict[str, DocumentMetadataInput] = {}
        self.index.replace_all(self.graph.documents())

        for item in normalized:
            descriptor = self._descriptor(item)
            current = self.graph.find_document(descriptor.document_id)
            conflict = self._metadata_conflict(descriptor, current)
            if conflict is not None:
                results.append(
                    IngestionResult(
                        descriptor.document_id,
                        IngestionDecision.REJECTED,
                        issues=(conflict,),
                    )
                )
                continue
            duplicate = self.index.find_duplicate(descriptor)
            if duplicate is not None:
                results.append(
                    IngestionResult(
                        descriptor.document_id,
                        IngestionDecision.DUPLICATE,
                        issues=(
                            _issue(
                                "DUPLICATE_METADATA",
                                IssueSeverity.WARNING,
                                descriptor.document_id,
                                IngestionDecision.DUPLICATE,
                                "UNCHANGED",
                            ),
                        ),
                    )
                )
                continue
            if current == descriptor:
                results.append(
                    IngestionResult(
                        descriptor.document_id,
                        IngestionDecision.DUPLICATE,
                        issues=self._quality_issues(
                            item,
                            IngestionDecision.DUPLICATE,
                        ),
                    )
                )
                accepted_inputs[descriptor.document_id] = item
                continue
            if current is None:
                self.graph.add_document(descriptor)
                decision = IngestionDecision.CREATED
            else:
                self.graph.replace_document(descriptor)
                decision = IngestionDecision.UPDATED
            self.index.replace_all(self.graph.documents())
            accepted_inputs[descriptor.document_id] = item
            results.append(
                IngestionResult(
                    descriptor.document_id,
                    decision,
                    issues=self._quality_issues(item, decision),
                )
            )

        enriched: list[IngestionResult] = []
        for result in results:
            item = (
                accepted_inputs.get(result.document_id)
                if result.document_id is not None
                else None
            )
            if item is None:
                enriched.append(result)
                continue
            relation_count, relation_issues = self._ingest_relations(item)
            enriched.append(
                IngestionResult(
                    document_id=result.document_id,
                    decision=result.decision,
                    created_relations=relation_count,
                    issues=result.issues + relation_issues,
                )
            )
        return IngestionBatchResult(tuple(enriched))

    @staticmethod
    def _normalize(value: IngestionInput) -> DocumentMetadataInput:
        if isinstance(value, DocumentMetadataInput):
            return value
        if isinstance(value, AgreementMetadataInput):
            return value.to_document_input()
        if isinstance(value, MeetingMinutesMetadataInput):
            return value.to_document_input()
        raise TypeError("unsupported ingestion input")

    @staticmethod
    def _descriptor(item: DocumentMetadataInput) -> DocumentDescriptor:
        return DocumentDescriptor(
            document_id=item.pseudonymous_id,
            title=item.normalized_title,
            document_kind=item.document_kind,
            provenance=item.logical_provenance,
            publication_date=item.document_date,
            effective_from=item.effective_from,
            effective_to=item.effective_to,
            version_label=item.version,
            family=item.family,
            instance=item.instance,
            nature=item.nature,
            agreement_reference=item.agreement_reference,
            status=item.status.value,
            topics=item.topics,
            referenced_document_ids=tuple(
                link.target_document_id for link in item.explicit_links
            ),
        )

    def _metadata_conflict(
        self,
        descriptor: DocumentDescriptor,
        current: DocumentDescriptor | None,
    ) -> IngestionIssue | None:
        if current is not None and current.document_kind is not descriptor.document_kind:
            return _issue(
                "DOCUMENT_TYPE_CONFLICT",
                IssueSeverity.ERROR,
                descriptor.document_id,
                IngestionDecision.REJECTED,
                "UNCHANGED",
            )
        if descriptor.document_kind is not DocumentKind.AGREEMENT:
            return None
        if current is not None:
            if (
                current.version_label == descriptor.version_label
                and current.publication_date
                and descriptor.publication_date
                and current.publication_date != descriptor.publication_date
            ):
                return _issue(
                    "AGREEMENT_VERSION_DATE_CONFLICT",
                    IssueSeverity.ERROR,
                    descriptor.document_id,
                    IngestionDecision.REJECTED,
                    "UNCHANGED",
                )
            if {current.status, descriptor.status} == {"ACTIVE", "REPLACED"}:
                return _issue(
                    "AGREEMENT_STATUS_CONFLICT",
                    IssueSeverity.ERROR,
                    descriptor.document_id,
                    IngestionDecision.REJECTED,
                    "UNCHANGED",
                )
        same_version = self.index.find(
            MetadataQuery(
                document_kind=DocumentKind.AGREEMENT,
                family=descriptor.family,
                version=descriptor.version_label,
            )
        )
        for other in same_version:
            if other.document_id == descriptor.document_id:
                continue
            if (
                other.publication_date
                and descriptor.publication_date
                and other.publication_date != descriptor.publication_date
            ):
                return _issue(
                    "AGREEMENT_VERSION_DATE_CONFLICT",
                    IssueSeverity.ERROR,
                    descriptor.document_id,
                    IngestionDecision.REJECTED,
                    "UNCHANGED",
                )
            if {other.status, descriptor.status} == {"ACTIVE", "REPLACED"}:
                return _issue(
                    "AGREEMENT_STATUS_CONFLICT",
                    IssueSeverity.ERROR,
                    descriptor.document_id,
                    IngestionDecision.REJECTED,
                    "UNCHANGED",
                )
        return None

    @staticmethod
    def _quality_issues(
        item: DocumentMetadataInput,
        decision: IngestionDecision,
    ) -> tuple[IngestionIssue, ...]:
        return tuple(
            _issue(
                "SOURCE_METADATA_WARNING",
                IssueSeverity.WARNING,
                item.pseudonymous_id,
                decision,
                "NODE_INGESTED_WITH_WARNING",
            )
            for _warning in item.quality_warnings
        )

    def _ingest_relations(
        self,
        item: DocumentMetadataInput,
    ) -> tuple[int, tuple[IngestionIssue, ...]]:
        created = 0
        issues: list[IngestionIssue] = []
        for link in item.explicit_links:
            target = self.graph.find_document(link.target_document_id)
            if target is None:
                issues.append(
                    _issue(
                        "RELATION_TARGET_MISSING",
                        IssueSeverity.ERROR,
                        item.pseudonymous_id,
                        IngestionDecision.REJECTED,
                        "NODE_PRESERVED_WITHOUT_RELATION",
                    )
                )
                continue
            source = self.graph.find_document(item.pseudonymous_id)
            if source is None:
                continue
            compatibility = self._relation_compatibility(
                source,
                target,
                link.relation_kind,
            )
            if compatibility is not None:
                issues.append(compatibility)
                continue
            relation = DocumentRelation(
                source_document_id=source.document_id,
                target_document_id=target.document_id,
                relation_kind=link.relation_kind,
                provenance=source.provenance,
                confidence=item.confidence,
            )
            if relation.relation_id in {
                existing.relation_id for existing in self.graph.relations()
            }:
                continue
            try:
                self._validate_version_cycle(relation, source.family)
                self.graph.add_relation(relation)
            except DocumentGraphError:
                issues.append(
                    _issue(
                        "AGREEMENT_VERSION_CYCLE",
                        IssueSeverity.ERROR,
                        source.document_id,
                        IngestionDecision.REJECTED,
                        "NODE_PRESERVED_WITHOUT_RELATION",
                    )
                )
                continue
            created += 1
        return created, tuple(issues)

    @staticmethod
    def _relation_compatibility(
        source: DocumentDescriptor,
        target: DocumentDescriptor,
        relation_kind: RelationKind,
    ) -> IngestionIssue | None:
        if relation_kind in (RelationKind.SUPERSEDES, RelationKind.AMENDS):
            if (
                source.document_kind is not DocumentKind.AGREEMENT
                or target.document_kind is not DocumentKind.AGREEMENT
            ):
                return _issue(
                    "RELATION_INCOMPATIBLE",
                    IssueSeverity.ERROR,
                    source.document_id,
                    IngestionDecision.REJECTED,
                    "NODE_PRESERVED_WITHOUT_RELATION",
                )
            if source.family != target.family:
                return _issue(
                    "AGREEMENT_PARENT_INCONSISTENT",
                    IssueSeverity.ERROR,
                    source.document_id,
                    IngestionDecision.REJECTED,
                    "NODE_PRESERVED_WITHOUT_RELATION",
                )
        return None

    def _validate_version_cycle(
        self,
        relation: DocumentRelation,
        family: str | None,
    ) -> None:
        if relation.relation_kind not in (
            RelationKind.SUPERSEDES,
            RelationKind.AMENDS,
        ):
            return
        candidate = DocumentGraph(
            self.graph.documents(),
            self.graph.relations() + (relation,),
        )
        if family is not None:
            AgreementVersionManager(candidate).describe_family(family)
