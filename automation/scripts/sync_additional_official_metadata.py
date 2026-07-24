"""Persist the reviewed CARSAT, France Chimie, ANACT and local-law catalogues."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from automation.official_knowledge.additional_metadata_feed import (
    synchronize_additional_metadata,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps([
        {
            "connector_name": item.connector_name,
            "document_count": item.document_count,
            "citation_count": item.citation_count,
            "last_synchronized_at": item.last_synchronized_at,
            "changes": list(item.changes),
        }
        for item in synchronize_additional_metadata(args.registry)
    ], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
