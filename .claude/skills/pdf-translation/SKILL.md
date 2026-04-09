---
name: pdf-translation
description: Use when processing PDF rulebooks, extracting raw markdown and image artifacts, or preparing source materials before `chapter-split`, `init-doc`, or translation setup.
user-invocable: true
disable-model-invocation: true
---

# PDF Translation Workflow

## Overview

Convert a source PDF into extracted markdown and image artifacts ready for chapter planning and translation setup.

**Core principle:** Extract cleanly and verify raw artifacts before chapter planning starts.

## The Process

### Step 1: Extract PDF

Run:

```bash
uv run python scripts/extract_pdf.py data/pdfs/<filename>.pdf
```

Expected outputs in `data/markdown/`:
- `<name>.md`
- `<name>_pages.md`
- `images/<name>/`

### Step 2: Validate Raw Outputs

Validate:
- expected files exist
- page markers are present in `_pages.md`
- image manifest exists when image extraction is enabled
- extraction text is readable enough for downstream planning

### Step 3: Re-extract or Fix Source if Needed

If extraction is garbled or page markers are broken:
- adjust source PDF
- re-run extraction
- do not continue until raw outputs are usable

### Step 4: Handoff

Hand off extracted outputs to:
- `chapter-split` for chapter/file planning and navigation generation
- `init-doc` when project-level decisions and terminology bootstrap are still pending

## Progress Sync Contract (Required)

1. Track extraction and raw validation steps in TodoWrite.
2. Mark extraction complete only after raw output validation.

## When to Stop and Ask for Help

Stop when:
- extraction output is unreadable/garbled
- page markers are missing or unreliable
- repeated extraction attempts still fail

## When to Revisit Earlier Steps

Return to Step 1 when:
- source PDF changes
- extraction options change

## Red Flags

Never:
- hand-build chapter mapping here when `chapter-split` is the correct next skill
- skip raw output validation before handoff

## Next Step

Continue with `chapter-split` or `/init-doc`.
