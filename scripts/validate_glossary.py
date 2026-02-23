#!/usr/bin/env python3
"""Validate glossary.json against glossary.schema.json."""

from __future__ import annotations

import argparse
from pathlib import Path

from jsonschema import Draft202012Validator

from _term_lib import DEFAULT_GLOSSARY, DEFAULT_GLOSSARY_SCHEMA, load_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate glossary schema.")
    parser.add_argument("--glossary", type=Path, default=DEFAULT_GLOSSARY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_GLOSSARY_SCHEMA)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    glossary = load_json(args.glossary, None)
    schema = load_json(args.schema, None)

    if glossary is None:
        raise SystemExit(f"❌ Glossary file not found: {args.glossary}")
    if schema is None:
        raise SystemExit(f"❌ Schema file not found: {args.schema}")

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(glossary), key=lambda e: list(e.path))
    if errors:
        print("❌ glossary schema validation failed:")
        for error in errors:
            path = ".".join(str(p) for p in error.path) or "<root>"
            print(f"- {path}: {error.message}")
        raise SystemExit(1)

    print("✓ glossary schema validation passed")


if __name__ == "__main__":
    main()
