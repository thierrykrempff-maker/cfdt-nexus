"""Content-free, deterministic ingestion audit export."""

from __future__ import annotations

import json
from typing import Any

from .graph import DocumentGraph
from .ingestion_models import IngestionBatchResult, IssueSeverity


class IngestionAuditExporter:
    """Aggregate ingestion metrics without exposing source metadata values."""

    def build(
        self,
        batch: IngestionBatchResult,
        graph: DocumentGraph,
    ) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        for document in graph.documents():
            key = document.document_kind.value
            by_type[key] = by_type.get(key, 0) + 1
        return {
            "conflicts_detected": sum(
                issue.severity is IssueSeverity.ERROR for issue in batch.issues
            ),
            "documents_ingested": len(batch.results),
            "duplicates_detected": batch.duplicates,
            "issues": [
                {
                    "code": issue.code,
                    "decision": issue.decision.value,
                    "document_id": issue.document_id,
                    "severity": issue.severity.value,
                }
                for issue in batch.issues
            ],
            "nodes_created": batch.created,
            "nodes_updated": batch.updated,
            "relations_created": batch.relation_count,
            "rejected": batch.rejected,
            "statistics_by_document_type": dict(sorted(by_type.items())),
            "warnings": sum(
                issue.severity is IssueSeverity.WARNING for issue in batch.issues
            ),
        }

    def to_json(
        self,
        batch: IngestionBatchResult,
        graph: DocumentGraph,
    ) -> str:
        return json.dumps(
            self.build(batch, graph),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
