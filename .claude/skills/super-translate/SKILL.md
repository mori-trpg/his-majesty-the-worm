---
name: super-translate
description: 多 agent 翻譯與審查循環。Use when high-quality translation is needed with iterative review until all critical issues are resolved.
user-invocable: true
disable-model-invocation: true
---

# Super Translate（多 Agent 翻譯審查循環）

採用 **Generator → Reviewer → Refiner** 迭代循環，每個檔案最多執行 3 輪審查，確保翻譯符合所有規則後才輸出。

與 `/translate` 的差異：`/translate` 為單輪線性翻譯；`/super-translate` 加入審查 agent 與修正循環，適合需要高品質輸出的正式發布前翻譯。

## Prerequisites

- `glossary.json` exists with key terms
- Files exist in `docs/src/content/docs/`
- Run `/init-doc` first if not done

## Process

### 0. Terminology Preflight（必要）

翻譯任何檔案前：

1. Invoke `terminology-management` skill。
2. Run term read/validation flow：
   - Load `glossary.json`
   - Build or reuse full-site term index
   - Report unknown high-frequency candidates
3. Resolve critical terminology conflicts first, then continue translation.

```bash
uv run python scripts/term_read.py
```

### 1. Select Translation Mode

Read `style-decisions.json` and check `translation_mode.mode`：

**If mode is null (not set):**
- Use AskUserQuestion tool to ask user：
  - **Full Translation**：Translate all content completely, preserving the original structure and details
  - **Summary Translation**：Provide a concise translation that extracts key rules and omits examples and lengthy explanations
- Update `style-decisions.json` with user's choice

**If mode is already set:**
- Show current mode setting
- Ask if user wants to change (optional)

### 2. Select Target

If no `$ARGUMENTS`：
- List available files in `docs/src/content/docs/`
- Ask user which to translate

Scope options：
- Single file：`docs/src/content/docs/rules/basic.md`
- Section：`rules` (all files in section)
- All：`all`

### 3. Load Resources

Read：
- `glossary.json` — term mappings
- `style-decisions.json` — style choices, `translation_mode`, `proper_nouns.mode`, `document_format`

### 4. Multi-Agent Translation Loop

**對每個目標檔案執行以下循環。**

---

#### Phase A — Translator Agent

使用 **Agent tool** 啟動翻譯 subagent，任務如下：

```
Task: Translate the following markdown file from English to Traditional Chinese (zh-TW).

Resources provided:
- glossary.json: use all approved term mappings strictly
- style-decisions.json: apply translation_mode, document_format, proper_nouns.mode

Translation constraints:
- Output Traditional Chinese (zh-TW) only; no Simplified Chinese
- Use full-width punctuation in Chinese text：，。、；：「」『』（）……
- Preserve all markdown syntax (frontmatter, headings, lists, tables, code blocks, links)
- Translate frontmatter title and description; keep sidebar structure
- Apply Starlight components only if enabled in document_format
- Follow Mode-Specific Rules (full / summary) as set in style-decisions.json
- Translation must be manual; do not use script-based batch replacement

Output:
1. Complete translated markdown content
2. List of uncertain or new terms (if any) for glossary review
```

---

#### Phase B — Reviewer Agent

使用 **Agent tool** 啟動審查 subagent，任務如下：

```
Task: Review the translated markdown for rule compliance. Return a structured report.

Check CRITICAL issues (must fix before passing):
1. Terminology: any game term not matching glossary.json approved zh translation
2. Untranslated content: any English paragraph, heading, or sentence remaining
3. Forbidden words: any term listed in glossary entry's "forbidden" array
4. Simplified Chinese: any Simplified Chinese character or Mainland China-specific wording

Check MINOR issues (should fix if possible):
5. Punctuation: Chinese prose using half-width punctuation (,.) instead of full-width（，。）
6. Starlight components: use of components disabled in style-decisions.json.document_format
7. Heading hierarchy: any skipped heading levels (e.g. H2 → H4)
8. Frontmatter: missing title, description, or sidebar.order

Output format (structured):
{
  "pass": true/false,
  "critical": [
    { "type": "untranslated|terminology|forbidden|simplified", "location": "...", "detail": "..." }
  ],
  "minor": [
    { "type": "punctuation|component|heading|frontmatter", "location": "...", "detail": "..." }
  ]
}

Pass condition: critical = 0 AND minor ≤ 3
```

---

#### Phase C — Refiner Loop

```
iteration = 0
current_draft = output from Phase A

loop:
  run Reviewer Agent (Phase B) on current_draft

  if pass (critical=0, minor≤3) OR iteration >= 3:
    break

  launch Refiner Agent:
    Task: Fix the following issues in the translated markdown.
    Fix ALL critical issues first.
    Fix minor issues where possible without changing correctly translated content.
    Do not alter already correct translations.
    Issues to fix: <reviewer report>
    Input draft: <current_draft>
    Output: revised markdown

  current_draft = refiner output
  iteration += 1

if iteration >= 3 AND critical > 0:
  Display remaining critical issues to user
  Use AskUserQuestion:
    "已達 3 輪審查上限，仍有以下 critical 問題未解決。請選擇處理方式："
    Option A: 接受目前狀態，直接輸出（可稍後執行 /check-consistency 修正）
    Option B: 停止此檔案，改為手動修正後再繼續
```

---

### 5. New Terms

Translator Agent 遇到未知術語時：

1. 列入 uncertain terms 清單回報
2. 主 agent 收到後：
   - 判斷是否為真正的遊戲術語
   - 若 `proper_nouns.mode != keep_original` 且為出現 2+ 次的專有名詞，必須託管
   - 若是術語，執行 `term_edit.py --cal`，再更新 glossary
   - Re-run terminology check（優先使用 cache）
   - 以更新後的術語表重新執行 Phase A

```bash
uv run python scripts/term_edit.py --term "<TERM>" --cal
uv run python scripts/term_edit.py --term "<TERM>" --set-zh "<ZH>" --status approved --mark-term
uv run python scripts/term_read.py
```

### 6. Write Output

審查循環通過後，以翻譯結果覆寫原始檔案。

### 7. Progress Tracking

每個檔案完成後回報：

```
✓ super-translated: <path>
  iterations: N  |  critical fixed: X  |  minor fixed: Y
```

顯示下一個檔案或整體完成摘要。

---

## Reviewer Check Reference

| 類型 | 優先級 | 規則 |
|------|--------|------|
| 術語不一致 | Critical | 必須符合 `glossary.json` approved 翻譯 |
| 未翻譯段落 | Critical | 不得有殘留英文段落或標題 |
| 禁用詞 | Critical | 不得出現 glossary `forbidden` 詞彙 |
| 簡體字／大陸用語 | Critical | 僅允許繁體中文，台灣用語 |
| 標點符號 | Minor | 中文文本必須使用全形標點 |
| Starlight 組件 | Minor | 僅使用 `document_format` 中 enabled 的組件 |
| 標題層級跳躍 | Minor | 不得跳級（如 H2→H4） |
| Frontmatter 結構 | Minor | 必須包含 title、description、sidebar.order |

## Example Usage

```
/super-translate
/super-translate docs/src/content/docs/rules/basic.md
/super-translate rules
/super-translate all
```

## Output

翻譯檔案就地覆寫，並附帶每檔的審查迭代摘要。

完成後建議執行 `/check-consistency` 進行跨檔案術語一致性驗證。
