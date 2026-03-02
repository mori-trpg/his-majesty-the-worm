---
name: init-doc
description: Initial summary - initialize the document translation project, build glossary and chapter structure
user-invocable: true
disable-model-invocation: true
---

# Initialize Document Translation

Use `pdf-translation` and `terminology-management` skills.

## Interaction Rules

- Always interact with the user in Traditional Chinese (zh-TW).
- All AskUserQuestion prompts and conversational text shown to the user must be in Traditional Chinese.
- Do not use Simplified Chinese.

## Process

### 0. Clean Sample Data (Required)

Before initialization, clear template/sample outputs:

```bash
uv run python scripts/clean_sample_data.py --yes
```

This cleanup removes:
- `data/markdown/*` (extracted markdown/images)
- `docs/src/content/docs/**/*.md|.mdx` (template docs content)
- resets `glossary.json` to an empty glossary skeleton (`_meta` only)

It does **not** remove `data/pdfs/*`.

### 1. Locate PDF

If no `$ARGUMENTS` provided, ask user for PDF location in `data/pdfs/`.

### 2. Extract Content

```bash
uv run python scripts/extract_pdf.py <pdf_path>
```

Review output in `data/markdown/`:
- `<name>.md` - clean version
- `<name>_pages.md` - with page markers

### 3. Review PDF Cropping and Split into Manageable Parts

After PDF cropping is completed, review the cropped result before continuing:

1. Inspect the cropped output for readability issues:
   - text clipped at margins
   - missing headers/footers needed for context
   - broken diagrams/tables
2. If the cropped PDF is too large, split it into suitable parts:
   - split by natural chapter boundaries when possible
   - keep each part at a manageable size (recommended: ~15-30 pages per part)
3. Save split PDF parts with clear names (for example `part-01-intro.pdf`, `part-02-core-rules.pdf`).
4. Re-run extraction for each split part if needed, and ensure resulting markdown files are complete.

### 4. Review Content and Decide Document Formatting

After extraction, briefly skim the extracted markdown to understand the book's structure, then confirm formatting standards with the user.

#### 4.1 Quick Content Review

Read through the extracted markdown to identify:
- Content types present (rules, examples, tips, warnings, tables, random encounter tables, character options, etc.)
- Structural patterns (heavy list usage, many tables, sidebar notes, designer commentary, etc.)
- Special content that could benefit from Starlight components

Summarize findings to user:

```
書本內容概覽：
- 主要內容類型：[規則說明、範例場景、角色選項...]
- 特殊結構：[大量表格、骰表、設計者備註...]
- 建議可使用的格式化元件：[...]
```

#### 4.2 Confirm Formatting Standards

Use AskUserQuestion to present available Starlight/Markdown features and let user decide which to use:

**Starlight Asides (callouts)**:
- `:::note[標題]` — 補充說明
- `:::tip[標題]` — 遊戲技巧與建議
- `:::caution[標題]` — 注意事項
- `:::danger[標題]` — 嚴重警告

**Card Grid**:
- 適合呈現角色職業、物品列表等並列內容
- 需 import `<CardGrid>` 和 `<Card>`

**Tabs**:
- 適合替代規則、不同人數玩法等切換式內容
- 需 import `<Tabs>` 和 `<TabItem>`

**Tables**:
- 結構化數據、屬性表、裝備列表

**Dice Tables**:
- 隨機遭遇表、戰利品表等

Ask user to confirm:
1. 啟用哪些元件
2. 各元件對應哪些內容類型（如：設計者備註 → `:::note`）
3. 其他格式化偏好或自訂指引

#### 4.3 Save Formatting Decisions

Record confirmed standards in `style-decisions.json` under `document_format`:

```json
{
  "document_format": {
    "description": "Formatting standards for translated docs",
    "starlight_asides": {
      "enabled": true,
      "mapping": {
        "note": "Supplementary notes and designer commentary",
        "tip": "Gameplay tips and strategy guidance",
        "caution": "Common mistakes and cautions",
        "danger": "Severe consequences and irreversible actions"
      }
    },
    "card_grid": {
      "enabled": false,
      "reason": "This book does not need card-based layout"
    },
    "tabs": {
      "enabled": false,
      "reason": "No alternate-rule or switchable content present"
    },
    "tables": {
      "use_for": ["character attributes", "equipment lists"],
      "notes": ""
    },
    "dice_tables": {
      "enabled": true,
      "format": "Use notation like 1d6 with explicit roll ranges"
    },
    "additional_guidelines": []
  }
}
```

