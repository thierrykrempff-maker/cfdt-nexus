#!/usr/bin/env python
"""Data-only report generator for synthetic employee cases (LOT 5B)."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable, Mapping

from .employee_case import ExpertAnalysis


REPORT_VERSION = "1.0"
PIPELINE_VERSION = "LOT_5A_V1"
PROTOCOL_VERSION = "PAYROLL_REASONING_PROTOCOL_V1"
CONFIDENCE_ORDER = {"UNKNOWN": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "VERY_HIGH": 4}

SECTION_ORDER: tuple[str, ...] = (
    "header",
    "executive_summary",
    "analyzed_situation",
    "documents",
    "theme_analysis",
    "payroll_expert_summary",
    "legal_expert_summary",
    "contradictions",
    "recommended_actions",
    "confidence",
    "limits",
    "metadata",
)

THEME_LABELS = {
    "overtime": "Heures supplementaires",
    "on_call": "Astreinte",
    "paid_leave": "Conges payes",
    "classification": "Classification",
    "sickness_maintenance": "Maladie et maintien de salaire",
    "holidays_and_rest": "Jours feries et repos",
}


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _json_value(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_value(item) for item in value]
    return value


def _unique(values: Iterable[Any]) -> list[Any]:
    result: list[Any] = []
    for value in values:
        if value not in result and value not in (None, "", [], {}):
            result.append(value)
    return result


def _analysis_dict(value: ExpertAnalysis | Mapping[str, Any]) -> dict[str, Any]:
    data = _json_value(value)
    if not isinstance(data, dict):
        raise TypeError("Expert analysis must be a mapping or ExpertAnalysis.")
    return data


def _expert_matches(name: str, target: str) -> bool:
    normalized = name.lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "payroll": ("expert_paie", "paie", "payroll"),
        "legal": ("juriste_travail", "juriste", "legal", "droit_travail"),
    }
    return normalized in aliases[target]


def _lowest_confidence(values: Iterable[Any]) -> str:
    levels = [str(value) for value in values if str(value) in CONFIDENCE_ORDER]
    return min(levels, key=CONFIDENCE_ORDER.get) if levels else "UNKNOWN"


class EmployeeCaseReportGenerator:
    """Assemble pipeline and expert data without invoking or calculating anything."""

    def generate(
        self,
        pipeline_result: Mapping[str, Any],
        expert_analyses: Iterable[ExpertAnalysis | Mapping[str, Any]],
    ) -> dict[str, Any]:
        pipeline = deepcopy(dict(pipeline_result))
        analyses = [deepcopy(_analysis_dict(item)) for item in expert_analyses]
        contexts = pipeline.get("contexts") if isinstance(pipeline.get("contexts"), dict) else {}
        payroll_context = contexts.get("expert_paie") if isinstance(contexts.get("expert_paie"), dict) else {}
        diagnostic = pipeline.get("diagnostic") if isinstance(pipeline.get("diagnostic"), dict) else {}
        generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

        sections = {
            "header": self._header(pipeline, payroll_context, generated_at),
            "executive_summary": self._executive_summary(pipeline, diagnostic),
            "analyzed_situation": self._situation(pipeline, payroll_context),
            "documents": self._documents(payroll_context, diagnostic),
            "theme_analysis": self._themes(payroll_context, diagnostic, analyses),
            "payroll_expert_summary": self._expert_summary(analyses, "payroll"),
            "legal_expert_summary": self._expert_summary(analyses, "legal"),
            "contradictions": {"items": list(diagnostic.get("contradictions") or [])},
            "recommended_actions": self._actions(payroll_context, diagnostic, analyses),
            "confidence": self._confidence(diagnostic, analyses),
            "limits": self._limits(pipeline, diagnostic, analyses),
            "metadata": self._metadata(pipeline, generated_at),
        }
        report = {
            "report_type": "employee_case_analysis",
            "section_order": list(SECTION_ORDER),
            "sections": sections,
            "employee_view": self._employee_view(sections),
            "expert_view": self._expert_view(sections),
            "calculation_performed": False,
            "expert_invocation_performed": False,
            "synthetic_only": True,
        }
        return report

    @staticmethod
    def _header(pipeline: Mapping[str, Any], context: Mapping[str, Any], generated_at: str) -> dict[str, Any]:
        case_id = str(pipeline.get("case_id") or "CASE_NOT_PROVIDED")
        return {
            "case_id": case_id,
            "title": str(pipeline.get("title") or f"Rapport du dossier {case_id}"),
            "generated_at": generated_at,
            "status": str(pipeline.get("final_status") or "unknown"),
            "report_version": REPORT_VERSION,
            "confidentiality": str(pipeline.get("confidentiality") or context.get("confidentiality") or "restricted"),
        }

    @staticmethod
    def _executive_summary(pipeline: Mapping[str, Any], diagnostic: Mapping[str, Any]) -> dict[str, Any]:
        blocked = list(diagnostic.get("themes_blocked") or [])
        findings = list(diagnostic.get("convergent_findings") or [])
        subject = str(diagnostic.get("general_summary") or "Analyse documentaire structuree du dossier synthetique.")
        paragraphs = [subject]
        if findings:
            paragraphs.append("Principaux constats partages : " + "; ".join(findings[:3]) + ".")
        if blocked:
            paragraphs.append("Certains themes restent bloques faute de pieces indispensables.")
        return {
            "paragraphs": paragraphs[:3],
            "blocked_themes": blocked,
            "global_confidence": str(diagnostic.get("global_confidence") or "UNKNOWN"),
            "status": str(pipeline.get("final_status") or "unknown"),
        }

    @staticmethod
    def _situation(pipeline: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "period": context.get("period"),
            "population": context.get("population"),
            "context": context.get("synthetic_facts") or {},
            "main_question": context.get("question"),
        }

    @staticmethod
    def _documents(context: Mapping[str, Any], diagnostic: Mapping[str, Any]) -> dict[str, Any]:
        completeness = context.get("theme_completeness") if isinstance(context.get("theme_completeness"), dict) else {}
        recommended = _unique(
            item
            for theme in completeness.values()
            if isinstance(theme, dict)
            for item in theme.get("missing_recommended", [])
        )
        blocking = _unique(
            item
            for theme in completeness.values()
            if isinstance(theme, dict)
            for item in theme.get("missing_required", [])
        )
        return {
            "present": list(context.get("documents_present") or []),
            "recommended": recommended,
            "missing": list(diagnostic.get("missing_documents") or context.get("documents_missing") or []),
            "blocking": blocking,
        }

    def _themes(
        self,
        context: Mapping[str, Any],
        diagnostic: Mapping[str, Any],
        analyses: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        completeness = context.get("theme_completeness") if isinstance(context.get("theme_completeness"), dict) else {}
        blocked = set(diagnostic.get("themes_blocked") or [])
        findings = _unique(item for analysis in analyses for item in analysis.get("findings", []))
        expert_limits = _unique(item for analysis in analyses for item in analysis.get("limits", []))
        used = _unique(item for analysis in analyses for item in analysis.get("documents_used", []))
        sections: list[dict[str, Any]] = []
        for theme in context.get("themes", []):
            details = completeness.get(theme) if isinstance(completeness.get(theme), dict) else {}
            sections.append(
                {
                    "theme": theme,
                    "label": THEME_LABELS.get(theme, str(theme).replace("_", " ").title()),
                    "status": "blocked" if theme in blocked else str(details.get("status") or "analyzed"),
                    "summary": "Informations fournies par les analyses expertes disponibles.",
                    "documents_used": used,
                    "missing_documents": list(details.get("missing_required") or []),
                    "findings": findings,
                    "limits": expert_limits,
                }
            )
        return sections

    @staticmethod
    def _expert_summary(analyses: list[dict[str, Any]], target: str) -> dict[str, Any]:
        selected = [item for item in analyses if _expert_matches(str(item.get("expert", "")), target)]
        if not selected:
            return {
                "available": False,
                "status": "unavailable",
                "summary": "Aucune analyse experte disponible.",
                "findings": [],
                "rules_or_sources": [],
                "documents_used": [],
                "missing_documents": [],
                "control_points": [],
                "risks": [],
                "confidence": "UNKNOWN",
                "refusals": [],
                "limits": ["Expert non disponible."],
            }
        return {
            "available": True,
            "status": _unique(item.get("status") for item in selected),
            "summary": " ".join(str(item.get("summary", "")) for item in selected).strip(),
            "findings": _unique(value for item in selected for value in item.get("findings", [])),
            "rules_or_sources": _unique(value for item in selected for value in item.get("cited_rules_or_sources", [])),
            "documents_used": _unique(value for item in selected for value in item.get("documents_used", [])),
            "missing_documents": _unique(value for item in selected for value in item.get("missing_documents", [])),
            "control_points": _unique(value for item in selected for value in item.get("control_points", [])),
            "risks": _unique(value for item in selected for value in item.get("risks", [])),
            "confidence": _lowest_confidence(item.get("confidence") for item in selected),
            "refusals": _unique(item.get("refusal_reason") for item in selected),
            "limits": _unique(value for item in selected for value in item.get("limits", [])),
        }

    @staticmethod
    def _actions(
        context: Mapping[str, Any],
        diagnostic: Mapping[str, Any],
        analyses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        missing = list(diagnostic.get("missing_documents") or context.get("documents_missing") or [])
        controls = _unique(value for item in analyses for value in item.get("control_points", []))
        return {
            "to_verify": _unique(value for item in analyses for value in item.get("cited_rules_or_sources", [])),
            "to_request": missing,
            "to_control": controls,
            "to_complete": list(diagnostic.get("themes_blocked") or []),
            "warning": "Actions de controle uniquement; aucun conseil juridique definitif.",
        }

    @staticmethod
    def _confidence(diagnostic: Mapping[str, Any], analyses: list[dict[str, Any]]) -> dict[str, Any]:
        global_level = str(diagnostic.get("global_confidence") or "UNKNOWN")
        contradictions = list(diagnostic.get("contradictions") or [])
        missing = list(diagnostic.get("missing_documents") or [])
        refusals = list(diagnostic.get("expert_refusals") or [])
        strengths = _unique(
            value
            for item in analyses
            if str(item.get("confidence")) in {"HIGH", "VERY_HIGH"}
            for value in item.get("cited_rules_or_sources", [])
        )
        weaknesses = _unique((*missing, *contradictions, *refusals))
        return {
            "global_level": global_level,
            "causes": weaknesses or ["Niveau repris du diagnostic LOT 5A."],
            "strengthening_elements": strengths,
            "weakening_elements": weaknesses,
        }

    @staticmethod
    def _limits(
        pipeline: Mapping[str, Any],
        diagnostic: Mapping[str, Any],
        analyses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "items": _unique(
                (
                    "Aucun calcul de paie n'est effectue.",
                    "Aucun avis juridique definitif n'est produit.",
                    *("Document absent: " + str(item) for item in diagnostic.get("missing_documents", [])),
                    *(str(item) for item in diagnostic.get("limits", [])),
                    *(str(value) for item in analyses for value in item.get("limits", [])),
                )
            ),
            "assumptions": list(pipeline.get("assumptions") or []),
            "methodological": ["Le rapport assemble uniquement les donnees recues du pipeline et des experts."],
        }

    @staticmethod
    def _metadata(pipeline: Mapping[str, Any], generated_at: str) -> dict[str, Any]:
        return {
            "report_version": REPORT_VERSION,
            "generated_at": generated_at,
            "pipeline_version": PIPELINE_VERSION,
            "protocol_version": PROTOCOL_VERSION,
            "confidentiality": str(pipeline.get("confidentiality") or "restricted"),
            "synthetic_only": True,
            "source_case_id": pipeline.get("case_id"),
        }

    @staticmethod
    def _employee_view(sections: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "audience": "employee",
            "header": sections["header"],
            "summary": sections["executive_summary"],
            "situation": sections["analyzed_situation"],
            "documents": sections["documents"],
            "themes": [
                {
                    "label": item["label"],
                    "status": item["status"],
                    "missing_documents": item["missing_documents"],
                }
                for item in sections["theme_analysis"]
            ],
            "actions": sections["recommended_actions"],
            "confidence": sections["confidence"]["global_level"],
            "limits": sections["limits"]["items"],
        }

    @staticmethod
    def _expert_view(sections: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "audience": "expert",
            "sections": deepcopy(dict(sections)),
            "rules_or_sources": _unique(
                (
                    *sections["payroll_expert_summary"]["rules_or_sources"],
                    *sections["legal_expert_summary"]["rules_or_sources"],
                )
            ),
            "control_points": _unique(
                (
                    *sections["payroll_expert_summary"]["control_points"],
                    *sections["legal_expert_summary"]["control_points"],
                )
            ),
            "confidence": sections["confidence"],
            "limits": sections["limits"],
        }
