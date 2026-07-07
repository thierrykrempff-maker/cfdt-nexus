#!/usr/bin/env python
"""Local CLI for the PISTE / Legifrance connector.

No command prints credentials or tokens. The JSON output is intentionally
diagnostic and anonymized around authentication.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import legifrance_connector as legifrance


DEFAULT_TEST_QUERY = "repos quotidien duree travail nuit"


def emit(payload: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(format_text(payload))


def format_text(payload: dict[str, Any]) -> str:
    lines = ["DIAGNOSTIC LEGIFRANCE"]
    if "configuration" in payload:
        config = payload["configuration"]
        lines.extend(
            [
                f"Client ID present : {'oui' if config.get('client_id_present') else 'non'}",
                f"Client Secret present : {'oui' if config.get('client_secret_present') else 'non'}",
                "Variables manquantes : " + (", ".join(config.get("missing_variables", [])) or "aucune"),
                f"Token URL : {config.get('token_url')}",
                f"API base : {config.get('api_base_url')}",
                f"Cache local : {config.get('cache_dir')}",
            ]
        )
    if payload.get("ok") is not None:
        lines.append(f"Statut : {'OK' if payload.get('ok') else 'ERREUR'}")
    if payload.get("error"):
        lines.append(f"Erreur : {payload['error']}")
    steps = payload.get("steps") or {}
    for name, step in steps.items():
        lines.append(f"- {name} : {'OK' if step.get('ok') else 'ERREUR'}")
    if payload.get("source_sample"):
        source = payload["source_sample"]
        lines.append(
            "Source test : "
            + " | ".join(
                str(value)
                for value in [
                    source.get("document"),
                    source.get("article"),
                    source.get("official_id"),
                    source.get("etat"),
                    f"en vigueur={source.get('is_in_force')}",
                ]
                if value is not None
            )
        )
    return "\n".join(lines)


def command_diagnose(_args: argparse.Namespace) -> dict[str, Any]:
    config = legifrance.LegifranceConfig.from_env()
    return {
        "ok": config.configured,
        "configuration": legifrance.safe_configuration(config),
        "endpoints": legifrance.LegifranceClient(config).used_endpoints(),
        "notice": "Aucun secret ni token n'est affiche par cette commande.",
    }


def command_test_connection(args: argparse.Namespace) -> dict[str, Any]:
    config = legifrance.LegifranceConfig.from_env()
    client = legifrance.LegifranceClient(config)
    try:
        return client.test_connection(args.query, limit=args.limit, article_id=args.article_id)
    except legifrance.LegifranceError as exc:
        return {
            "ok": False,
            "configuration": legifrance.safe_configuration(config),
            "endpoints": client.used_endpoints(),
            "steps": {},
            "error": str(exc),
            "notice": "Aucun secret ni token n'est affiche par cette commande.",
        }


def command_search(args: argparse.Namespace) -> dict[str, Any]:
    config = legifrance.LegifranceConfig.from_env()
    client = legifrance.LegifranceClient(config)
    try:
        hits = client.search_article_hits(args.query, limit=args.limit)
        return {
            "ok": True,
            "configuration": legifrance.safe_configuration(config),
            "endpoints": client.used_endpoints(),
            "hit_count": len(hits),
            "hits": hits,
        }
    except legifrance.LegifranceError as exc:
        return {
            "ok": False,
            "configuration": legifrance.safe_configuration(config),
            "endpoints": client.used_endpoints(),
            "error": str(exc),
        }


def command_article(args: argparse.Namespace) -> dict[str, Any]:
    config = legifrance.LegifranceConfig.from_env()
    client = legifrance.LegifranceClient(config)
    try:
        source = client.article_source(args.article_id)
        return {
            "ok": True,
            "configuration": legifrance.safe_configuration(config),
            "endpoints": client.used_endpoints(),
            "source": source,
        }
    except legifrance.LegifranceError as exc:
        return {
            "ok": False,
            "configuration": legifrance.safe_configuration(config),
            "endpoints": client.used_endpoints(),
            "error": str(exc),
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CFDT Nexus - connecteur Legifrance PISTE")
    sub = parser.add_subparsers(dest="command", required=True)

    diagnose = sub.add_parser("diagnose")
    diagnose.add_argument("--format", choices=["text", "json"], default="text")

    test = sub.add_parser("test-connection")
    test.add_argument("--query", default=DEFAULT_TEST_QUERY)
    test.add_argument("--limit", type=int, default=3)
    test.add_argument("--article-id")
    test.add_argument("--format", choices=["text", "json"], default="text")

    search = sub.add_parser("search")
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=3)
    search.add_argument("--format", choices=["text", "json"], default="text")

    article = sub.add_parser("article")
    article.add_argument("--article-id", required=True)
    article.add_argument("--format", choices=["text", "json"], default="text")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "diagnose":
        emit(command_diagnose(args), args.format)
    elif args.command == "test-connection":
        emit(command_test_connection(args), args.format)
    elif args.command == "search":
        emit(command_search(args), args.format)
    elif args.command == "article":
        emit(command_article(args), args.format)
    else:
        raise SystemExit(f"Commande inconnue: {args.command}")


if __name__ == "__main__":
    main()
