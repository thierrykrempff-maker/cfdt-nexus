from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from SYNDICAL_REASONING_ENGINE.cse_models import MeetingBody, PVSearchQuery
from SYNDICAL_REASONING_ENGINE.legal_issue_models import (
    IssueCategory,
    LegalIssue,
    PlanningStatus,
    ResearchPlan,
    ResearchQuery,
    ResearchTarget,
    SourceFamily,
)


def row(
    *,
    document_id: str,
    chunk_index: int,
    text: str,
    instance: str = "CSE",
    meeting_date: str | None = "2024-04-18",
    kind: str = "proces-verbal",
    path: str = "PV CSE/Sarralbe/PV 2024-04-18.pdf",
    pages: tuple[int, ...] = (7,),
    indexable: bool = True,
) -> dict[str, object]:
    return {
        "chunk_id": f"{document_id}-chunk-{chunk_index}",
        "document_id": document_id,
        "source_relative_path": path,
        "source_sha256": f"sha-{document_id}",
        "chunk_index": chunk_index,
        "chunk_count": 1,
        "text": text,
        "text_length_chars": len(text),
        "unique_text_length_chars": len(text),
        "page_numbers": list(pages),
        "metadata_snapshot": {
            "meeting_date": {"value": meeting_date, "confidence_level": "high"},
            "instance": {"value": instance, "confidence_level": "high"},
            "meeting_type": {"value": "ordinaire", "confidence_level": "high"},
            "document_kind": {"value": kind, "confidence_level": "high"},
            "title": {"value": f"PV {instance} du {meeting_date}", "confidence_level": "high"},
        },
        "document_quality_level": "good",
        "warnings": [],
        "created_at": "2024-04-19T08:00:00+00:00",
        "chunking_version": "1.0",
        "indexable": indexable,
    }


def corpus(tmp_path: Path) -> Path:
    root = tmp_path / "processed"
    chunks = root / "chunks"
    chunks.mkdir(parents=True)
    rows = [
        row(
            document_id="cse-pause",
            chunk_index=0,
            text=(
                "Les élus demandent comment sont décomptées les pauses cigarette au "
                "tourniquet. La direction répond que le badgeage sert au contrôle du "
                "temps et qu’un rappel de consigne sera présenté."
            ),
        ),
        row(
            document_id="cse-shift",
            chunk_index=0,
            text=(
                "Le CSE examine la réorganisation du laboratoire et le passage du "
                "personnel de jour en personnel posté. La direction informe les élus "
                "que les effectifs et les horaires seront réexaminés."
            ),
            meeting_date="2025-02-11",
            path="PV CSE/Sarralbe/PV 2025-02-11.pdf",
        ),
        row(
            document_id="cssct-epi",
            chunk_index=0,
            text=(
                "Les membres de la CSSCT demandent si le stock de gants, lunettes et "
                "visières est adapté au risque chimique. La direction répond qu’une "
                "analyse des EPI et du DUERP sera réalisée."
            ),
            instance="CSSCT",
            meeting_date="2024-06-20",
            path="PV CSSCT/Sarralbe/PV CSSCT 2024-06-20.pdf",
        ),
        row(
            document_id="ce-procedure",
            chunk_index=0,
            text=(
                "La direction indique qu’une procédure chimique mise à jour doit être "
                "validée puis diffusée. Le comité demande le numéro de version."
            ),
            instance="CE",
            meeting_date="2019-03-12",
            path="PV CE/Sarralbe/PV CE 2019-03-12.pdf",
        ),
        row(
            document_id="other-site",
            chunk_index=0,
            text="La direction répond sur le badgeage et les pauses du site de Tavaux.",
            path="PV CSE/Tavaux/PV 2024-04-18.pdf",
        ),
        row(
            document_id="annex",
            chunk_index=0,
            text="Support préparatoire : tableau des horaires et des effectifs projetés.",
            kind="annexe",
            path="PV CSE/Sarralbe/Annexe horaires 2024.pdf",
        ),
    ]
    with (chunks / "corpus.jsonl").open("w", encoding="utf-8") as stream:
        for item in rows:
            stream.write(json.dumps(item, ensure_ascii=False) + "\n")
    return root


def pv_query(
    *concepts: str,
    query_id: str = "query-1",
    issue_id: str = "issue-1",
    case_id: str = "case-a",
    bodies: tuple[MeetingBody, ...] = (MeetingBody.CSE, MeetingBody.CE),
    establishment: str = "Sarralbe",
    temporal: str = "2018-2026",
    blocked: bool = False,
    negative_terms: tuple[str, ...] = (),
) -> PVSearchQuery:
    return PVSearchQuery(
        query_id,
        issue_id,
        "target-1",
        case_id,
        tuple(concepts),
        (),
        (),
        negative_terms,
        temporal,
        bodies,
        establishment,
        ("PV",),
        0.2,
        8,
        "Retrouver un précédent interne pertinent.",
        blocked,
        "Recherche déterminée par les faits.",
    )


def research_query(
    *,
    family: SourceFamily = SourceFamily.CSE_MINUTES,
    concepts: tuple[str, ...] = ("pause", "badgeage"),
    status: PlanningStatus = PlanningStatus.READY,
) -> tuple[ResearchQuery, ResearchTarget]:
    query = ResearchQuery(
        "query-1",
        "issue-1",
        "target-1",
        "pauses badgeage tourniquet",
        concepts,
        ("fait-1",),
        "2018-2026",
        "Sarralbe",
        "salariés",
        ("PV",),
        "passage daté",
        "extrait exact",
        (),
        1,
        False,
        "Recherche contextuelle.",
        status,
    )
    target = ResearchTarget(
        "target-1",
        "issue-1",
        family,
        7,
        "Rechercher un précédent interne.",
        False,
        "PV",
        "passage exact",
        True,
        (),
    )
    return query, target


def plan(*, blocked: bool = False) -> ResearchPlan:
    query, target = research_query(
        status=PlanningStatus.BLOCKED_BY_MISSING_FACTS if blocked else PlanningStatus.READY
    )
    issue = LegalIssue(
        "issue-1",
        "case-a",
        "Pauses et badgeage",
        "Quelle pratique antérieure est documentée ?",
        IssueCategory.EMPLOYEE_MONITORING,
        ("fait-1",),
        (),
        ("missing-1",) if blocked else (),
        "normal",
        PlanningStatus.BLOCKED_BY_MISSING_FACTS if blocked else PlanningStatus.READY,
        "high",
        ("pauses et badgeage",),
        ("rule-test",),
        False,
        True,
        True,
    )
    return ResearchPlan(
        "plan-1",
        "case-a",
        (issue,),
        (target,),
        () if blocked else (query,),
        (query,) if blocked else (),
        (),
        (),
        PlanningStatus.BLOCKED_BY_MISSING_FACTS if blocked else PlanningStatus.READY,
        None,
        "test",
    )