Values above are examples; actual values depend on user choices.

### 5. Extract and Select Images

#### 5.1 Extract Images from PDF

Images are automatically extracted during step 2 (`extract_pdf.py`).

Images saved to `data/markdown/images/<pdf_name>/`.

#### 5.2 Present Images to User

List all extracted images with thumbnails or descriptions:

```
找到以下圖片：
1. image_001.jpg（封面，1200x800）
2. image_002.png（角色插圖，600x400）
3. image_003.jpg（地圖，1000x700）
...

請選擇用途：
```

#### 5.3 Ask Image Assignments

Use AskUserQuestion for each image type:

**Hero Image** (homepage main image, cropped into a circle):
- Recommendation: choose a key visual, character, or iconic image
- Location: `docs/src/assets/hero.jpg`

**Background Image**:
- Recommendation: choose an atmosphere image, scene image, or texture
- Location: `docs/public/bg.jpg`

**OG Image** (social sharing preview image):
- Recommendation: 1200x630 is ideal, choose an image that represents the game
- Location: `docs/public/og-image.jpg`

#### 5.4 Process Selected Images

Copy selected images to appropriate locations:

```bash
# Hero image (resize if needed)
cp data/markdown/images/<pdf_name>/<selected_hero>.jpg docs/src/assets/hero.jpg

# Background image
cp data/markdown/images/<pdf_name>/<selected_bg>.jpg docs/public/bg.jpg

# OG image (resize to 1200x630 if needed)
cp data/markdown/images/<pdf_name>/<selected_og>.jpg docs/public/og-image.jpg
```

### 6. Configure Visual Theme

#### 6.1 Background Mode

Use AskUserQuestion:

```
背景色調設定：

選項：
1. 深色模式（Dark）- 適合大多數遊戲，神祕且有沉浸感
2. 淺色模式（Light）- 清新、明亮風格

目前背景圖的主色調是什麼？
```

#### 6.2 Overlay Settings

Based on background image analysis, ask:

```
背景圖對比度設定：

觀察您選擇的背景圖，請確認：

1. 需要深色遮罩 - 背景太亮，文字可能不清楚
2. 需要淺色遮罩 - 背景太深但想要淺色主題
3. 不需要遮罩 - 背景對比度適中
4. 自訂遮罩透明度（0-1）

建議：通常 0.6-0.8 的遮罩效果最佳
```

Update `docs/src/styles/custom.css`:

```css
/* Overlay opacity */
--overlay-opacity: <user_choice>;
```

#### 6.3 Color Palette Design

Use AskUserQuestion to determine color style:

```
色票風格設定：

請選擇適合遊戲氛圍的色彩風格：

1. 🌊 冷色系（Cool）
   - 主色：藍色系
   - 適合：科幻、海洋、冬季、神祕

2. 🔥 暖色系（Warm）
   - 主色：橘紅色系
   - 適合：冒險、沙漠、戰鬥、熱情

3. 🌲 自然系（Nature）
   - 主色：綠色系
   - 適合：奇幻、森林、生態、療癒

4. 🌙 暗黑系（Dark）
   - 主色：紫黑色系
   - 適合：恐怖、哥德、死亡、邪惡

5. ⚔️ 史詩系（Epic）
   - 主色：金色系
   - 適合：中世紀、王國、戰爭、榮耀

6. 🎨 自訂（Custom）
   - 提供主色 HEX 或描述風格
```

#### 6.4 Generate Color Variables

Based on user choice, generate an HSL color scheme:

**Cool**:
```css
--color-primary-h: 217;   /* Blue */
--color-secondary-h: 180; /* Cyan */
--color-tertiary-h: 260;  /* Purple */
--color-quaternary-h: 200; /* Sky blue */
```

**Warm**:
```css
--color-primary-h: 25;    /* Orange */
--color-secondary-h: 45;  /* Gold */
--color-tertiary-h: 0;    /* Red */
--color-quaternary-h: 350; /* Rose */
```

