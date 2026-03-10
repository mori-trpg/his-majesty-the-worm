# Bilingual Mode Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add bilingual translation mode where Chinese is primary and English source appears as blockquotes after each paragraph.

**Architecture:** New `bilingual` mode added to `translation_mode` enum; `bilingual_prep.py` converts raw English markdown to placeholder-draft; new `bilingual-translate` skill handles single-pass translation; `chapter-split` reads mode to set output dir; `init-doc` asks mode at setup.

**Tech Stack:** Python 3.11+ (uv), Astro/Starlight, JSON schema

**Design doc:** `docs/plans/2026-03-10-bilingual-mode-design.md`

---

### Task 1: Add `bilingual` to schema and lib

**Files:**
- Modify: `style-decisions.schema.json:20` (translation_mode.mode enum)
- Modify: `scripts/_style_decisions_lib.py:18-27` (TRANSLATION_MODE_OPTIONS)

**Step 1: Update schema enum**

In `style-decisions.schema.json`, change:
```json
"mode": { "enum": ["full", "summary"] }
```
to:
```json
"mode": { "enum": ["full", "summary", "bilingual"] }
```

**Step 2: Add bilingual option to lib**

In `scripts/_style_decisions_lib.py`, add to `TRANSLATION_MODE_OPTIONS`:
```python
"bilingual": {
    "name": "雙語模式",
    "description": "中文翻譯為主，英文原文以 blockquote 附於每段之後",
},
```

**Step 3: Verify schema validation still passes**

```bash
uv run python scripts/validate_style_decisions.py
```
Expected: exits 0 (or "file not found" if no style-decisions.json yet — both OK)

**Step 4: Commit**

```bash
git add style-decisions.schema.json scripts/_style_decisions_lib.py
git commit -m "feat: add bilingual translation mode to schema and lib"
```

---

### Task 2: Add `set-translation-mode` CLI command

**Files:**
- Modify: `scripts/style_decisions.py` (add cmd_set_translation_mode + subparser)

**Step 1: Write failing test**

Create `tests/test_style_decisions_bilingual.py`:
```python
import subprocess, json, tempfile, shutil
from pathlib import Path

def test_set_translation_mode_bilingual(tmp_path):
    style = tmp_path / "style-decisions.json"
    schema = Path("style-decisions.schema.json")
    # Init first
    subprocess.run(
        ["uv", "run", "python", "scripts/style_decisions.py", "init",
         "--style", str(style), "--schema", str(schema)],
        check=True
    )
    # Set bilingual mode
    subprocess.run(
        ["uv", "run", "python", "scripts/style_decisions.py", "set-translation-mode",
         "--mode", "bilingual",
         "--reason", "test",
         "--style", str(style), "--schema", str(schema)],
        check=True
    )
    data = json.loads(style.read_text())
    assert data["translation_mode"]["mode"] == "bilingual"
```

**Step 2: Run test to verify it fails**

```bash
uv run python -m pytest tests/test_style_decisions_bilingual.py -v
```
Expected: FAIL with "unrecognized arguments: set-translation-mode"

**Step 3: Implement `cmd_set_translation_mode`**

In `scripts/style_decisions.py`, add after `cmd_set_images`:
```python
def cmd_set_translation_mode(args: argparse.Namespace) -> None:
    patch: dict[str, Any] = {
        "translation_mode": {"mode": args.mode}
    }
    if args.reason:
        patch["translation_mode"]["reason"] = args.reason
    merge_and_save(args.style, args.schema, patch)
    print(f"✓ 已設定翻譯模式: {args.mode}")
```

Then add subparser in `main()` (after the existing `set-images` subparser):
```python
p_mode = sub.add_parser("set-translation-mode", help="設定翻譯模式")
p_mode.add_argument("--mode", required=True, choices=["full", "summary", "bilingual"])
p_mode.add_argument("--reason", default=None)
p_mode.set_defaults(func=cmd_set_translation_mode)
```

**Step 4: Run test to verify it passes**

```bash
uv run python -m pytest tests/test_style_decisions_bilingual.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/style_decisions.py tests/test_style_decisions_bilingual.py
git commit -m "feat: add set-translation-mode CLI command"
```

---

### Task 3: Create `bilingual_prep.py`

**Files:**
- Create: `scripts/bilingual_prep.py`
- Create: `tests/test_bilingual_prep.py`

**Step 1: Write failing tests**

