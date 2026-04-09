# Scripts 重構計畫

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 將 `extract_pdf.py`（1102 行）和 `split_chapters.py`（561 行）拆分成職責清晰的模組，並補上測試覆蓋。

**Architecture:** 從兩個大腳本中抽取共用邏輯為 4 個內部模組（`_image_analysis.py`、`_epub_lib.py`、`_layout_lib.py`、`_markdown_utils.py`），讓原腳本瘦身為薄型編排器。每個模組先寫測試再搬移程式碼，用 import 替代內聯。

**Tech Stack:** Python 3.11+, pytest, uv

---

## 現狀分析

| 檔案 | 行數 | 職責 |
|------|------|------|
| `extract_pdf.py` | 1102 | PDF/EPUB 提取、圖片分析、版面偵測、策略決策 |
| `split_chapters.py` | 561 | 頁面解析、背景圖偵測、圖片管理、章節組裝 |
| `_term_lib.py` | 425 | 術語庫（已抽取，不動） |
| `_style_decisions_lib.py` | 147 | 樣式設定庫（已抽取，不動） |

## 目標模組結構

```
scripts/
├── _image_analysis.py    # 視覺指紋、圖片分析、背景偵測 (~120 行)
├── _epub_lib.py          # EPUB 解析、spine、虛擬頁碼 (~160 行)
├── _layout_lib.py        # 版面分類、品質探測 (~200 行)
├── _markdown_utils.py    # Markdown 清理、圖片語法、分段 (~60 行)
├── extract_pdf.py        # 瘦身編排器 (~350 行，降幅 ~68%)
├── split_chapters.py     # 瘦身編排器 (~300 行，降幅 ~47%)
└── tests/
    ├── conftest.py
    ├── test_image_analysis.py
    ├── test_epub_lib.py
    ├── test_layout_lib.py
    ├── test_markdown_utils.py
    ├── test_extract_pdf.py
    └── test_split_chapters.py
```

## 函式搬移對照表

### `_image_analysis.py`（從 extract_pdf.py + split_chapters.py）

| 函式 | 來源 | 行號 |
|------|------|------|
| `compute_visual_hash()` | extract_pdf.py | 77-83 |
| `analyze_image_bytes()` | extract_pdf.py | 86-147 |
| `image_file_size_key()` | split_chapters.py | 214-219 |
| `image_visual_key()` | split_chapters.py | 222-227 |
| `image_coverage_ratio()` | split_chapters.py | 230-235 |
| `image_dominant_color_ratio()` | split_chapters.py | 238-243 |
| `image_page_dimensions()` | split_chapters.py | 246-252 |
| `is_background_candidate()` | split_chapters.py | 267-321 |

### `_epub_lib.py`（從 extract_pdf.py）

| 函式 | 行號 |
|------|------|
| `normalize_epub_internal_path()` | 249-257 |
| `parse_epub_package()` | 260-302 |
| `iter_epub_spine_documents()` | 305-312 |
| `build_epub_virtual_pages()` | 363-395 |
| `extract_epub_with_pages()` | 398-425 |
| `extract_epub_images()` | 959-1024 |
| `build_epub_image_filename()` | 837-842 |
| `sanitize_filename_component()` | 357-360 |

### `_layout_lib.py`（從 extract_pdf.py）

| 函式 | 行號 |
|------|------|
| `classify_page_layout()` | 508-582 |
| `sample_page_indices()` | 585-591 |
| `extract_page_text_pymupdf()` | 428-437 |
| `analyze_pymupdf_text_noise()` | 440-462 |
| `probe_pymupdf_text_quality()` | 594-630 |
| `detect_layout_profile()` | 633-681 |
| 常數: `LONG_SPACE_RUN_RE`, `NOISY_LINE_SPACE_RE`, `MIN_QUALITY_PROBE_CHARS`, `PYMUPDF_LAYOUT_NOISE_*` | 66-70 |

### `_markdown_utils.py`（從 extract_pdf.py + split_chapters.py）

| 函式 | 來源 | 行號 |
|------|------|------|
| `strip_markdown_images()` | extract_pdf.py | 315-320 |
| `extract_markdown_image_targets()` | extract_pdf.py | 323-331 |
| `split_markdown_sections()` | extract_pdf.py | 334-354 |
| `clean_content()` | split_chapters.py | 138-144 |
| `count_page_text_tokens()` | split_chapters.py | 147-149 |
| 常數: `LINKED_MARKDOWN_IMAGE_RE`, `MARKDOWN_IMAGE_RE`, `MARKDOWN_HEADING_RE` | extract_pdf.py | 71-73 |