**Nature**:
```css
--color-primary-h: 142;   /* Green */
--color-secondary-h: 80;  /* Yellow-green */
--color-tertiary-h: 30;   /* Brown */
--color-quaternary-h: 160; /* Teal */
```

**Dark**:
```css
--color-primary-h: 280;   /* Purple */
--color-secondary-h: 320; /* Magenta */
--color-tertiary-h: 0;    /* Blood red */
--color-quaternary-h: 260; /* Deep purple */
```

**Epic**:
```css
--color-primary-h: 45;    /* Gold */
--color-secondary-h: 30;  /* Bronze */
--color-tertiary-h: 0;    /* Red */
--color-quaternary-h: 15; /* Orange gold */
```

#### 6.5 Apply Theme Settings

Update `docs/src/styles/custom.css` with selected colors.

If user chose background image, uncomment background-image in CSS:

```css
body {
  background-color: var(--sl-color-black);
  background-image: url('/bg.jpg');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  background-repeat: no-repeat;
}
```

### 7. Identify Key Terms (Interactive)

Invoke `terminology-management` skill and run candidate generation from extracted docs:

- Capitalized game terms (Move, Playbook, Harm)
- Quoted terms
- Repeated specialized vocabulary (frequency >= 2)
- Proper nouns appearing >= 2 times (must be treated as managed terms when `proper_nouns.mode != keep_original`)

Use script flow:

```bash
uv run python scripts/term_generate.py --min-frequency 2
```

Present terms to user for translation confirmation.

### 8. Configure Proper Noun Translation Policy (Required)

Before building the glossary, ask user to choose proper noun handling policy:

1. Keep original names by default
2. Translate names when official/accepted Chinese forms exist
3. Prefer translated names, with original in parentheses on first mention

Record the decision in `style-decisions.json`:

```json
{
  "proper_nouns": {
    "mode": "keep_original | official_only | translate_with_original_first",
    "reason": "user preference"
  }
}
```

### 9. Build Glossary (Single Source of Truth)

Create `glossary.json` with confirmed terms:

```json
{
  "Term": {
    "zh": "translation",
    "notes": "usage context"
  }
}
```

Then run terminology read/check:

```bash
uv run python scripts/term_edit.py --term "<TERM>" --cal
uv run python scripts/term_edit.py --term "<TERM>" --set-zh "<ZH>" --status approved --mark-term
uv run python scripts/term_read.py
```

Rules:
- `glossary.json` is the only source of truth.
- For unmanaged terms, `term_edit.py` must run with `--cal` before editing.
- Terms marked as managed skip full-site search in later `--cal` runs.
- If `proper_nouns.mode != keep_original`, proper nouns with frequency >= 2 must be added as managed glossary terms.

Ask user about style preferences and record in `style-decisions.json`.

### 10. Split Content

```bash
uv run python scripts/split_chapters.py
```

### 11. Generate Homepage index.md from style-decisions.json

Before chapter splitting, create/update `docs/src/content/docs/index.md` using project metadata and style decisions.

1. Read repository settings from `style-decisions.json`:
   - `repository.visibility`
   - `repository.url`
   - `repository.show_on_homepage`
2. Write homepage frontmatter and intro content in Traditional Chinese.
3. Repo link rendering rule:
   - If `visibility=public` and `show_on_homepage=true`, include a visible `GitHub Repo` link in `index.md`.
   - If `visibility=private`, do not render repo link.
4. Keep this logic data-driven: homepage content must follow `style-decisions.json` as source of truth.

### 12. Analyze and Split index.md

After initial split, analyze the generated `index.md` to create proper chapter structure:

1. **Identify TOC Structure**
   - Find table of contents or major headings in index.md
   - Extract chapter/section titles and their order
   - Note heading hierarchy (H1, H2, H3)

2. **Propose Chapter Split**
   Present to user:
   ```
   找到以下章節結構：
   1. [章節名稱] - 約 XXX 字
   2. [章節名稱] - 約 XXX 字
   ...
   建議拆分為獨立檔案嗎？
   ```

3. **Execute Split**
   For each identified chapter:
   - Create new file with slug derived from title
   - Add frontmatter with `sidebar.order` to preserve TOC sequence
   - Move corresponding content from index.md
   - Update index.md to contain only overview/introduction

