"""Pure ARCH-02 adapters for the legacy payroll expert.

The module does not call the payroll expert, a connector, or a network service.
It only converts already available in-memory structures.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Mapping, Sequence

from automation.contracts import (
    ConfidenceAssessment,
    ConfidenceDimension,
    ConfidenceLevel,
    ConfidentialityLevel,
    ConnectionStatus,
    ConsultationStatus,
    CriticalityLevel,
    ExpertReport,
    ExpertRequest,
    KnowledgeSource,
    MissingInformation,
    ReportStatus,
    RiskAssessment,
    SourceCategory,
    SourceEvidence,
    Statement,
    StatementKind,
)
if TYPE_CHECKING:
    from automation.payroll.payroll_reasoning_protocol import PayrollQuestion


ADAPTER_VERSION = "1.0"
ADAPTER_NAME = "payroll_legacy_arch02"
_BRIDGE_KEY = "_nexus_arch02"

_REQUEST_KEYS = {
    "request_id", "case_id", "dossier_id", "query", "question", "requested_domain", "domain",
    "context", "payroll_context", "payroll_rule_context", "reference_date", "employee_population",
    "employment_category", "work_schedule", "site", "variables", "documents", "documents_present",
    "pieces_presentes", "facts", "established_facts", "declarations", "declared_information",
    "hypotheses", "assumptions", "assumed_intentions", "scenarios", "missing_information",
    "sources", "available_evidence_refs", "detail_level", "confidentiality", "metadata", "route",
    "issue_groups", "documents_to_request", _BRIDGE_KEY,
}

_REPORT_KEYS = {
    "report_id", "request_id", "active", "name", "objet_du_controle",
    "elements_du_bulletin_concernes", "regles_ou_sources_disponibles",
    "donnees_necessaires_au_calcul", "methode_de_controle", "anomalies_potentielles",
    "calcul_detaille", "documents_necessaires", "sources_utilisees", "sources",
    "source_evidence", "niveau_de_confiance", "confidence", "limites", "warnings", "errors",
    "risks", "recommendations", "proposed_actions", "questions_to_ask", "missing_information",
    "hypotheses", "assumptions", "scenarios", "contradictions", "conclusions",
    "payroll_rule_analysis", "payroll_referential_analysis", "reponse_salarie", "reponse_expert",
    "metadata", _BRIDGE_KEY,
}

_CONFIDENCE_MAP = {
    "tres faible": ConfidenceLevel.VERY_LOW,
    "very_low": ConfidenceLevel.VERY_LOW,
    "faible": ConfidenceLevel.LOW,
    "low": ConfidenceLevel.LOW,
    "moyen": ConfidenceLevel.MEDIUM,
    "moyenne": ConfidenceLevel.MEDIUM,
    "medium": ConfidenceLevel.MEDIUM,
    "eleve": ConfidenceLevel.HIGH,
    "elevee": ConfidenceLevel.HIGH,
    "high": ConfidenceLevel.HIGH,
    "tres eleve": ConfidenceLevel.VERY_HIGH,
    "very_high": ConfidenceLevel.VERY_HIGH,
}


def _json_value(value: Any) -> Any:
    """Return a detached, deterministic JSON-compatible copy."""
    if isinstance(value, Enum):
        return value.value
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return _json_value(asdict(value))
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("legacy payroll mapping keys must be strings")
            result[key] = _json_value(item)
        return result
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        converted = [_json_value(item) for item in value]
        return sorted(converted, key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True))
    raise TypeError(f"legacy payroll value of type {type(value).__name__} is not JSON-compatible")


def _copy_mapping(value: Mapping[str, Any], label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    result = _json_value(value)
    if not isinstance(result, dict):
        raise TypeError(f"{label} must serialize to an object")
    return result


def _canonical(value: Any) -> str:
    return json.dumps(_json_value(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _stable_id(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}-{digest}"


def _text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _string_list(value: Any, field_name: str) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [_text(value, field_name)]
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        raise TypeError(f"{field_name} must be a string or a sequence")
    return [_text(item, field_name) for item in value]


def _sequence(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    if isinstance(value, (str, Mapping)):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return list(value)
    raise TypeError("legacy payroll collection must be a string, mapping, or sequence")


def _unknown_fields(value: Mapping[str, Any], known: set[str]) -> dict[str, Any]:
    return {key: _json_value(item) for key, item in value.items() if key not in known}


def _legacy_identifier(original: Mapping[str, Any]) -> str | None:
    for key in ("request_id", "report_id", "case_id", "dossier_id", "source_id", "id"):
        if original.get(key) not in (None, ""):
            return str(original[key])
    return None


def _unconverted_record(field: str, value: Any, warning: str) -> dict[str, Any]:
    return {
        "legacy_type": type(value).__name__,
        "legacy_field": field,
        "legacy_value": _json_value(value),
        "adapter_version": ADAPTER_VERSION,
        "conversion_status": "PRESERVED_UNCONVERTED",
        "conversion_warning": warning,
    }


def _adapter_metadata(
    source_type: str,
    original: Mapping[str, Any],
    unknown: Mapping[str, Any],
    *,
    preserved_fields: Sequence[str] = (),
) -> dict[str, Any]:
    preserved = dict(unknown)
    for field in preserved_fields:
        if field in original and field not in preserved:
            preserved[field] = original[field]
    records = [
        _unconverted_record(
            field,
            value,
            "No direct ARCH-01 field; value preserved in structured legacy metadata.",
        )
        for field, value in sorted(preserved.items())
    ]
    converted = sorted(field for field in original if field not in preserved and field != _BRIDGE_KEY)
    return {
        "adapter": {
            "name": ADAPTER_NAME,
            "version": ADAPTER_VERSION,
            "source_type": source_type,
        },
        "legacy": {
            "legacy_type": source_type,
            "origin_identifier": _legacy_identifier(original),
            "original": _json_value(original),
            "unknown_fields": _json_value(unknown),
            "converted_fields": converted,
            "unconverted_fields": records,
            "conversion_warnings": [record["conversion_warning"] for record in records],
        },
    }


def _merge_metadata(base: Mapping[str, Any], extra: Mapping[str, Any]) -> dict[str, Any]:
    result = _copy_mapping(base, "metadata") if base else {}
    for key, value in extra.items():
        if key in result:
            result[f"legacy_{key}"] = result.pop(key)
        result[key] = _json_value(value)
    return result


def _statement(item: Any, kind: StatementKind, position: int, origin: str) -> Statement:
    if isinstance(item, Mapping):
        raw = _copy_mapping(item, origin)
        text = raw.get("text") or raw.get("value") or raw.get("description")
        statement_id = raw.get("statement_id") or raw.get("id")
        evidence_ids = tuple(_string_list(raw.get("evidence_ids"), f"{origin}.evidence_ids"))
        metadata = {key: value for key, value in raw.items() if key not in {"text", "value", "description", "statement_id", "id", "evidence_ids", "kind"}}
    else:
        raw = item
        text = item
        statement_id = None
        evidence_ids = ()
        metadata = {}
    clean_text = _text(text, origin)
    return Statement(
        statement_id=str(statement_id or _stable_id("stmt", [origin, position, kind.value, raw])),
        text=clean_text,
        kind=kind,
        evidence_ids=evidence_ids,
        metadata={"adapter_origin": origin, **metadata},
    )


def _statements(value: Any, kind: StatementKind, origin: str) -> tuple[Statement, ...]:
    if value in (None, ""):
        return ()
    items = [value] if isinstance(value, (str, Mapping)) else list(value)
    return tuple(_statement(item, kind, position, origin) for position, item in enumerate(items))


def _criticality(value: Any, default: CriticalityLevel = CriticalityLevel.MEDIUM) -> CriticalityLevel:
    if value in (None, ""):
        return default
    try:
        return CriticalityLevel(str(value).strip().upper())
    except ValueError as exc:
        raise ValueError(f"unknown criticality level: {value}") from exc


def _missing_information(value: Any, position: int) -> MissingInformation:
    if isinstance(value, Mapping):
        raw = _copy_mapping(value, "missing_information")
        description = raw.get("description") or raw.get("value") or raw.get("name")
        reason = raw.get("reason") or "Information nécessaire à l'analyse Paie."
        question = raw.get("suggested_question") or raw.get("question") or f"Pouvez-vous préciser : {description} ?"
        missing_id = raw.get("missing_id") or raw.get("id")
        known = {"missing_id", "id", "description", "value", "name", "reason", "criticality", "addressee", "suggested_question", "question", "blocking", "domain"}
        metadata = _unknown_fields(raw, known)
        blocking = raw.get("blocking", False)
        if not isinstance(blocking, bool):
            raise TypeError("missing_information.blocking must be a boolean")
    else:
        raw = value
        description = value
        reason = "Information nécessaire à l'analyse Paie."
        question = f"Pouvez-vous préciser : {value} ?"
        missing_id = None
        metadata = {}
        blocking = False
    clean_description = _text(description, "missing_information.description")
    return MissingInformation(
        missing_id=str(missing_id or _stable_id("missing", [position, raw])),
        description=clean_description,
        reason=_text(reason, "missing_information.reason"),
        criticality=_criticality(raw.get("criticality") if isinstance(raw, Mapping) else None),
        addressee=str(raw.get("addressee", "demandeur") if isinstance(raw, Mapping) else "demandeur"),
        suggested_question=_text(question, "missing_information.suggested_question"),
        blocking=blocking,
        domain=str(raw.get("domain", "paie") if isinstance(raw, Mapping) else "paie"),
        metadata={"adapter_origin": "legacy_payroll", **metadata},
    )


def _missing_items(value: Any) -> tuple[MissingInformation, ...]:
    if value in (None, ""):
        return ()
    items = [value] if isinstance(value, (str, Mapping)) else list(value)
    return tuple(_missing_information(item, position) for position, item in enumerate(items))


def _risk(item: Any, position: int) -> RiskAssessment:
    if not isinstance(item, Mapping):
        raise TypeError("a legacy risk must be a structured mapping; free text is not silently classified")
    raw = _copy_mapping(item, "risk")
    description = _text(raw.get("description"), "risk.description")
    impact = _text(raw.get("impact"), "risk.impact")
    if raw.get("level") in (None, ""):
        raise ValueError("risk.level must be explicit; an unknown risk level is not converted to MEDIUM")
    level = _criticality(raw.get("level"))
    known = {"risk_id", "id", "risk_type", "type", "description", "level", "probability", "impact", "horizon", "supporting_evidence", "mitigation_actions", "domain"}
    return RiskAssessment(
        risk_id=str(raw.get("risk_id") or raw.get("id") or _stable_id("risk", [position, raw])),
        risk_type=str(raw.get("risk_type") or raw.get("type") or "legacy_payroll"),
        description=description,
        level=level,
        probability=raw.get("probability"),
        impact=impact,
        horizon=str(raw.get("horizon") or "non précisé"),
        supporting_evidence=tuple(_string_list(raw.get("supporting_evidence"), "risk.supporting_evidence")),
        mitigation_actions=tuple(_string_list(raw.get("mitigation_actions"), "risk.mitigation_actions")),
        domain=str(raw.get("domain") or "paie"),
        metadata={"adapter_origin": "legacy_payroll", "unknown_fields": _unknown_fields(raw, known)},
    )


def _risks(value: Any) -> tuple[RiskAssessment, ...]:
    if value in (None, ""):
        return ()
    items = [value] if isinstance(value, Mapping) else list(value)
    return tuple(_risk(item, position) for position, item in enumerate(items))


def _confidence(value: Any, origin: str) -> ConfidenceAssessment:
    return legacy_confidence_to_confidence_assessment(value, origin=origin)


def legacy_confidence_to_confidence_assessment(
    value: Any,
    *,
    dimension: ConfidenceDimension = ConfidenceDimension.EXPERT_ANALYSIS_CONFIDENCE,
    origin: str = "legacy_payroll_confidence",
) -> ConfidenceAssessment:
    """Convert one legacy confidence value without inventing a known level."""
    if not isinstance(dimension, ConfidenceDimension):
        raise TypeError("dimension must be a ConfidenceDimension")
    raw = None if value is None else str(value).strip()
    normalized = (raw or "").casefold().replace("é", "e").replace("è", "e").replace("ê", "e")
    level = _CONFIDENCE_MAP.get(normalized)
    return ConfidenceAssessment(
        assessment_id=_stable_id("confidence", [origin, raw]),
        dimension=dimension,
        level=level,
        rationale="Conversion prudente d'un niveau global historique ; ne vaut pas certitude factuelle.",
        raw_value=raw if level is None else None,
        producer=ADAPTER_NAME,
        metadata={"adapter_origin": origin, "legacy_global_confidence": raw},
    )


def _confidence_assessments(value: Any) -> tuple[tuple[ConfidenceAssessment, ...], dict[str, Any]]:
    if not isinstance(value, Mapping):
        return (_confidence(value, "legacy_payroll_report"),), {}
    raw = _copy_mapping(value, "legacy confidence")
    aliases = (
        (("factual", "facts", "factual_confidence"), ConfidenceDimension.EXPERT_ANALYSIS_CONFIDENCE),
        (("legal", "legal_confidence"), ConfidenceDimension.LEGAL_SOLIDITY),
        (("documentary", "document", "document_confidence"), ConfidenceDimension.SOURCE_RELIABILITY),
        (("coverage", "coverage_confidence"), ConfidenceDimension.CASE_COMPLETENESS),
        (("global", "overall", "global_confidence"), ConfidenceDimension.EXPERT_ANALYSIS_CONFIDENCE),
    )
    assessments: list[ConfidenceAssessment] = []
    used_dimensions: set[ConfidenceDimension] = set()
    consumed: set[str] = set()
    preserved: dict[str, Any] = {}
    for keys, dimension in aliases:
        key = next((candidate for candidate in keys if candidate in raw), None)
        if key is None:
            continue
        consumed.add(key)
        if dimension in used_dimensions:
            preserved[key] = raw[key]
            continue
        assessments.append(legacy_confidence_to_confidence_assessment(raw[key], dimension=dimension, origin=f"legacy_confidence.{key}"))
        used_dimensions.add(dimension)
    for key, item in raw.items():
        if key not in consumed:
            preserved[key] = item
    return tuple(assessments), {
        "unmapped_dimensions": preserved,
        "warning": "Legacy confidence dimensions without a faithful ARCH-01 equivalent remain in metadata." if preserved else None,
    }


def _parse_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be an ISO-8601 datetime with timezone")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime with timezone") from exc
    if result.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return result


def legacy_evidence_to_source_evidence(value: Mapping[str, Any], source_id: str) -> SourceEvidence:
    """Convert an explicit access trace; incomplete or unverifiable claims are rejected."""
    evidence_data = _copy_mapping(value, "consultation_evidence")
    status_value = str(evidence_data.get("status") or evidence_data.get("consultation_status") or "").upper()
    if status_value not in {ConsultationStatus.SUCCEEDED.value, ConsultationStatus.CACHE_HIT.value}:
        raise ValueError("SourceEvidence requires an explicitly SUCCEEDED or CACHE_HIT consultation")
    status = ConsultationStatus(status_value)
    occurred_at = _parse_datetime(evidence_data.get("occurred_at"), "consultation_evidence.occurred_at")
    exact_reference = _text(evidence_data.get("exact_reference"), "consultation_evidence.exact_reference")
    access_result = _text(evidence_data.get("access_result"), "consultation_evidence.access_result")
    trace = _text(
        evidence_data.get("excerpt_or_fingerprint") or evidence_data.get("verifiable_trace"),
        "consultation_evidence.excerpt_or_fingerprint",
    )
    evidence_id = str(evidence_data.get("evidence_id") or _stable_id("evidence", [source_id, evidence_data]))
    return SourceEvidence(
        evidence_id=evidence_id,
        source_id=_text(source_id, "source_id"),
        access_mode=str(evidence_data.get("access_mode") or "legacy_explicit_trace"),
        consultation_status=status,
        occurred_at=occurred_at,
        exact_reference=exact_reference,
        excerpt_or_fingerprint=trace,
        access_result=access_result,
        metadata={"adapter_origin": "legacy_payroll_source"},
    )


def legacy_payroll_source_to_contracts(value: str | Mapping[str, Any]) -> tuple[KnowledgeSource, SourceEvidence | None]:
    """Convert a source; evidence is emitted only for an explicit, valid access trace."""
    raw = {"name": value} if isinstance(value, str) else _copy_mapping(value, "legacy payroll source")
    name = _text(raw.get("name") or raw.get("document") or raw.get("title"), "source.name")
    source_id = str(raw.get("source_id") or _stable_id("source", raw))
    evidence_raw = raw.get("consultation_evidence")
    claims_consultation = raw.get("consulted") is True or raw.get("consulted_at") not in (None, "")
    if claims_consultation and not isinstance(evidence_raw, Mapping):
        raise ValueError("a consultation claim requires structured consultation_evidence")
    evidence: SourceEvidence | None = None
    consulted_at: datetime | None = None
    evidence_id: str | None = None
    if evidence_raw is not None:
        evidence_data = _copy_mapping(evidence_raw, "consultation_evidence")
        evidence = legacy_evidence_to_source_evidence(evidence_data, source_id)
        consulted_at = evidence.occurred_at
        evidence_id = evidence.evidence_id
    is_official = raw.get("is_official", False)
    is_internal = raw.get("is_internal", not is_official)
    if not isinstance(is_official, bool) or not isinstance(is_internal, bool):
        raise TypeError("source is_official and is_internal must be booleans")
    category_value = raw.get("category") or ("OFFICIAL" if is_official else "INTERNAL" if is_internal else "OTHER")
    confidentiality_value = raw.get("confidentiality") or ("INTERNAL" if is_internal else "PUBLIC")
    known = {"source_id", "name", "document", "title", "publisher", "category", "source_type", "is_official", "is_internal", "confidentiality", "connection_status", "reference", "jurisdiction", "domains", "version", "freshness", "consulted", "consulted_at", "consultation_evidence"}
    source = KnowledgeSource(
        source_id=source_id,
        name=name,
        publisher=str(raw.get("publisher") or "non précisé"),
        category=SourceCategory(str(category_value).upper()),
        source_type=str(raw.get("source_type") or "legacy_reference"),
        is_official=is_official,
        is_internal=is_internal,
        confidentiality=ConfidentialityLevel(str(confidentiality_value).upper()),
        connection_status=ConnectionStatus(str(raw.get("connection_status") or "NOT_INVESTIGATED").upper()),
        reference=raw.get("reference"),
        consulted_at=consulted_at,
        retrieval_evidence_id=evidence_id,
        jurisdiction=raw.get("jurisdiction"),
        domains=tuple(_string_list(raw.get("domains"), "source.domains")),
        version=raw.get("version"),
        freshness=raw.get("freshness"),
        metadata={
            "adapter_origin": "legacy_payroll_source",
            "consultation_not_demonstrated": evidence is None,
            "unknown_fields": _unknown_fields(raw, known),
        },
    )
    return source, evidence


def legacy_source_to_knowledge_source(value: str | Mapping[str, Any]) -> KnowledgeSource:
    return legacy_payroll_source_to_contracts(value)[0]


def legacy_missing_information_to_contract(value: Any, position: int = 0) -> MissingInformation:
    return _missing_information(value, position)


def legacy_risk_to_risk_assessment(value: Mapping[str, Any], position: int = 0) -> RiskAssessment:
    return _risk(value, position)


def _request_context(raw: Mapping[str, Any]) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for key in ("context", "payroll_context", "payroll_rule_context"):
        value = raw.get(key)
        if value is not None:
            if not isinstance(value, Mapping):
                raise TypeError(f"{key} must be a mapping")
            context.update(_copy_mapping(value, key))
    for key in ("reference_date", "employee_population", "employment_category", "work_schedule", "site", "variables", "documents", "documents_present", "pieces_presentes"):
        if key in raw and key not in context:
            context[key] = _json_value(raw[key])
    return context


def legacy_payroll_request_to_expert_request(value: Mapping[str, Any]) -> ExpertRequest:
    raw = _copy_mapping(value, "legacy payroll request")
    bridge = raw.get(_BRIDGE_KEY)
    if isinstance(bridge, Mapping) and isinstance(bridge.get("expert_request"), Mapping):
        bridged = ExpertRequest.from_dict(bridge["expert_request"])
        if str(raw.get("query") or raw.get("question") or "").strip() == bridged.question_text:
            return bridged
    question = _text(raw.get("query") or raw.get("question"), "legacy payroll question")
    explicit_id = raw.get("request_id") or raw.get("case_id") or raw.get("dossier_id")
    request_id = str(explicit_id or _stable_id("payreq", raw))
    facts_value = raw.get("facts") if "facts" in raw else raw.get("established_facts")
    declarations_value = raw.get("declarations") if "declarations" in raw else raw.get("declared_information")
    facts = _statements(facts_value, StatementKind.ESTABLISHED_FACT, "facts")
    declarations = _statements(declarations_value, StatementKind.DECLARED_INFORMATION, "declarations")
    sources = _sequence(raw.get("sources"))
    source_refs: list[str] = []
    for source in sources:
        contract, _ = legacy_payroll_source_to_contracts(source)
        source_refs.append(contract.source_id)
    explicit_refs = _string_list(raw.get("available_evidence_refs"), "available_evidence_refs")
    legacy_categories = {
        "assumptions": _json_value(raw.get("hypotheses") if "hypotheses" in raw else raw.get("assumptions") or []),
        "assumed_intentions": _json_value(raw.get("assumed_intentions") or []),
        "scenarios": _json_value(raw.get("scenarios") or []),
    }
    metadata = _merge_metadata(
        raw.get("metadata") if isinstance(raw.get("metadata"), Mapping) else {},
        _adapter_metadata(
            "legacy_payroll_mapping",
            raw,
            _unknown_fields(raw, _REQUEST_KEYS),
            preserved_fields=("hypotheses", "assumptions", "assumed_intentions", "scenarios", "route", "issue_groups"),
        ),
    )
    metadata["legacy_categories"] = legacy_categories
    return ExpertRequest(
        request_id=request_id,
        question_text=question,
        requested_domain=str(raw.get("requested_domain") or raw.get("domain") or "paie"),
        context=_request_context(raw),
        facts=facts,
        declared_information=declarations,
        available_evidence_refs=tuple(dict.fromkeys(explicit_refs + source_refs)),
        missing_information=_missing_items(raw.get("missing_information")),
        detail_level=str(raw.get("detail_level") or "STANDARD"),
        confidentiality=ConfidentialityLevel(str(raw.get("confidentiality") or "RESTRICTED").upper()),
        metadata=metadata,
    )


def payroll_question_to_expert_request(value: PayrollQuestion, request_id: str | None = None) -> ExpertRequest:
    from automation.payroll.payroll_reasoning_protocol import PayrollQuestion

    if not isinstance(value, PayrollQuestion):
        raise TypeError("value must be a PayrollQuestion")
    raw = _json_value(value)
    if not isinstance(raw, dict):
        raise TypeError("PayrollQuestion must serialize to an object")
    legacy = {
        "request_id": request_id or _stable_id("payreq", raw),
        "query": value.question,
        "domain": "paie",
        "context": {
            "question_type": value.question_type,
            "subject": value.subject,
            "scope": value.scope.value,
            "population": value.population,
            "period": value.period,
            "payroll_period": value.payroll_period,
            "urgent": value.urgent,
            "available_documents": sorted(item.value for item in value.available_documents),
            "rules": list(value.rules),
            "variables": list(value.variables),
            "kelio_counters": list(value.kelio_counters),
            "nibelis_rubrics": list(value.nibelis_rubrics),
            "parameters": list(value.parameters),
            "contradictory_documents": value.contradictory_documents,
        },
        "sources": list(value.sources),
        "missing_information": list(value.missing_information),
        "metadata": {"payroll_question": raw},
    }
    return legacy_payroll_request_to_expert_request(legacy)


def expert_request_to_legacy_payroll(value: ExpertRequest) -> dict[str, Any]:
    if not isinstance(value, ExpertRequest):
        raise TypeError("value must be an ExpertRequest")
    metadata = value.to_dict().get("metadata", {})
    legacy_meta = metadata.get("legacy", {}) if isinstance(metadata, Mapping) else {}
    original = legacy_meta.get("original") if isinstance(legacy_meta, Mapping) else None
    result = _copy_mapping(original, "legacy original") if isinstance(original, Mapping) else {}
    result["request_id"] = value.request_id
    result["query"] = value.question_text
    result["domain"] = value.requested_domain
    result["context"] = _json_value(value.context)
    result["facts"] = [item.to_dict() for item in value.facts]
    result["declarations"] = [item.to_dict() for item in value.declared_information]
    result["missing_information"] = [item.to_dict() for item in value.missing_information]
    categories = metadata.get("legacy_categories", {}) if isinstance(metadata, Mapping) else {}
    if isinstance(categories, Mapping):
        result["hypotheses"] = _json_value(categories.get("assumptions") or [])
        result["assumed_intentions"] = _json_value(categories.get("assumed_intentions") or [])
        result["scenarios"] = _json_value(categories.get("scenarios") or [])
    result["available_evidence_refs"] = list(value.available_evidence_refs)
    result["detail_level"] = value.detail_level
    result["confidentiality"] = value.confidentiality.value
    result[_BRIDGE_KEY] = {
        "adapter": ADAPTER_NAME,
        "version": ADAPTER_VERSION,
        "expert_request": value.to_dict(),
    }
    return _json_value(result)


def expert_request_to_payroll_question(value: ExpertRequest) -> PayrollQuestion:
    from automation.payroll.payroll_reasoning_protocol import DocumentCategory, PayrollQuestion, QuestionScope

    if not isinstance(value, ExpertRequest):
        raise TypeError("value must be an ExpertRequest")
    context = value.to_dict().get("context", {})
    raw_meta = value.to_dict().get("metadata", {})
    payroll_raw = raw_meta.get("payroll_question") if isinstance(raw_meta, Mapping) else None
    raw = payroll_raw if isinstance(payroll_raw, Mapping) else context
    try:
        scope = QuestionScope(str(raw.get("scope") or "employee"))
        documents = frozenset(DocumentCategory(item) for item in raw.get("available_documents") or ())
    except ValueError as exc:
        raise ValueError("ExpertRequest contains an unsupported PayrollQuestion scope or document category") from exc
    return PayrollQuestion(
        question=value.question_text,
        question_type=str(raw.get("question_type") or "question"),
        subject=str(raw.get("subject") or "general"),
        scope=scope,
        population=raw.get("population"),
        period=raw.get("period"),
        payroll_period=raw.get("payroll_period"),
        urgent=bool(raw.get("urgent", False)),
        available_documents=documents,
        sources=tuple(str(item) for item in raw.get("sources") or value.available_evidence_refs),
        rules=tuple(str(item) for item in raw.get("rules") or ()),
        variables=tuple(str(item) for item in raw.get("variables") or ()),
        kelio_counters=tuple(str(item) for item in raw.get("kelio_counters") or ()),
        nibelis_rubrics=tuple(str(item) for item in raw.get("nibelis_rubrics") or ()),
        parameters=tuple(str(item) for item in raw.get("parameters") or ()),
        missing_information=tuple(item.description for item in value.missing_information),
        contradictory_documents=bool(raw.get("contradictory_documents", False)),
    )


def legacy_payroll_report_to_expert_report(value: Mapping[str, Any], request_id: str | None = None) -> ExpertReport:
    raw = _copy_mapping(value, "legacy payroll report")
    bridge = raw.get(_BRIDGE_KEY)
    if isinstance(bridge, Mapping) and isinstance(bridge.get("expert_report"), Mapping):
        bridged = ExpertReport.from_dict(bridge["expert_report"])
        if not request_id or bridged.request_id == request_id:
            return bridged
    resolved_request_id = request_id or raw.get("request_id")
    if not resolved_request_id:
        raise ValueError("legacy payroll report requires request_id for traceability")
    sources: list[KnowledgeSource] = []
    evidence: list[SourceEvidence] = []
    source_values = _sequence(raw.get("sources") if raw.get("sources") is not None else raw.get("sources_utilisees"))
    for source_value in source_values:
        source, source_evidence = legacy_payroll_source_to_contracts(source_value)
        sources.append(source)
        if source_evidence is not None:
            evidence.append(source_evidence)
    assumptions_value = raw.get("hypotheses") if "hypotheses" in raw else raw.get("assumptions")
    assumptions = list(_statements(assumptions_value, StatementKind.ASSUMPTION, "hypotheses"))
    assumptions.extend(_statements(raw.get("anomalies_potentielles"), StatementKind.ASSUMPTION, "anomalies_potentielles"))
    scenarios = _statements(raw.get("scenarios"), StatementKind.SCENARIO, "scenarios")
    missing_value = raw.get("missing_information")
    if missing_value is None:
        missing_value = raw.get("donnees_necessaires_au_calcul") or ()
    confidence_value = raw.get("niveau_de_confiance") if "niveau_de_confiance" in raw else raw.get("confidence")
    confidence_assessments, confidence_metadata = _confidence_assessments(confidence_value)
    errors = _string_list(raw.get("errors"), "errors")
    warnings = _string_list(raw.get("warnings"), "warnings") + _string_list(raw.get("limites"), "limites")
    if errors:
        status = ReportStatus.FAILED
    elif raw.get("active") is False:
        status = ReportStatus.REFUSED
    elif missing_value or warnings:
        status = ReportStatus.PARTIAL
    else:
        status = ReportStatus.COMPLETED
    findings = _string_list(raw.get("objet_du_controle"), "objet_du_controle")
    findings += _string_list(raw.get("elements_du_bulletin_concernes"), "elements_du_bulletin_concernes")
    recommendations = _string_list(raw.get("recommendations"), "recommendations")
    recommendations += _string_list(raw.get("methode_de_controle"), "methode_de_controle")
    questions = _string_list(raw.get("questions_to_ask"), "questions_to_ask")
    metadata = _merge_metadata(
        raw.get("metadata") if isinstance(raw.get("metadata"), Mapping) else {},
        _adapter_metadata(
            "legacy_payroll_report",
            raw,
            _unknown_fields(raw, _REPORT_KEYS),
            preserved_fields=("payroll_rule_analysis", "payroll_referential_analysis", "reponse_salarie", "reponse_expert"),
        ),
    )
    if confidence_metadata:
        metadata["confidence_conversion"] = confidence_metadata
    for key in ("payroll_rule_analysis", "payroll_referential_analysis", "reponse_salarie", "reponse_expert"):
        if key in raw:
            metadata.setdefault("legacy_sections", {})[key] = _json_value(raw[key])
    return ExpertReport(
        report_id=str(raw.get("report_id") or _stable_id("payreport", [resolved_request_id, raw])),
        request_id=str(resolved_request_id),
        producer=str(raw.get("name") or "Expert Paie V0"),
        findings=tuple(findings),
        conclusions=tuple(_string_list(raw.get("conclusions"), "conclusions")),
        recommendations=tuple(recommendations),
        proposed_actions=tuple(_string_list(raw.get("proposed_actions"), "proposed_actions")),
        questions_to_ask=tuple(questions),
        missing_information=_missing_items(missing_value),
        risks=_risks(raw.get("risks")),
        sources=tuple(sources),
        source_evidence=tuple(evidence),
        contradictions=tuple(_string_list(raw.get("contradictions"), "contradictions")),
        assumptions=tuple(assumptions),
        scenarios=scenarios,
        confidence_assessments=confidence_assessments,
        warnings=tuple(dict.fromkeys(warnings)),
        errors=tuple(errors),
        status=status,
        metadata=metadata,
    )


def expert_report_to_legacy_payroll(value: ExpertReport) -> dict[str, Any]:
    if not isinstance(value, ExpertReport):
        raise TypeError("value must be an ExpertReport")
    serialized = value.to_dict()
    metadata = serialized.get("metadata", {})
    legacy_meta = metadata.get("legacy", {}) if isinstance(metadata, Mapping) else {}
    original = legacy_meta.get("original") if isinstance(legacy_meta, Mapping) else None
    result = _copy_mapping(original, "legacy original") if isinstance(original, Mapping) else {}
    original_object = result.get("objet_du_controle") if result else None
    original_elements = result.get("elements_du_bulletin_concernes") if result else None
    result.update({
        "report_id": value.report_id,
        "request_id": value.request_id,
        "active": value.status not in {ReportStatus.REFUSED, ReportStatus.FAILED},
        "name": value.producer,
        "objet_du_controle": original_object if original_object is not None else (value.findings[0] if value.findings else ""),
        "elements_du_bulletin_concernes": original_elements if original_elements is not None else list(value.findings[1:]),
        "conclusions": list(value.conclusions),
        "methode_de_controle": list(value.recommendations),
        "proposed_actions": list(value.proposed_actions),
        "questions_to_ask": list(value.questions_to_ask),
        "missing_information": [item.to_dict() for item in value.missing_information],
        "risks": [item.to_dict() for item in value.risks],
        "sources": [item.to_dict() for item in value.sources],
        "source_evidence": [item.to_dict() for item in value.source_evidence],
        "hypotheses": [item.to_dict() for item in value.assumptions],
        "scenarios": [item.to_dict() for item in value.scenarios],
        "contradictions": list(value.contradictions),
        "limites": list(value.warnings),
        "errors": list(value.errors),
    })
    confidence = value.confidence_assessments[0] if value.confidence_assessments else None
    if confidence is not None:
        result["niveau_de_confiance"] = confidence.raw_value if not confidence.known else confidence.level.value
    result[_BRIDGE_KEY] = {
        "adapter": ADAPTER_NAME,
        "version": ADAPTER_VERSION,
        "expert_report": serialized,
    }
    return _json_value(result)


# Explicit public names used by the ARCH-02 architecture contract. The shorter
# historical names remain available for compatibility with the initial pilot.
expert_request_to_legacy_payroll_request = expert_request_to_legacy_payroll
legacy_payroll_result_to_expert_report = legacy_payroll_report_to_expert_report
expert_report_to_legacy_payroll_result = expert_report_to_legacy_payroll