Create `tests/test_bilingual_prep.py`:
```python
import sys
sys.path.insert(0, "scripts")
from bilingual_prep import merge_soft_linebreaks, build_bilingual_draft

def test_merge_soft_linebreaks_english():
    # English line break gets a space
    text = "line one\nline two"
    assert merge_soft_linebreaks(text) == "line one line two"

def test_merge_soft_linebreaks_chinese():
    # Chinese line break gets no space
    text = "第一行\n第二行"
    assert merge_soft_linebreaks(text) == "第一行第二行"

def test_merge_soft_linebreaks_preserves_paragraph():
    text = "para one\n\npara two"
    assert merge_soft_linebreaks(text) == "para one\n\npara two"

def test_build_bilingual_draft_plain_paragraph():
    source = "When a character attacks, they roll dice."
    result = build_bilingual_draft(source)
    assert "<!-- TODO: 翻譯 -->" in result
    assert "> When a character attacks, they roll dice." in result

def test_build_bilingual_draft_heading_no_placeholder():
    source = "## Combat\n\nSome rules here."
    result = build_bilingual_draft(source)
    # Heading should have no placeholder
    lines = result.splitlines()
    heading_idx = next(i for i, l in enumerate(lines) if l.startswith("## Combat"))
    assert lines[heading_idx - 1] != "<!-- TODO: 翻譯 -->" if heading_idx > 0 else True

def test_build_bilingual_draft_code_block_no_placeholder():
    source = "Text before.\n\n```\ncode here\n```\n\nText after."
    result = build_bilingual_draft(source)
    # Code block should not have placeholder prepended
    assert result.count("<!-- TODO: 翻譯 -->") == 2  # only text_before and text_after

def test_build_bilingual_draft_table_no_placeholder():
    source = "| A | B |\n|---|---|\n| 1 | 2 |"
    result = build_bilingual_draft(source)
    assert "<!-- TODO: 翻譯 -->" not in result
```

**Step 2: Run tests to verify they fail**