4. **Frontmatter Template**
   ```yaml
   ---
   title: Chapter Title
   description: Chapter Description
   sidebar:
     order: N  # Keep original table of contents order
   ---
   ```

### 13. Configure Chapters

Finalize `chapters.json` after all splits are done:
1. Show table of contents from PDF and actual generated files
2. Confirm chapter structure based on final split result
3. Map page ranges and file paths to output files
4. Ensure order matches `sidebar.order` and actual navigation

### 14. Create Translation Progress Tracker

After `chapters.json` is finalized, create `data/translation-progress.json` to track per-chapter translation status.

Schema:

```json
{
  "_meta": {
    "description": "Translation progress tracker",
    "updated": "YYYY-MM-DD",
    "total_chapters": 0,
    "completed": 0
  },
  "chapters": [
    {
      "id": "chapter-slug",
      "title": "Chapter Title (English source)",
      "file": "docs/src/content/docs/chapter-slug.md",
      "source_pages": "1-20",
      "status": "not_started",
      "notes": ""
    }
  ]
}
```

Status values: `not_started` | `in_progress` | `completed` | `reviewed`

Rules:
- Derive `id` from the output filename (without `.md`).
- Populate `source_pages` from `chapters.json` page range mapping.
- Set all chapters to `not_started` on initialization.
- This file is the single source of truth for translation status; update it manually after each chapter is translated.

### 15. Verify

- Check generated files in `docs/src/content/docs/`
- Verify sidebar order matches original TOC
- Preview: `cd docs && bun dev`

### 16. Record Configuration

Save all visual settings to `style-decisions.json`:

```json
{
  "theme": {
    "mode": "dark",
    "palette": "cool",
    "overlay_opacity": 0.7
  },
  "images": {
    "hero": "image_001.jpg",
    "background": "image_003.jpg",
    "og": "image_001.jpg"
  },
  "colors": {
    "primary_h": 217,
    "secondary_h": 180,
    "tertiary_h": 260,
    "quaternary_h": 200
  },
  "proper_nouns": {
    "mode": "official_only",
    "reason": "User prefers official or widely accepted Chinese names"
  },
  "repository": {
    "visibility": "public",
    "url": "https://github.com/<username>/<project_name>",
    "show_on_homepage": true
  }
}
```

### 17. Final Cleanup and Sidebar Refresh

After cropping and split operations are complete:

1. Remove unnecessary example files and placeholders from `docs/src/content/docs/`.
2. Ensure only real, current documents remain in the content tree.
3. Reorganize sidebar configuration/order so it reflects the latest split structure.
4. Verify sidebar links do not point to deleted or renamed files.
5. Run a final docs preview and confirm navigation is correct.

## Completion Checklist (Must Follow in Order)

- [ ] Step 1: PDF source located in `data/pdfs/` and confirmed
- [ ] Step 2: Content extracted via `extract_pdf.py`; outputs in `data/markdown/` verified
- [ ] Step 3: Cropped PDF quality reviewed; required splits done; re-extraction confirmed complete
- [ ] Step 4: Book structure overview completed; formatting standards confirmed with user and saved to `style-decisions.json.document_format`
- [ ] Step 5: Images selected and copied to assets (hero/background/og)
- [ ] Step 6: Visual theme configured (background mode, overlay, palette)
- [ ] Step 7: Terminology candidates reviewed and confirmed with user in Traditional Chinese
- [ ] Step 8: Proper noun translation policy confirmed with user and saved to `style-decisions.json`
- [ ] Step 9: `glossary.json` and style decisions updated
- [ ] Step 10: Initial chapter split completed via `split_chapters.py`
- [ ] Step 11: Homepage `index.md` generated from `style-decisions.json` (including repo link display rules)
- [ ] Step 12: `index.md` analyzed and chapter split files generated
- [ ] Step 13: Final `chapters.json` configuration completed; order matches sidebar
- [ ] Step 14: `data/translation-progress.json` created with all chapters set to `not_started`
- [ ] Step 15: Docs preview verification completed (navigation, links, rendering)
- [ ] Step 16: Configuration records updated in `style-decisions.json`
- [ ] Step 17: Unnecessary sample files removed and sidebar refreshed
- [ ] Gate: Confirmed all user interactions were in Traditional Chinese

## Example Usage

```
/init-doc
/init-doc data/pdfs/rulebook.pdf
```