---

## Task 1: 建立測試基礎設施

**Files:**
- Create: `scripts/tests/__init__.py`
- Create: `scripts/tests/conftest.py`
- Create: `pyproject.toml`（補 pytest 設定，若不存在）

**Step 1: 確認 pytest 可用**

Run: `cd /Users/weihung/projects/game-doc-template && uv run pytest --version`

**Step 2: 建立測試目錄**

```python
# scripts/tests/__init__.py
# (empty)
```

```python
# scripts/tests/conftest.py
import sys
from pathlib import Path

# 讓 tests 能 import scripts/ 下的模組
sys.path.insert(0, str(Path(__file__).parent.parent))
```

**Step 3: 確認 pyproject.toml 有 pytest 設定**

在 `pyproject.toml` 的 `[tool.pytest.ini_options]` 加入：

```toml
[tool.pytest.ini_options]
testpaths = ["scripts/tests"]
```

**Step 4: 驗證空測試能跑**

Run: `uv run pytest scripts/tests/ -v`
Expected: 0 tests collected, no errors

**Step 5: Commit**

```bash
git add scripts/tests/ pyproject.toml
git commit -m "chore: add test infrastructure for scripts"
```

---

## Task 2: 抽取 `_markdown_utils.py` + 測試

最小、最獨立的模組，零外部依賴。

**Files:**
- Create: `scripts/_markdown_utils.py`
- Create: `scripts/tests/test_markdown_utils.py`
- Modify: `scripts/extract_pdf.py`
- Modify: `scripts/split_chapters.py`

**Step 1: 寫測試**

```python
# scripts/tests/test_markdown_utils.py
from _markdown_utils import (
    strip_markdown_images,
    extract_markdown_image_targets,
    split_markdown_sections,
    clean_content,
    count_page_text_tokens,
)


class TestStripMarkdownImages:
    def test_removes_simple_image(self):
        text = "Hello ![alt](img.png) world"
        result = strip_markdown_images(text)
        assert "![" not in result
        assert "Hello" in result
        assert "world" in result

    def test_removes_linked_image(self):
        text = "Before [![alt](img.png)](link) after"
        result = strip_markdown_images(text)
        assert "![" not in result

    def test_no_images_unchanged(self):
        text = "Just plain text"
        assert strip_markdown_images(text) == text


class TestExtractMarkdownImageTargets:
    def test_extracts_single_image(self):
        text = "![alt](images/photo.png)"
        targets = extract_markdown_image_targets(text)
        assert targets == ["images/photo.png"]

    def test_extracts_multiple(self):
        text = "![a](one.png) text ![b](two.jpg)"
        targets = extract_markdown_image_targets(text)
        assert targets == ["one.png", "two.jpg"]

    def test_no_images(self):
        assert extract_markdown_image_targets("no images here") == []


class TestSplitMarkdownSections:
    def test_splits_on_headings(self):
        text = "# Title\nContent\n## Section\nMore content"
        sections = split_markdown_sections(text)
        assert len(sections) == 2
        assert sections[0].startswith("# Title")
        assert sections[1].startswith("## Section")

    def test_single_section(self):
        text = "Just text without headings"
        sections = split_markdown_sections(text)
        assert len(sections) == 1


class TestCleanContent:
    def test_removes_pattern(self):
        text = "Hello (Order #123) world"
        result = clean_content(text, [r"\(Order #\d+\)"])
        assert "(Order" not in result

    def test_collapses_blank_lines(self):
        text = "A\n\n\n\n\nB"
        result = clean_content(text, [])
        assert "\n\n\n" not in result

    def test_no_patterns(self):
        text = "Keep everything"
        assert clean_content(text, []) == text


class TestCountPageTextTokens:
    def test_counts_words(self):
        assert count_page_text_tokens("one two three") == 3

    def test_empty_string(self):
        assert count_page_text_tokens("") == 0
```

**Step 2: 跑測試確認失敗**

Run: `uv run pytest scripts/tests/test_markdown_utils.py -v`
Expected: FAIL (ImportError)

