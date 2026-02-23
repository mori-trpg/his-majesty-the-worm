---
name: term-decision
description: 用語權衡 - 術語選擇與全文替換
user-invocable: true
disable-model-invocation: true
---

# Terminology Decision

Use `terminology-management` skill.

## Process

### 1. Identify Term

If `$ARGUMENTS` provided, focus on that term.
Otherwise, list terms needing decisions from:
- Inconsistent usage found in `term_read.py` output
- Missing glossary entries from `term_generate.py` output
- User-flagged terms

### 2. Present Options

For each term, show:
- Original English term
- Current usage(s) in documents
- Suggested translations with rationale
- How other games translate similar terms

### 3. User Decision

Ask user to choose:
1. Translation to use
2. Any context-specific variants
3. Reason for choice

### 4. Record Decision

Update `style-decisions.json`:

```json
{
  "term_category": {
    "decision": "選擇的翻譯",
    "alternatives": ["其他選項"],
    "reason": "選擇原因"
  }
}
```

Update `glossary.json` with final term.
For unmanaged terms, run `--cal` first:

```bash
uv run python scripts/term_edit.py --term "<TERM>" --cal
uv run python scripts/term_edit.py --term "<TERM>" --set-zh "<ZH>" --status approved --mark-term --notes "<REASON>"
```

### 5. Batch Replace

Find all occurrences across `docs/src/content/docs/`:
- Show preview of changes
- Confirm with user
- Apply replacements

After replacement, run:

```bash
uv run python scripts/term_read.py
```

### 6. Verify

Show summary of changes made.

## Example Usage

```
/term-decision
/term-decision Move
/term-decision "Basic Move"
```
