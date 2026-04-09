#!/usr/bin/env python3
"""Generate candidate terminology from markdown docs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from _term_lib import (
    CANDIDATE_CACHE,
    DEFAULT_GLOSSARY,
    PROJECT_ROOT,
    build_corpus,
    extract_candidates,
    load_glossary,
    resolve_root,
    save_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate term candidates.")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--glossary", type=Path, default=DEFAULT_GLOSSARY)
    parser.add_argument("--min-frequency", type=int, default=2)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.root = resolve_root(args.root)
    glossary = load_glossary(args.glossary)
    managed = {k.lower() for k in glossary.keys() if k != "_meta"}

    corpus, fingerprint = build_corpus(args.root)
    candidates = extract_candidates(corpus, min_frequency=args.min_frequency)
    filtered: list[dict[str, Any]] = []
    for c in candidates:
        if c["normalized"] in managed:
            continue
        filtered.append(c)
        if len(filtered) >= args.limit:
            break

    payload = {
        "root": str(args.root.relative_to(PROJECT_ROOT) if args.root.is_absolute() else args.root),
        "fingerprint": fingerprint,
        "min_frequency": args.min_frequency,
        "count": len(filtered),
        "candidates": filtered,
    }
    save_json(CANDIDATE_CACHE, payload)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"候選術語數量: {payload['count']} (min_frequency={args.min_frequency})")
    print("term\tcount")
    for item in filtered:
        print(f"{item['term']}\t{item['count']}")


if __name__ == "__main__":
    main()