**Step 3: 建立模組，從兩個腳本搬移函式**

```python
# scripts/_markdown_utils.py
"""Markdown 文字處理工具。"""

import re

LINKED_MARKDOWN_IMAGE_RE = re.compile(r"\[!\[[^\]]*]\([^)]+\)]\([^)]+\)")
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*]\([^)]+\)")
MARKDOWN_HEADING_RE = re.compile(r"^#{1,3}\s+\S")


def strip_markdown_images(text: str) -> str:
    """移除 Markdown 圖片語法。"""
    stripped = LINKED_MARKDOWN_IMAGE_RE.sub("", text)
    stripped = MARKDOWN_IMAGE_RE.sub("", stripped)
    stripped = re.sub(r"\n{3,}", "\n\n", stripped)
    return stripped.strip()


def extract_markdown_image_targets(text: str) -> list[str]:
    """擷取 Markdown 中的圖片路徑。"""
    from urllib.parse import unquote

    targets: list[str] = []
    for match in MARKDOWN_IMAGE_RE.finditer(text):
        target = match.group(0).split("](", 1)[1].rsplit(")", 1)[0].strip()
        target = target.split(maxsplit=1)[0].strip("<>")
        if target:
            targets.append(unquote(target))
    return targets


def split_markdown_sections(text: str) -> list[str]:
    """依 heading 將 Markdown 切成區塊。"""
    lines = text.splitlines()
    sections: list[str] = []
    current: list[str] = []

    for line in lines:
        if MARKDOWN_HEADING_RE.match(line) and any(part.strip() for part in current):
            section = "\n".join(current).strip()
            if section:
                sections.append(section)
            current = [line]
            continue
        current.append(line)

    if any(part.strip() for part in current):
        section = "\n".join(current).strip()
        if section:
            sections.append(section)

    return sections or [text.strip()]


def clean_content(text: str, patterns: list[str]) -> str:
    """清理內容，移除指定 pattern 並壓縮空行。"""
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def count_page_text_tokens(text: str) -> int:
    """估算文字 token 數。"""
    return len(re.findall(r"\S+", text))
```

**Step 4: 跑測試確認通過**

Run: `uv run pytest scripts/tests/test_markdown_utils.py -v`
Expected: ALL PASS

**Step 5: 更新 extract_pdf.py import**

- 刪除 `LINKED_MARKDOWN_IMAGE_RE`、`MARKDOWN_IMAGE_RE`、`MARKDOWN_HEADING_RE` 定義
- 刪除 `strip_markdown_images()`、`extract_markdown_image_targets()`、`split_markdown_sections()` 函式
- 頂部加 `from _markdown_utils import strip_markdown_images, extract_markdown_image_targets, split_markdown_sections, MARKDOWN_IMAGE_RE`

**Step 6: 更新 split_chapters.py import**

- 刪除 `clean_content()` 和 `count_page_text_tokens()` 函式
- 頂部加 `from _markdown_utils import clean_content, count_page_text_tokens`

**Step 7: 端到端驗證**

Run: `uv run python scripts/extract_pdf.py --help && uv run python scripts/split_chapters.py --init 2>&1 | head -5`
Expected: 無 ImportError

**Step 8: Commit**

```bash
git add scripts/_markdown_utils.py scripts/tests/test_markdown_utils.py scripts/extract_pdf.py scripts/split_chapters.py
git commit -m "refactor: extract _markdown_utils from extract_pdf and split_chapters"
```

---

## Task 3: 抽取 `_image_analysis.py` + 測試

跨兩個腳本共用的圖片分析邏輯。

**Files:**
- Create: `scripts/_image_analysis.py`
- Create: `scripts/tests/test_image_analysis.py`
- Modify: `scripts/extract_pdf.py`
- Modify: `scripts/split_chapters.py`

**Step 1: 寫測試**

