#!/usr/bin/env python
"""
Nexus local interface server.

Serves a local-only UI and calls the existing Assistant DS Router CLI:
automation/scripts/assistant_ds_router.py ask --query ... --format json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parents[1]
ROUTER_SCRIPT = ROOT / "automation" / "scripts" / "assistant_ds_router.py"
EXPERTS_DIR = ROOT / "automation"

sys.path.insert(0, str(EXPERTS_DIR))
from experts import orchestrator, report_generator  # noqa: E402


def router_environment() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_router(query: str, source_limit: int = 6) -> dict[str, Any]:
    command = [
        sys.executable,
        "-B",
        str(ROUTER_SCRIPT),
        "ask",
        "--query",
        query,
        "--source-limit",
        str(source_limit),
        "--format",
        "json",
    ]
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        env=router_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        timeout=180,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "Assistant DS Router indisponible.")
    return json.loads(completed.stdout)


def analyze_question(query: str, source_limit: int = 6) -> dict[str, Any]:
    cleaned = (query or "").strip()
    if not cleaned:
        raise ValueError("Question vide.")
    answer = run_router(cleaned, source_limit)
    expert_payload = orchestrator.orchestrate(answer)
    payload = {
        "ok": True,
        "answer": answer,
        **expert_payload,
    }
    payload["analysis_report"] = report_generator.build_report(payload)
    return payload


class NexusHandler(SimpleHTTPRequestHandler):
    server_version = "NexusLocalInterface/2.2"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(APP_DIR), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        sys.stderr.write("[nexus-local] " + format % args + "\n")

    def send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", ""}:
            self.path = "/index.html"
        if self.path == "/health":
            self.send_json(HTTPStatus.OK, {"ok": True, "service": "nexus-local-interface", "version": "2.2"})
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/analyze":
            self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Endpoint inconnu."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(body or "{}")
            source_limit = int(payload.get("source_limit") or 6)
            result = analyze_question(str(payload.get("query") or ""), source_limit)
            self.send_json(HTTPStatus.OK, result)
        except ValueError as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
        except Exception as exc:  # pragma: no cover - defensive local server boundary.
            self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(exc)})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CFDT Nexus - interface locale")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", help="ouvrir le navigateur local")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    server = ThreadingHTTPServer((args.host, args.port), NexusHandler)
    url = f"http://{args.host}:{args.port}/"
    print(f"Nexus interface locale: {url}")
    print("Aucun acces internet requis. Arreter avec Ctrl+C.")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArret de Nexus local.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
