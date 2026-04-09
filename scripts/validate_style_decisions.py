#!/usr/bin/env python3
"""Validate style-decisions.json against style-decisions.schema.json."""

from __future__ import annotations

import argparse
from pathlib import Path

from _style_decisions_lib import (
    DEFAULT_STYLE_DECISIONS,
    DEFAULT_STYLE_DECISIONS_SCHEMA,
    load_style_decisions,
    load_style_decisions_schema,
    validate_style_decisions_payload,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate style decisions schema.")
    parser.add_argument("--style", type=Path, default=DEFAULT_STYLE_DECISIONS)
    parser.add_argument("--schema", type=Path, default=DEFAULT_STYLE_DECISIONS_SCHEMA)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = load_style_decisions(args.style, default=None)
    schema = load_style_decisions_schema(args.schema)

    if payload is None:
        raise SystemExit(f"❌ Style decisions file not found: {args.style}")
    if schema is None:
        raise SystemExit(f"❌ Schema file not found: {args.schema}")

    errors = validate_style_decisions_payload(payload, schema)
    if errors:
        print("❌ style decisions schema validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("✓ style decisions schema validation passed")


if __name__ == "__main__":
    main()