```python
# scripts/tests/test_image_analysis.py
from _image_analysis import (
    compute_visual_hash,
    image_file_size_key,
    image_visual_key,
    image_coverage_ratio,
    image_dominant_color_ratio,
    image_page_dimensions,
    is_background_candidate,
)


class TestComputeVisualHash:
    def test_returns_hex_string(self):
        samples = [100, 200, 50, 250, 128, 64, 192, 32]
        result = compute_visual_hash(samples)
        assert result is not None
        assert all(c in "0123456789abcdef" for c in result)

    def test_empty_samples_returns_none(self):
        assert compute_visual_hash([]) is None

    def test_deterministic(self):
        samples = [10, 20, 30, 40]
        assert compute_visual_hash(samples) == compute_visual_hash(samples)


class TestImageAccessors:
    def test_file_size_key(self):
        assert image_file_size_key({"file_size": 1024}) == 1024
        assert image_file_size_key({}) is None

    def test_visual_key(self):
        assert image_visual_key({"visual_hash": "abc123"}) == "abc123"
        assert image_visual_key({}) is None

    def test_coverage_ratio(self):
        assert image_coverage_ratio({"coverage_ratio": 0.75}) == 0.75
        assert image_coverage_ratio({}) is None

    def test_dominant_color_ratio(self):
        assert image_dominant_color_ratio({"dominant_color_ratio": 0.9}) == 0.9
        assert image_dominant_color_ratio({}) is None

    def test_page_dimensions(self):
        assert image_page_dimensions({"page_width": 612, "page_height": 792}) == (612.0, 792.0)
        assert image_page_dimensions({}) == (None, None)


class TestIsBackgroundCandidate:
    def test_large_coverage_with_text(self):
        image = {"page": 1, "coverage_ratio": 0.8, "x": 0, "y": 0, "width": 600, "height": 750, "page_width": 612, "page_height": 792}
        stats = {1: {"text_tokens": 100, "char_count": 500}}
        policy = {"background_min_coverage_ratio": 0.6, "background_min_text_tokens": 80}
        assert is_background_candidate(image, stats, policy) is True

    def test_small_image_not_background(self):
        image = {"page": 1, "coverage_ratio": 0.1, "x": 100, "y": 100, "width": 50, "height": 50, "page_width": 612, "page_height": 792}
        stats = {1: {"text_tokens": 100, "char_count": 500}}
        policy = {"background_min_coverage_ratio": 0.6, "background_min_text_tokens": 80, "background_edge_margin_ratio": 0.08, "background_edge_min_area_ratio": 0.18, "background_edge_min_span_ratio": 0.7}
        assert is_background_candidate(image, stats, policy) is False

    def test_no_coverage_ratio(self):
        image = {"page": 1}
        assert is_background_candidate(image, {}, {}) is False
```

**Step 2: 跑測試確認失敗**

Run: `uv run pytest scripts/tests/test_image_analysis.py -v`
Expected: FAIL (ImportError)

**Step 3: 建立模組**

從 `extract_pdf.py` 搬 `compute_visual_hash`、`analyze_image_bytes`。
從 `split_chapters.py` 搬 `image_file_size_key`、`image_visual_key`、`image_coverage_ratio`、`image_dominant_color_ratio`、`image_page_dimensions`、`is_background_candidate`。

**Step 4: 跑測試確認通過**

Run: `uv run pytest scripts/tests/test_image_analysis.py -v`
Expected: ALL PASS

**Step 5: 更新兩個腳本的 import，刪除搬走的函式**

**Step 6: 端到端驗證**

Run: `uv run python scripts/extract_pdf.py --help && uv run python scripts/split_chapters.py --init 2>&1 | head -5`

**Step 7: Commit**

```bash
git add scripts/_image_analysis.py scripts/tests/test_image_analysis.py scripts/extract_pdf.py scripts/split_chapters.py
git commit -m "refactor: extract _image_analysis shared module"
```

---

## Task 4: 抽取 `_layout_lib.py` + 測試

版面偵測與品質探測，僅被 `extract_pdf.py` 使用。

**Files:**
- Create: `scripts/_layout_lib.py`
- Create: `scripts/tests/test_layout_lib.py`
- Modify: `scripts/extract_pdf.py`

**Step 1: 寫測試**

