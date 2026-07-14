#!/usr/bin/env python
"""Pre-commit style privacy check for payroll-related files.

The script is local-only. It scans tracked, modified, staged and untracked
candidate files unless explicit paths are provided with --path.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from automation.payroll import payroll_data_privacy_validator as privacy_validator  # noqa: E402


def git_names(*args: str) -> list[Path]:
    command = ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", *args]
    result = subprocess.run(command, cwd=REPO_ROOT, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return [REPO_ROOT / line.strip() for line in result.stdout.splitlines() if line.strip()]


def collect_git_candidate_paths() -> list[Path]:
    paths: set[Path] = set()
    for command in (
        ("ls-files", "--others", "--exclude-standard"),
        ("diff", "--name-only"),
        ("diff", "--cached", "--name-only"),
    ):
        paths.update(git_names(*command))
    return sorted(path for path in paths if path.exists())


def print_text_report(report: dict[str, object]) -> None:
    print(f"privacy_status={report['status']}")
    print(f"findings={report['findings_count']} blocked={report['blocked_count']} warnings={report['warning_count']}")
    for item in report.get("findings", []):
        if not isinstance(item, dict):
            continue
        print(
            " - "
            f"{item.get('risk_level')} "
            f"{item.get('category')} "
            f"{item.get('path')} "
            f"{item.get('masked_excerpt')} "
            f"{item.get('recommendation')}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check payroll files for private data before commit.")
    parser.add_argument("--path", action="append", default=[], help="Limit scan to one path. Can be repeated.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    args = parser.parse_args(argv)

    paths = [Path(value) for value in args.path] if args.path else collect_git_candidate_paths()
    report = privacy_validator.scan_paths(paths)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_text_report(report)
    return 1 if report["status"] == privacy_validator.STATUS_BLOCKED else 0


if __name__ == "__main__":
    raise SystemExit(main())
