#!/usr/bin/env python3
"""
Draft management for translation workflow.

Commands:
    path <source>      Create empty draft file and register it in manifest; print draft path
    writeback <source> Write draft back to source using manifest metadata
    clean              Remove all drafts for the specified skill

Options:
    --skill  translate | super-translate  (default: translate)

Examples:
    DRAFT=$(uv run python scripts/draft.py path docs/src/content/docs/rules/basic.md)
    uv run python scripts/draft.py writeback docs/src/content/docs/rules/basic.md
    uv run python scripts/draft.py --skill super-translate path docs/src/content/docs/rules/basic.md
    uv run python scripts/draft.py clean
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
VALID_SKILLS = ("translate", "super-translate")
_FM_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)", re.DOTALL)


def _draft_path(source: Path, skill: str) -> Path:
    draft_root = ROOT / ".claude" / "skills" / skill / ".state" / "drafts"
    return draft_root / source


def _manifest_path(skill: str) -> Path:
    state_root = ROOT / ".claude" / "skills" / skill / ".state"
    return state_root / "draft-manifest.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_manifest(skill: str) -> dict:
    manifest_path = _manifest_path(skill)
    if not manifest_path.exists():
        return {"entries": {}}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _save_manifest(skill: str, manifest: dict) -> None:
    manifest_path = _manifest_path(skill)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _strip_draft_fields(content: str) -> str:
    """Remove legacy lines starting with _draft_ from YAML frontmatter."""
    match = _FM_RE.match(content)
    if not match:
        return content
    fm_lines = [l for l in match.group(1).splitlines() if not l.startswith("_draft_")]
    body = match.group(2)
    return "---\n" + "\n".join(fm_lines) + "\n---\n" + body


def cmd_path(source_str: str, skill: str) -> None:
    source = Path(source_str)
    draft = _draft_path(source, skill)
    draft.parent.mkdir(parents=True, exist_ok=True)
    if not draft.exists():
        draft.write_text("", encoding="utf-8")

    manifest = _load_manifest(skill)
    entries = manifest.setdefault("entries", {})
    entries[source_str] = {
        "source": source_str,
        "draft": str(draft.relative_to(ROOT).as_posix()),
        "updated": _now_iso(),
    }
    _save_manifest(skill, manifest)
    print(draft)


def cmd_writeback(source_str: str, skill: str) -> None:
    manifest = _load_manifest(skill)
    entry = manifest.get("entries", {}).get(source_str)
    if entry is None:
        print(f"Error: draft manifest entry not found for: {source_str}", file=sys.stderr)
        sys.exit(1)
    source = Path(source_str)
    draft_str = entry.get("draft")
    if not draft_str:
        print(f"Error: draft path missing in manifest for: {source_str}", file=sys.stderr)
        sys.exit(1)
    draft = ROOT / Path(draft_str)
    if not draft.exists():
        print(f"Error: draft not found: {draft}", file=sys.stderr)
        sys.exit(1)
    content = draft.read_text(encoding="utf-8")
    cleaned = _strip_draft_fields(content)
    abs_source = ROOT / source
    abs_source.parent.mkdir(parents=True, exist_ok=True)
    abs_source.write_text(cleaned, encoding="utf-8")
    draft.unlink()
    manifest["entries"].pop(source_str, None)
    _save_manifest(skill, manifest)
    print(f"Writeback: {draft.relative_to(ROOT)} → {source}", file=sys.stderr)


def cmd_clean(skill: str) -> None:
    draft_dir = ROOT / ".claude" / "skills" / skill / ".state" / "drafts"
    manifest_path = _manifest_path(skill)
    if draft_dir.exists():
        shutil.rmtree(draft_dir)
        print(f"Cleaned: {draft_dir.relative_to(ROOT)}", file=sys.stderr)
    else:
        print(f"No drafts found for skill '{skill}'", file=sys.stderr)
    if manifest_path.exists():
        manifest_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Draft management for translation workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--skill",
        choices=VALID_SKILLS,
        default="translate",
        help="Skill context (default: translate)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_path = sub.add_parser("path", help="Create draft file, register manifest entry, and print draft path")
    p_path.add_argument("source", help="Source file path relative to project root")

    p_wb = sub.add_parser("writeback", help="Write draft to source using manifest metadata")
    p_wb.add_argument("source", help="Source file path relative to project root")

    sub.add_parser("clean", help="Remove all drafts for the specified skill")

    args = parser.parse_args()

    if args.command == "path":
        cmd_path(args.source, args.skill)
    elif args.command == "writeback":
        cmd_writeback(args.source, args.skill)
    elif args.command == "clean":
        cmd_clean(args.skill)


if __name__ == "__main__":
    main()