```python
# scripts/tests/test_layout_lib.py
from _layout_lib import (
    classify_page_layout,
    sample_page_indices,
    analyze_pymupdf_text_noise,
)


class TestClassifyPageLayout:
    def test_unknown_with_no_words(self):
        result = classify_page_layout([], 612.0)
        assert result["layout_profile"] == "unknown"

    def test_zero_page_width(self):
        result = classify_page_layout([], 0)
        assert result["layout_profile"] == "unknown"


class TestSamplePageIndices:
    def test_small_document(self):
        assert sample_page_indices(5) == [0, 1, 2, 3, 4]

    def test_empty_document(self):
        assert sample_page_indices(0) == []

    def test_large_document_samples_max(self):
        result = sample_page_indices(100, max_samples=10)
        assert len(result) == 10
        assert result[0] == 0
        assert result[-1] == 99

    def test_sorted(self):
        result = sample_page_indices(50)
        assert result == sorted(result)


class TestAnalyzePymupdfTextNoise:
    def test_clean_text(self):
        text = "This is normal text without excessive spacing."
        result = analyze_pymupdf_text_noise(text)
        assert result["is_noisy"] is False

    def test_noisy_text(self):
        # 大量間距模擬雙欄噪訊
        text = "A" * 200 + "        " * 20 + "B" * 200
        result = analyze_pymupdf_text_noise(text)
        assert result["long_space_runs"] > 0
```

**Step 2: 跑測試確認失敗**

Run: `uv run pytest scripts/tests/test_layout_lib.py -v`

**Step 3: 建立模組**

搬移：`classify_page_layout`、`sample_page_indices`、`extract_page_text_pymupdf`、`analyze_pymupdf_text_noise`、`probe_pymupdf_text_quality`、`detect_layout_profile`，以及相關常數。

**Step 4: 跑測試確認通過**

Run: `uv run pytest scripts/tests/test_layout_lib.py -v`

**Step 5: 更新 extract_pdf.py import**

**Step 6: 端到端驗證 + Commit**

```bash
git add scripts/_layout_lib.py scripts/tests/test_layout_lib.py scripts/extract_pdf.py
git commit -m "refactor: extract _layout_lib for layout detection and quality probing"
```

---

## Task 5: 抽取 `_epub_lib.py` + 測試

**Files:**
- Create: `scripts/_epub_lib.py`
- Create: `scripts/tests/test_epub_lib.py`
- Modify: `scripts/extract_pdf.py`

**Step 1: 寫測試**

```python
# scripts/tests/test_epub_lib.py
from pathlib import PurePosixPath
from _epub_lib import normalize_epub_internal_path, sanitize_filename_component


class TestNormalizeEpubInternalPath:
    def test_simple_relative(self):
        result = normalize_epub_internal_path(PurePosixPath("OEBPS"), "chapter1.xhtml")
        assert result == "OEBPS/chapter1.xhtml"

    def test_with_fragment(self):
        result = normalize_epub_internal_path(PurePosixPath("OEBPS"), "ch1.xhtml#section2")
        assert result == "OEBPS/ch1.xhtml"

    def test_empty_base(self):
        result = normalize_epub_internal_path(PurePosixPath("."), "chapter.xhtml")
        assert result == "chapter.xhtml"

    def test_url_encoded(self):
        result = normalize_epub_internal_path(PurePosixPath("OEBPS"), "my%20chapter.xhtml")
        assert "my chapter" in result


class TestSanitizeFilenameComponent:
    def test_simple_name(self):
        assert sanitize_filename_component("chapter1") == "chapter1"

    def test_special_chars(self):
        result = sanitize_filename_component("my file (1)")
        assert " " not in result
        assert "(" not in result

    def test_empty_returns_default(self):
        assert sanitize_filename_component("!!!") == "image"
```

**Step 2: 跑測試確認失敗 → 建立模組 → 跑測試確認通過**

搬移所有 EPUB 相關函式（見對照表）。

**Step 3: 更新 extract_pdf.py import + 端到端驗證**

**Step 4: Commit**

```bash
git add scripts/_epub_lib.py scripts/tests/test_epub_lib.py scripts/extract_pdf.py
git commit -m "refactor: extract _epub_lib for EPUB parsing and extraction"
```

---

## Task 6: 清理 extract_pdf.py + 整合測試

**Files:**
- Modify: `scripts/extract_pdf.py`
- Create: `scripts/tests/test_extract_pdf.py`

**Step 1: 確認 extract_pdf.py 行數降至 ~350 行以下**

Run: `wc -l scripts/extract_pdf.py`
Expected: < 400

**Step 2: 寫整合測試（策略解析）**

