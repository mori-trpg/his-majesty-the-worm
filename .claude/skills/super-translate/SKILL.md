---
name: super-translate
description: Use when high-quality translation is needed for docs with iterative multi-agent review before final output.
user-invocable: true
disable-model-invocation: true
---

# Super Translate

## Overview

Translate with a fixed loop:
`translator -> source-reviewer -> quality-reviewer -> refiner`

Core principle:
- Source fidelity first
- Terminology consistency always
- Quality review only after source review passes

## The Process

### Step 1: Check Translation Progress

Read `data/translation-progress.json` to understand current state:
- Show which chapters are `not_started`, `in_progress`, `completed`, `reviewed`.
- If no arguments given, ask user in Traditional Chinese which chapters to translate next, using the progress file as reference.
- If `data/translation-progress.json` does not exist, remind user to run `/init-doc` first.

Status legend: `·` not_started  `▶` in_progress  `✓` completed  `★` reviewed

### Step 2: Terminology Preflight (Required)

Run before any translation:

```bash
uv run python scripts/term_read.py
```

Resolve critical terminology issues first.

### Step 3: Resolve Mode and Targets

1. Read `style-decisions.json.translation_mode.mode`.
2. If missing, ask user in Traditional Chinese:
   - **完整翻譯**：完整翻譯所有內容，保留原始結構與細節
   - **摘要翻譯**：以精簡方式翻譯重點規則，省略範例與冗長說明
3. Resolve scope: single file / section / all (cross-reference with Step 1 progress).

### Step 4: Initialize State

```bash
bash .claude/skills/super-translate/scripts/run_state.sh start \
  --targets <file1> <file2> ...
```

### Step 5: Execute Per File (Max 3 Iterations)

For each file:

1. Dispatch `translator`.
2. Dispatch `source-reviewer` on source + draft.
3. If source review fails, dispatch `refiner`, then re-run source review.
4. After source review passes, dispatch `quality-reviewer`.
5. If quality review fails, dispatch `refiner`, then re-run quality review.
6. Stop when:
   - all critical issues resolved and quality gate passes, or
   - 3 iterations reached.

If 3 iterations reached and critical issues remain, ask user in Traditional Chinese:
- **接受目前狀態，直接輸出（可稍後執行 /check-consistency 修正）**
- **停止此檔案，改為手動修正後再繼續**

### Step 6: Unknown Term Handling

When unknown terms appear:

```bash
uv run python scripts/term_edit.py --term "<TERM>" --cal
uv run python scripts/term_edit.py --term "<TERM>" --set-zh "<ZH>" --status approved --mark-term
uv run python scripts/term_read.py
```

Then re-run the affected file with the updated glossary.

### Step 7: Update State and Finalize

After each file:

1. Update session state:

```bash
bash .claude/skills/super-translate/scripts/run_state.sh update \
  --file <target_file> \
  --status pass \
  --critical-fixed <N> \
  --minor-fixed <M> \
  --remaining-critical <R>
```

Use `--status blocked` if unresolved critical issues remain.

2. Update translation progress — edit `data/translation-progress.json` and set the chapter's `status`:
   - `completed` if all critical issues resolved and quality gate passed
   - `in_progress` if blocked (unresolved critical issues remain)

After all files:

```bash
bash .claude/skills/super-translate/scripts/run_state.sh end
```

Run `/check-consistency` after completion.

## Agent Dispatch Contract

Use Task tool and set explicit `subagent_type` each time.

### translator

```text
subagent_type: translator
description: Translate <TARGET_FILE>
```

### source-reviewer

```text
subagent_type: source-reviewer
description: Source review <TARGET_FILE>
```

### quality-reviewer

```text
subagent_type: quality-reviewer
description: Quality review <TARGET_FILE>
```

### refiner

```text
subagent_type: refiner
description: Refine <TARGET_FILE> using reviewer findings
```

## Progress Reporting

After each file, report in Traditional Chinese:

```text
✓ super-translated: <path>
  iterations: N  |  critical fixed: X  |  minor fixed: Y
```

## Red Flags

Never:
- skip `source-reviewer` or `quality-reviewer`
- run `quality-reviewer` before `source-reviewer` passes
- overwrite source file with unresolved critical issues
- bypass glossary/style decisions
- use script-based bulk replacement to generate translated prose
