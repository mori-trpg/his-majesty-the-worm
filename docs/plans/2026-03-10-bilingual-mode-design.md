# 雙語翻譯模式設計

## 概覽

新增雙語翻譯模式，讓讀者在同一頁面看到中文翻譯與英文原文並存。中文為主要內容，英文原文以 blockquote 呈現於每段之後。

## 路由與目錄結構

兩種翻譯模式對應兩套獨立路由：

```
docs/src/content/docs/
  rules/                    → /rules/（純中文，預設無前綴）
  bilingual/
    rules/                  → /bilingual/rules/（雙語）
```

導覽列新增「雙語版」群組，與純中文版平行。

## 雙語文件格式

每段中文翻譯後接英文原文（blockquote）：

```markdown
---
title: 戰鬥
description: 戰鬥規則雙語版
sidebar:
  order: 10
bilingual: true
---

當角色進行攻擊時，擲骰決定結果。

> When a character attacks, they roll dice.

攻擊方將結果與目標防禦值比較。

> The attacker compares the result to the target's defense.
```

## 翻譯模式選擇

在 `/init-doc` 流程中新增問題，讓使用者選擇翻譯模式：

- **純中文翻譯**：使用現有 `/translate` 或 `/super-translate` 流程
- **雙語模式**：使用新的 `/bilingual-translate` 流程

決定存入 `style-decisions.json`：

```json
{
  "translation_mode": {
    "decision": "bilingual",
    "alternatives": ["zh_only"],
    "reason": "使用者在 init-doc 選擇雙語模式"
  }
}
```

兩者互斥，不支援同時建立兩種模式。

## 新增腳本：`bilingual_prep.py`

將來源英文 .md 轉換為帶佔位符的雙語 draft。

**流程：**

1. **預處理軟換行**：合併段落內的單個 `\n`
   - 英文行尾 → 加空格（避免單字黏合）
   - 中文行尾 → 不加空格
   - 保留 `\n\n` 作為段落邊界
2. **跳過特殊區塊**：heading、table、code block 不加佔位符
3. **產出 draft**：每段英文前插入 `<!-- TODO: 翻譯 -->` 佔位符

**輸出格式：**

```markdown
<!-- TODO: 翻譯 -->

> When a character attacks, they roll dice.

<!-- TODO: 翻譯 -->

> The attacker compares the result to the target's defense.
```

**指令：**

```bash
uv run python scripts/bilingual_prep.py <SOURCE_FILE> <OUTPUT_DRAFT>
```

## 新增技能：`/bilingual-translate`

單輪翻譯流程，不走 super-translate 的多輪 review。

**工作流程：**

1. 前置檢查：glossary + style-decisions 存在，術語 preflight 通過
2. 對每個目標檔案執行 `bilingual_prep.py`，產出帶佔位符的 draft
3. 逐段翻譯：將 `<!-- TODO: 翻譯 -->` 替換為對應中文翻譯
4. 單輪自我審查：術語、標點、未翻譯段落
5. 寫入 `docs/src/content/docs/bilingual/<path>`
6. 更新 `translation-progress-bilingual.json`（獨立進度追蹤）
7. 批次 commit：`progress (bilingual): X/Y`

**來源檔案：** 直接讀取 `data/markdown/` 原始英文來源。

## `chapter-split` 調整

`chapters.json` 新增 `mode` 欄位：

```json
{
  "mode": "bilingual",
  "output_dir": "docs/src/content/docs/bilingual",
  ...
}
```

`chapter-split` 技能從 `style-decisions.json` 讀取 `translation_mode`，自動設定 `output_dir`。分割邏輯本身不變，只有輸出路徑改變。

`split_chapters.py` 和 `generate_nav.py` 依 `mode` 欄位決定輸出路徑與導覽群組名稱。

## 影響範圍

| 元件 | 變動 |
|------|------|
| `init-doc` 技能 | 新增翻譯模式選擇問題 |
| `chapter-split` 技能 | 讀取 `translation_mode`，設定 `output_dir` |
| `chapters.json` | 新增 `mode` 欄位 |
| `split_chapters.py` | 支援 `bilingual` output dir |
| `generate_nav.py` | 支援雙語導覽群組 |
| `scripts/bilingual_prep.py` | 全新腳本 |
| `.claude/skills/bilingual-translate/` | 全新技能 |
| `translation-progress-bilingual.json` | 全新進度追蹤檔案 |
| `/translate`、`/super-translate` | 不變（純中文模式繼續使用） |