```python
# scripts/tests/test_extract_pdf.py
from extract_pdf import (
    normalize_page_text_engine,
    normalize_layout_profile,
    should_print_progress,
    build_image_filename,
)


class TestNormalizePageTextEngine:
    def test_valid_engines(self):
        assert normalize_page_text_engine("pymupdf") == "pymupdf"
        assert normalize_page_text_engine("markitdown") == "markitdown"
        assert normalize_page_text_engine("auto") == "auto"

    def test_aliases(self):
        assert normalize_page_text_engine("fitz") == "pymupdf"

    def test_none(self):
        assert normalize_page_text_engine(None) is None

    def test_invalid(self):
        assert normalize_page_text_engine("bogus") is None


class TestShouldPrintProgress:
    def test_first_page(self):
        assert should_print_progress(1, 100, 25) is True

    def test_last_page(self):
        assert should_print_progress(100, 100, 25) is True

    def test_interval(self):
        assert should_print_progress(50, 100, 25) is True

    def test_non_interval(self):
        assert should_print_progress(13, 100, 25) is False
```

**Step 3: 跑全部測試**

Run: `uv run pytest scripts/tests/ -v`
Expected: ALL PASS

**Step 4: Commit**

```bash
git add scripts/extract_pdf.py scripts/tests/test_extract_pdf.py
git commit -m "refactor: slim down extract_pdf.py with integration tests"
```

---

## Task 7: 清理 split_chapters.py + 整合測試

**Files:**
- Modify: `scripts/split_chapters.py`
- Create: `scripts/tests/test_split_chapters.py`

**Step 1: 確認行數降至 ~300 行以下**

Run: `wc -l scripts/split_chapters.py`

**Step 2: 寫整合測試**

```python
# scripts/tests/test_split_chapters.py
from split_chapters import (
    extract_pages,
    get_page_range,
    generate_frontmatter,
    infer_source_stem,
    build_page_text_stats,
)
from _markdown_utils import clean_content


class TestExtractPages:
    def test_extracts_pages(self):
        content = "<!-- PAGE 1 -->\n\nFirst page\n\n<!-- PAGE 2 -->\n\nSecond page"
        pages = extract_pages(content)
        assert pages[1] == "First page"
        assert pages[2] == "Second page"

    def test_empty_content(self):
        assert extract_pages("") == {}


class TestGetPageRange:
    def test_range(self):
        pages = {1: "A", 2: "B", 3: "C"}
        result = get_page_range(pages, 1, 2)
        assert "A" in result
        assert "B" in result
        assert "C" not in result


class TestGenerateFrontmatter:
    def test_with_order(self):
        result = generate_frontmatter("Test Title", "Desc", 5)
        assert "title: Test Title" in result
        assert "order: 5" in result

    def test_without_order(self):
        result = generate_frontmatter("Title")
        assert "order" not in result


class TestInferSourceStem:
    def test_pages_suffix(self):
        from pathlib import Path
        assert infer_source_stem(Path("data/rulebook_pages.md")) == "rulebook"

    def test_no_suffix(self):
        from pathlib import Path
        assert infer_source_stem(Path("data/rulebook.md")) == "rulebook"
```

**Step 3: 跑全部測試**

Run: `uv run pytest scripts/tests/ -v`
Expected: ALL PASS

**Step 4: Commit**

```bash
git add scripts/split_chapters.py scripts/tests/test_split_chapters.py
git commit -m "refactor: slim down split_chapters.py with integration tests"
```

---

## Task 8: 最終驗證

**Step 1: 跑全部測試**

Run: `uv run pytest scripts/tests/ -v --tb=short`

**Step 2: 確認行數**

Run: `wc -l scripts/*.py scripts/tests/*.py | sort -n`

**Step 3: 確認無循環 import**

Run: `uv run python -c "import scripts.extract_pdf; import scripts.split_chapters; print('OK')"`

**Step 4: 確認 CLI 正常**

Run: `uv run python scripts/extract_pdf.py --help && uv run python scripts/split_chapters.py --help`

---

## 預期成果

| 指標 | 重構前 | 重構後 |
|------|--------|--------|
| `extract_pdf.py` 行數 | 1102 | ~350 |
| `split_chapters.py` 行數 | 561 | ~300 |
| 測試檔案數 | 0 | 7 |
| 共用模組數 | 2 | 6 |
| 最大單檔行數 | 1102 | ~350 |
