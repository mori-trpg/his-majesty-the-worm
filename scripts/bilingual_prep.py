#!/usr/bin/env python3
"""Convert source English markdown to bilingual draft with placeholders.

Usage:
    uv run python scripts/bilingual_prep.py <source.md> <output_draft.md>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Regex patterns
_HEADING_RE = re.compile(r"^#{1,6}\s")
_TABLE_ROW_RE = re.compile(r"^\|")
_FENCE_RE = re.compile(r"^```")


def _ends_with_cjk(line: str) -> bool:
    """Return True if the last non-space character is CJK."""
    stripped = line.rstrip()
    if not stripped:
        return False
    return "\u4e00" <= stripped[-1] <= "\u9fff" or "\u3040" <= stripped[-1] <= "\u30ff"


def merge_soft_linebreaks(text: str) -> str:
    """Merge single newlines within paragraphs.

    English line endings get a space; CJK line endings get nothing.
    Double newlines (paragraph boundaries) are preserved.
    Fenced code blocks are left untouched.
    """
    paragraphs = text.split("\n\n")
    merged = []
    for para in paragraphs:
        # Leave fenced code blocks and other special blocks as-is
        first_line = para.splitlines()[0] if para else ""
        if _FENCE_RE.match(first_line) or _HEADING_RE.match(first_line) or _TABLE_ROW_RE.match(first_line):
            merged.append(para)
            continue
        lines = para.split("\n")
        if len(lines) <= 1:
            merged.append(para)
            continue
        result = lines[0]
        for line in lines[1:]:
            if _ends_with_cjk(result):
                result += line
            else:
                result += " " + line
        merged.append(result)
    return "\n\n".join(merged)


def _is_special_block(block: str) -> bool:
    """Return True for headings, tables, code fences, and blockquotes."""
    first_line = block.splitlines()[0] if block else ""
    return bool(
        _HEADING_RE.match(first_line)
        or _TABLE_ROW_RE.match(first_line)
        or _FENCE_RE.match(first_line)
        or first_line.startswith(">")
        or first_line.startswith("---")
    )


def _is_fenced_code(block: str) -> bool:
    return block.startswith("```") or block.startswith("~~~")


def build_bilingual_draft(source: str) -> str:
    """Build bilingual draft from source markdown.

    Each plain paragraph becomes:
        <!-- TODO: 翻譯 -->

        > original text

    Special blocks (headings, tables, code, blockquotes) are kept as-is.
    Frontmatter is preserved unchanged.
    """
    # Handle frontmatter
    frontmatter = ""
    body = source
    if source.startswith("---"):
        end = source.find("\n---", 3)
        if end != -1:
            frontmatter = source[: end + 4]
            body = source[end + 4:].lstrip("\n")

    # Preprocess soft line breaks
    body = merge_soft_linebreaks(body)

    # Split into blocks
    # We must handle fenced code blocks specially (they contain \n\n internally)
    blocks: list[str] = []
    in_fence = False
    current_block: list[str] = []

    for line in body.split("\n"):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            current_block.append(line)
            if not in_fence:
                blocks.append("\n".join(current_block))
                current_block = []
        elif in_fence:
            current_block.append(line)
        elif line == "":
            if current_block:
                blocks.append("\n".join(current_block))
                current_block = []
        else:
            current_block.append(line)

    if current_block:
        blocks.append("\n".join(current_block))

    # Build output
    output_parts: list[str] = []
    if frontmatter:
        output_parts.append(frontmatter)

    for block in blocks:
        if not block.strip():
            continue
        if _is_special_block(block) or _is_fenced_code(block):
            output_parts.append(block)
        else:
            # Plain paragraph: add placeholder + blockquote
            quoted = "\n".join(f"> {line}" for line in block.splitlines())
            output_parts.append(f"<!-- TODO: 翻譯 -->\n\n{quoted}")

    return "\n\n".join(output_parts) + "\n"


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: bilingual_prep.py <source.md> <output_draft.md>", file=sys.stderr)
        sys.exit(1)

    source_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not source_path.exists():
        print(f"❌ 找不到來源檔案: {source_path}", file=sys.stderr)
        sys.exit(1)

    source_text = source_path.read_text(encoding="utf-8")
    draft = build_bilingual_draft(source_text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(draft, encoding="utf-8")
    print(f"✓ 雙語 draft 已寫入: {output_path}")


if __name__ == "__main__":
    main()