```bash
uv run python -m pytest tests/test_bilingual_prep.py -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'bilingual_prep'"

**Step 3: Implement `bilingual_prep.py`**

Create `scripts/bilingual_prep.py`:
```python
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
    """
    paragraphs = text.split("\n\n")
    merged = []
    for para in paragraphs:
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
```

**Step 4: Run tests to verify they pass**

```bash
uv run python -m pytest tests/test_bilingual_prep.py -v
```
Expected: all PASS

**Step 5: Commit**

```bash
git add scripts/bilingual_prep.py tests/test_bilingual_prep.py
git commit -m "feat: add bilingual_prep.py for draft generation"
```

---

### Task 4: Update `split_chapters.py` for bilingual output dir

**Files:**
- Modify: `scripts/split_chapters.py` (read `mode` from config, derive output_dir)

**Step 1: Write failing test**

Add to `tests/test_bilingual_prep.py` (or create `tests/test_split_chapters_bilingual.py`):
```python
import subprocess, json, tempfile
from pathlib import Path

def test_split_chapters_bilingual_output_dir(tmp_path):
    """chapters.json with mode=bilingual should write to bilingual/ subdir."""
    # Create minimal chapters.json pointing to a tiny source
    source = tmp_path / "source.md"
    source.write_text("<!-- page 1 -->\n# Test\n\nHello world.\n")
    out_dir = tmp_path / "docs" / "src" / "content" / "docs"
    cfg = {
        "source": str(source),
        "output_dir": str(out_dir),
        "mode": "bilingual",
        "chapters": {
            "rules": {
                "title": "規則",
                "order": 1,
                "files": {
                    "index": {
                        "title": "規則總覽",
                        "description": "test",
                        "pages": [1, 1]
                    }
                }
            }
        }
    }
    cfg_file = tmp_path / "chapters.json"
    cfg_file.write_text(json.dumps(cfg))
    result = subprocess.run(
        ["uv", "run", "python", "scripts/split_chapters.py", "--config", str(cfg_file)],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    bilingual_dir = out_dir / "bilingual" / "rules"
    assert bilingual_dir.exists(), f"Expected {bilingual_dir} to exist"
```

**Step 2: Run test to verify it fails**

```bash
uv run python -m pytest tests/test_split_chapters_bilingual.py -v
```
Expected: FAIL (bilingual dir not created)

**Step 3: Read `load_config` in `split_chapters.py`**

Read `scripts/split_chapters.py:59-90` to understand config loading, then modify the output_dir resolution logic:

After `load_config` returns, if `config.get("mode") == "bilingual"`, prepend `"bilingual"` to the output path:

```python
# In the main split execution, after loading config:
output_dir = Path(config["output_dir"])
if config.get("mode") == "bilingual":
    output_dir = output_dir / "bilingual"
    config["output_dir"] = str(output_dir)
```

Find the exact location where `output_dir` is first resolved in `split_chapters.py` (search for `output_dir`) and apply the patch there.

**Step 4: Run test to verify it passes**

```bash
uv run python -m pytest tests/test_split_chapters_bilingual.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/split_chapters.py tests/test_split_chapters_bilingual.py
git commit -m "feat: split_chapters respects mode=bilingual output dir"
```

---

### Task 5: Update `generate_nav.py` for bilingual sidebar

**Files:**
- Modify: `scripts/generate_nav.py` (read `mode` from chapters.json, add bilingual group)

**Step 1: Understand current sidebar generation**

Read `scripts/generate_nav.py:148-173`. Current `generate_sidebar_entries` uses `autogenerate: { directory: '<slug>' }`. For bilingual mode, the directory should be `bilingual/<slug>`.

**Step 2: Update `generate_sidebar_entries`**

```python
def generate_sidebar_entries(chapters: dict, mode: str = "zh_only") -> str:
    """Generate JS sidebar array entries."""
    sections = sorted_sections(chapters)
    entries = []
    for slug, section in sections:
        title = section["title"]
        directory = f"bilingual/{slug}" if mode == "bilingual" else slug
        entries.append(
            f"\t\t\t\t{{\n"
            f"\t\t\t\t\tlabel: '{title}',\n"
            f"\t\t\t\t\tautogenerate: {{ directory: '{directory}' }},\n"
            f"\t\t\t\t}}",
        )
    return ",\n".join(entries)
```

**Step 3: Pass mode to `generate_sidebar_entries` in `main()`**

Read `scripts/generate_nav.py:176-200` to find where `generate_sidebar_entries` is called in `main()`. Pass `mode` from loaded chapters:

```python
chapters_data = load_json(CHAPTERS_FILE)
chapters = chapters_data.get("chapters", chapters_data)  # support both flat and nested
mode = chapters_data.get("mode", "zh_only")
# ... then pass mode to generate_sidebar_entries(chapters, mode=mode)
```

**Step 4: Verify manually**

```bash
# Quick smoke test (no chapters.json needed — just verify import works)
uv run python -c "import generate_nav; print('OK')"
```

**Step 5: Commit**

```bash
git add scripts/generate_nav.py
git commit -m "feat: generate_nav supports bilingual sidebar directory prefix"
```

---

### Task 6: Update `chapter-split` skill

**Files:**
- Modify: `.claude/skills/chapter-split/SKILL.md`

**Step 1: Read current skill**

Already read. Find Step 4 ("Finalize Config and Image Policy") which writes `chapters.json`.

**Step 2: Add bilingual mode section**

In Step 4, before writing final config, add:

```markdown
#### Bilingual mode

Read `style-decisions.json` for `translation_mode.mode`.
If `mode == "bilingual"`, add to config:

```json
{
  "mode": "bilingual"
}
```

`split_chapters.py` will resolve the final output path as `<output_dir>/bilingual/`.
Do NOT manually set `output_dir` to include `bilingual/` — the script handles that.
```

Also update Step 7 (Handoff): note that if mode is bilingual, next step is `/bilingual-translate`, not `/translate` or `/super-translate`.

**Step 3: Commit**

```bash
git add .claude/skills/chapter-split/SKILL.md
git commit -m "feat: chapter-split skill sets mode=bilingual in chapters.json"
```

---

### Task 7: Update `init-doc` skill

**Files:**
- Modify: `.claude/skills/init-doc/SKILL.md`

**Step 1: Add translation mode question to Step 5**

In Step 5 ("Confirm Document Formatting Decisions"), after collecting formatting choices, add a new question:

```markdown
Ask user to choose translation mode (Traditional Chinese):

```text
請選擇翻譯模式：
A. 純中文翻譯：完整翻譯所有內容，僅保留中文
B. 雙語模式：中文翻譯為主，英文原文以 blockquote 附於每段之後
```

Persist via:

```bash
uv run python scripts/style_decisions.py set-translation-mode \
  --mode "<full|bilingual>" \
  --reason "<USER_INPUT_OR_DEFAULT>"
```
```

**Step 2: Update Step 9 (Progress Tracker)**

If mode is `bilingual`, note that progress tracker file will be `data/translation-progress-bilingual.json` (created by `/bilingual-translate` on first run, not during init).

**Step 3: Update "Next Step" section**

Change:
```
Continue with `/translate` or `/super-translate`.
```
to:
```
If `translation_mode.mode == "bilingual"`, continue with `/bilingual-translate`.
Otherwise, continue with `/translate` or `/super-translate`.
```

**Step 4: Commit**

```bash
git add .claude/skills/init-doc/SKILL.md
git commit -m "feat: init-doc skill asks translation mode during setup"
```

---

### Task 8: Create `bilingual-translate` skill

**Files:**
- Create: `.claude/skills/bilingual-translate/SKILL.md`

**Step 1: Create skill file**

Create `.claude/skills/bilingual-translate/SKILL.md`:

```markdown
---
name: bilingual-translate
description: Use when translating in bilingual mode — produces Chinese primary + English blockquote markdown. Single-pass, no multi-round review. Requires translation_mode=bilingual in style-decisions.json.
user-invocable: true
disable-model-invocation: true
---

# Bilingual Translate

## Overview

Single-pass bilingual translation. Produces documents where each Chinese paragraph is followed by the English original as a blockquote.

**Output format:**

```markdown
中文翻譯段落文字。

> Original English paragraph text here.
```

**Core principle:** Draft-first with bilingual_prep.py placeholders. Write directly to bilingual output dir. No multi-round review loop.

## Task Initialization (MANDATORY)

Before ANY action, create tasks using TaskCreate:
- One task per target file
- One task for batch checkpoint
- One task for final verification

## The Process

### Step 1: Resolve Scope and Preconditions

1. Verify required files:
   - `glossary.json`
   - `style-decisions.json` with `translation_mode.mode == "bilingual"`
   - `chapters.json` with `mode == "bilingual"`
   If any missing or mode mismatch, stop and ask user to run `/init-doc` first.

2. Resolve target files from `$ARGUMENTS` or auto-select from `translation-progress-bilingual.json` (if it exists). If the progress file does not exist, treat all files from `chapters.json` as `not_started`.

3. Display selected files to user in Traditional Chinese before proceeding.

### Step 2: Terminology Preflight (Fail-Closed)

```bash
uv run python scripts/validate_glossary.py
uv run python scripts/term_read.py --fail-on-missing --fail-on-forbidden
```

If preflight fails, stop and fix terminology first.

### Step 3: Prepare Bilingual Draft

For each target file, determine the source English markdown path from `data/markdown/` (the `_pages.md` source referenced in `chapters.json`).

Get the output path from `chapters.json`: `<output_dir>/bilingual/<slug>/index.md` (or the mapped file path).

Run bilingual_prep.py to generate the draft with placeholders:

```bash
uv run python scripts/bilingual_prep.py <SOURCE_FILE> <DRAFT_FILE>
```

Where `<DRAFT_FILE>` is a temporary path in `.claude/skills/bilingual-translate/.state/drafts/`.

### Step 4: Translate Per File

For each target file:

1. Mark task `in_progress`
2. Read draft (with `<!-- TODO: 翻譯 -->` placeholders), `glossary.json`, and `style-decisions.json`
3. Replace each `<!-- TODO: 翻譯 -->` with the Chinese translation of the following blockquote paragraph
4. Update frontmatter `title` to Traditional Chinese; keep `bilingual: true`
5. Self-review (single pass):
   - Any `<!-- TODO: 翻譯 -->` left untranslated?
   - Glossary violations?
   - Full-width punctuation correct?
   - English blockquotes preserved exactly (no modification to `>` lines)?
6. Write final file to `docs/src/content/docs/bilingual/<path>`
7. Update `translation-progress-bilingual.json` (create if absent):
   - Set file status to `completed`
   - Update `_meta.completed` and `_meta.updated`

### Step 5: Batch Checkpoint Commit

After all files in batch are processed:

```bash
git add docs/src/content/docs/bilingual/ data/
git commit -m "progress (bilingual): X/Y"
```

### Step 6: Final Verification

```bash
uv run python scripts/validate_glossary.py
uv run python scripts/term_read.py --fail-on-missing --fail-on-forbidden
```

## Red Flags

| Thought | Reality |
|---------|---------|
| "Modify the English blockquote lines" | Never alter `>` lines. They are source text. |
| "Skip bilingual_prep, I'll format manually" | bilingual_prep ensures consistent structure. Always use it. |
| "translation-progress-bilingual.json doesn't exist, skip tracking" | Create it on first run. |
| "One file done, no need for checkpoint" | Every batch gets a commit. |

## Example Usage

```text
/bilingual-translate
/bilingual-translate docs/src/content/docs/bilingual/rules/combat.md
/bilingual-translate all
```
```

**Step 2: Register in CLAUDE.md Quick Reference**

In `CLAUDE.md`, add to the Slash Skills table:
```
| `/bilingual-translate` | Single-pass bilingual translate (中文 + 英文 blockquote) |
```

**Step 3: Commit**

```bash
git add .claude/skills/bilingual-translate/SKILL.md CLAUDE.md
git commit -m "feat: add bilingual-translate skill"
```

---

## Verification Checklist

After all tasks complete:

```bash
# 1. Schema validation
uv run python scripts/validate_style_decisions.py

# 2. Set bilingual mode and confirm
uv run python scripts/style_decisions.py set-translation-mode --mode bilingual --reason "test"
uv run python scripts/validate_style_decisions.py

# 3. bilingual_prep smoke test
echo "Test paragraph.\n\nAnother paragraph." > /tmp/test_source.md
uv run python scripts/bilingual_prep.py /tmp/test_source.md /tmp/test_output.md
cat /tmp/test_output.md

# 4. Run all tests
uv run python -m pytest tests/ -v -k "bilingual"
```

Expected: all green.
