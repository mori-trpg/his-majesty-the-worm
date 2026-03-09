---
name: init-doc
description: Use when initializing a translation project from extraction through glossary, chapter mapping, and progress tracking.
user-invocable: true
disable-model-invocation: true
---

# Initialize Document Translation

## Overview

Initialize translation baseline from PDF extraction to chaptered docs, style decisions, glossary, and progress tracker.

**Core principle:** Build a deterministic, verifiable baseline before any large-scale translation.

## Interaction Rules

- All user interaction must be Traditional Chinese (zh-TW).
- AskUserQuestion prompts must be Traditional Chinese.
- Do not use Simplified Chinese in user-facing text.

## The Process

### Step 1: Cleanup and Source Validation

Run cleanup:

```bash
uv run python scripts/clean_sample_data.py --yes
```

Then resolve source PDF from `$ARGUMENTS` or ask user in Traditional Chinese. Ensure source is under `data/pdfs/`.

### Step 2: Create TodoWrite

Create items for:
- extraction
- formatting decisions
- image and theme setup
- terminology bootstrap
- chapter mapping
- progress tracker creation
- final handoff gate

### Step 3: Extract and Validate Raw Outputs

Run:

```bash
uv run python scripts/extract_pdf.py <pdf_path>
```

Validate outputs:
- `data/markdown/<name>.md`
- `data/markdown/<name>_pages.md`
- `data/markdown/images/<name>/`

### Step 4: Cropping Review and Optional Split

Review readability and completeness.
If needed, split large source into parts and re-extract until clean.

### Step 5: Confirm Document Formatting Decisions

Summarize content to user in Traditional Chinese:

```text
書本內容概覽：
- 主要內容類型：[規則說明、範例場景、角色選項...]
- 特殊結構：[大量表格、骰表、設計者備註...]
- 建議可使用的格式化元件：[...]
```

Collect formatting choices (Traditional Chinese):
- layout profile for extraction (`auto` / `single-column` / `double-column`)
- aside mapping (`note/tip/caution/danger`)
- card/tabs usage
- table/dice-table conventions

Persist via script:

```bash
uv run python scripts/style_decisions.py init
uv run python scripts/style_decisions.py set-document-format \
  --layout-profile "<auto|single-column|double-column>" \
  --aside-note "<note_component>" \
  --aside-tip "<tip_component>" \
  --aside-caution "<caution_component>" \
  --aside-danger "<danger_component>" \
  --cards-usage "<cards_usage_note>" \
  --tabs-usage "<tabs_usage_note>" \
  --tables-convention "<table_note>" \
  --dice-tables-convention "<dice_table_note>"
uv run python scripts/validate_style_decisions.py
```

### Step 6: Select Images, Theme, and Homepage Content

1. Ask user to assign extracted images for hero/background/og.
2. Copy and resize where needed.
3. Ask theme decisions in Traditional Chinese (mode/overlay/palette).
4. Update `docs/src/styles/custom.css` and persist style decisions.
5. Persist image retention decision via `uv run python scripts/style_decisions.py set-images --preserve-images <true_or_false>`.
6. Ask for site meta in Traditional Chinese and persist via `uv run python scripts/style_decisions.py set-site ...`.
7. Ask for copyright and credits in Traditional Chinese:
   - Copyright notice text（例：`© 2024 Author Name. All rights reserved.`）
   - Credits entries as role → name pairs（例：原作者、翻譯、美術設計等）
   - Whether to show each section on the homepage
8. Persist via:

```bash
uv run python scripts/style_decisions.py set-copyright \
  --text "<USER_INPUT>" \
  --show-on-homepage <true_or_false>
uv run python scripts/style_decisions.py set-credits \
  --entry "原作者:..." \
  --entry "翻譯:..." \
  --show-on-homepage <true_or_false>
```

9. Ask whether there are any translation-wide notes the translator must always follow, and persist each note via:

```bash
uv run python scripts/style_decisions.py add-translation-note \
  --key "<short_key>" \
  --topic "<optional_topic>" \
  --note "<USER_INPUT>"
```

10. Run `uv run python scripts/validate_style_decisions.py`.

`generate_nav.py` will render these as **## 版權宣告** and **## 製作名單** sections on the homepage. If neither is provided, a generic fallback disclaimer is used.

### Step 7: Build Terminology Baseline

1. Generate candidates:

```bash
uv run python scripts/term_generate.py --min-frequency 2
```

2. Ask user to confirm key terms and proper noun policy.
3. Update glossary safely:

```bash
uv run python scripts/term_edit.py --term "<TERM>" --set-zh "<ZH>" --status approved --mark-term
uv run python scripts/validate_glossary.py
uv run python scripts/term_read.py --fail-on-missing --fail-on-forbidden
```

### Step 8: Chapter Split and Navigation

Invoke `chapter-split` skill instead of duplicating split logic here.

Required handoff to `chapter-split`:
1. Source is the extracted `_pages.md` file from this init run.
2. Reuse the current image retention decision.
3. Reuse the formatting and terminology decisions already completed in earlier steps.
4. Generate `chapters.json`, split docs output, and regenerate navigation.
5. If `chapter-split` reports unresolved critical issues, stop `init-doc` and resolve them before continuing.

### Step 9: Create Translation Progress Tracker

Create `data/translation-progress.json` from `chapters.json`:

```bash
uv run python scripts/init_create_progress.py --force
```

Tracker contract:
- chapter ids derived from output file paths
- source page ranges mapped from chapter config
- initial status `not_started`
- `_meta` fields (`updated`, `total_chapters`, `completed`)

### Step 10: Final Gate and Handoff (Fail-Closed)

Run one-shot handoff gate:

```bash
uv run python scripts/init_handoff_gate.py
```

If any gate fails, stop and fix before completion.

## Progress Sync Contract (Required)

1. Keep TodoWrite updated at every step.
2. Mark blockers immediately and include failing command/context.
3. Close TodoWrite only after final gate passes.

## When to Stop and Ask for Help

Stop when:
- source extraction repeatedly fails
- `chapter-split` cannot produce a usable config
- glossary validation cannot be resolved safely
- docs build fails with unclear root cause

## When to Revisit Earlier Steps

Return to earlier steps when:
- user changes formatting/theme policy
- user changes proper noun strategy
- source markdown changes enough to invalidate page mapping

## Red Flags

Never:
- continue after failed validation gates
- continue after failed `chapter-split` handoff
- skip user confirmation for formatting/proper noun policy
- leave progress tracker uninitialized at handoff

## Next Step

Continue with `/translate` or `/super-translate`.

## Example Usage

```text
/init-doc
/init-doc data/pdfs/rulebook.pdf
```
