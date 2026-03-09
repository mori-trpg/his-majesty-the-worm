#!/usr/bin/env python3
"""
PDF 提取工具
將 PDF 轉換為 Markdown，支援文字與圖片提取

使用方式：
    python scripts/extract_pdf.py <pdf_file>
    python scripts/extract_pdf.py <pdf_file> --include-images
    python scripts/extract_pdf.py <pdf_file> --no-include-images
    python scripts/extract_pdf.py <pdf_file> --skip-full-markitdown
    python scripts/extract_pdf.py <pdf_file> --layout-profile double-column
    python scripts/extract_pdf.py <pdf_file> --page-text-engine markitdown

輸出：
    data/markdown/<檔名>.md                 - markitdown 提取版本
    data/markdown/<檔名>_pages.md           - 含頁碼標記版本（用於章節拆分）
    data/markdown/images/<檔名>/            - 提取的圖片
    data/markdown/images/<檔名>/manifest.json - 圖片位置與尺寸資訊
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

try:
    from markitdown import MarkItDown
except ImportError:
    MarkItDown = None

try:
    import pymupdf
except ImportError:
    pymupdf = None


VALID_PAGE_TEXT_ENGINES = {"auto", "pymupdf", "markitdown"}
VALID_LAYOUT_PROFILES = {"auto", "single-column", "double-column"}
PAGE_TEXT_ENGINE_ALIASES = {
    "fitz": "pymupdf",
    "markdown": "markitdown",
}
LAYOUT_PROFILE_ALIASES = {
    "single": "single-column",
    "single_column": "single-column",
    "double": "double-column",
    "double_column": "double-column",
    "two-column": "double-column",
    "two_column": "double-column",
}
LONG_SPACE_RUN_RE = re.compile(r" {4,}")
NOISY_LINE_SPACE_RE = re.compile(r" {8,}")
MIN_QUALITY_PROBE_CHARS = 400
PYMUPDF_LAYOUT_NOISE_RATIO = 0.08
PYMUPDF_LAYOUT_NOISE_LINES = 4


def compute_visual_hash(samples: list[int]) -> str | None:
    """根據灰階採樣建立簡單視覺指紋。"""
    if not samples:
        return None
    average = sum(samples) / len(samples)
    bits = "".join("1" if sample >= average else "0" for sample in samples)
    return f"{int(bits, 2):016x}"


def analyze_image_bytes(image_bytes: bytes) -> dict[str, object]:
    """分析圖片內容，提供背景判定可用的視覺特徵。"""
    if pymupdf is None or not hasattr(pymupdf, "Pixmap"):
        return {}

    try:
        pixmap = pymupdf.Pixmap(image_bytes)
    except Exception:
        return {}

    width = int(getattr(pixmap, "width", 0) or 0)
    height = int(getattr(pixmap, "height", 0) or 0)
    stride = int(getattr(pixmap, "stride", 0) or 0)
    channel_count = int(getattr(pixmap, "n", 0) or 0)
    samples = getattr(pixmap, "samples", b"")

    if width <= 0 or height <= 0 or stride <= 0 or channel_count <= 0 or not samples:
        return {}

    color_counts: Counter[tuple[int, int, int]] = Counter()
    grayscale_samples: list[int] = []
    max_sample_axis = 48
    grid_axis = 8
    step_x = max(1, width // max_sample_axis)
    step_y = max(1, height // max_sample_axis)

    def sample_rgb(x: int, y: int) -> tuple[int, int, int]:
        offset = y * stride + x * channel_count
        pixel = samples[offset: offset + channel_count]
        if not pixel:
            return (0, 0, 0)
        if channel_count == 1:
            value = pixel[0]
            return (value, value, value)
        if channel_count >= 3:
            return (pixel[0], pixel[1], pixel[2])
        value = pixel[0]
        return (value, value, value)

    for y in range(0, height, step_y):
        for x in range(0, width, step_x):
            r, g, b = sample_rgb(x, y)
            color_counts[(r // 16, g // 16, b // 16)] += 1

    for grid_y in range(grid_axis):
        sample_y = min(height - 1, int((grid_y + 0.5) * height / grid_axis))
        for grid_x in range(grid_axis):
            sample_x = min(width - 1, int((grid_x + 0.5) * width / grid_axis))
            r, g, b = sample_rgb(sample_x, sample_y)
            grayscale = int(0.299 * r + 0.587 * g + 0.114 * b)
            grayscale_samples.append(grayscale)

    total_samples = sum(color_counts.values())
    dominant_color_ratio = None
    if total_samples:
        dominant_color_ratio = round(max(color_counts.values()) / total_samples, 4)

    return {
        "visual_hash": compute_visual_hash(grayscale_samples),
        "dominant_color_ratio": dominant_color_ratio,
        "sampled_pixel_count": total_samples,
    }


def normalize_page_text_engine(value: object) -> str | None:
    """正規化頁面文字引擎設定。"""
    if value is None:
        return None
    normalized = str(value).strip().lower()
    normalized = PAGE_TEXT_ENGINE_ALIASES.get(normalized, normalized)
    if normalized in VALID_PAGE_TEXT_ENGINES:
        return normalized
    return None


def normalize_layout_profile(value: object) -> str | None:
    """正規化版面設定。"""
    if value is None:
        return None
    normalized = str(value).strip().lower()
    normalized = LAYOUT_PROFILE_ALIASES.get(normalized, normalized)
    if normalized in VALID_LAYOUT_PROFILES:
        return normalized
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="將 PDF 提取成可切分的 Markdown")
    parser.add_argument("pdf_file", help="來源 PDF 檔案")
    parser.add_argument(
        "--skip-full-markitdown",
        action="store_true",
        help="略過整本 markitdown 提取，只保留 _pages.md 與圖片輸出",
    )
    parser.add_argument(
        "--page-text-engine",
        choices=("auto", "pymupdf", "markitdown"),
        default="auto",
        help="生成 _pages.md 時使用的頁面文字引擎（預設: auto，會依雙欄偵測與文件設定選擇）",
    )
    parser.add_argument(
        "--layout-profile",
        choices=("auto", "single-column", "double-column"),
        default="auto",
        help="文件版面設定（預設: auto；double-column 會偏向 markitdown，single-column 會偏向 pymupdf）",
    )

    include_group = parser.add_mutually_exclusive_group()
    include_group.add_argument(
        "--include-images",
        dest="include_images",
        action="store_true",
        help="包含圖片提取與 manifest",
    )
    include_group.add_argument(
        "--no-include-images",
        dest="include_images",
        action="store_false",
        help="略過圖片提取",
    )
    parser.set_defaults(include_images=None)
    return parser.parse_args()


def prompt_include_images() -> bool:
    """互動詢問是否要提取圖片。非互動執行時預設為否。"""
    if not sys.stdin.isatty():
        return False

    while True:
        answer = input("是否要包含圖片提取與位置記錄？[y/N]: ").strip().lower()
        if answer in {"", "n", "no"}:
            return False
        if answer in {"y", "yes"}:
            return True
        print("請輸入 y 或 n。")


def extract_with_markitdown(pdf_path: Path, output_dir: Path) -> Path | None:
    """使用 markitdown 提取 PDF 內容（較好的格式保留）"""
    if MarkItDown is None:
        print("⚠️  markitdown 未安裝，跳過")
        return None

    md = MarkItDown()
    result = md.convert(str(pdf_path))

    output_file = output_dir / f"{pdf_path.stem}.md"
    output_file.write_text(result.text_content, encoding="utf-8")

    print(f"✓ 已提取: {output_file}")
    return output_file


def extract_page_text_pymupdf(page) -> str:
    """使用 pymupdf 直接提取單頁文字。"""
    try:
        text = page.get_text("text", sort=True)
    except TypeError:
        try:
            text = page.get_text("text")
        except TypeError:
            text = page.get_text()
    return text.strip()


def analyze_pymupdf_text_noise(text: str) -> dict[str, object]:
    """估算 pymupdf 文字是否混入大量版面空白或側欄干擾。"""
    normalized = text.replace("\x00", "")
    char_count = len(normalized)
    long_space_runs = [len(match.group(0)) for match in LONG_SPACE_RUN_RE.finditer(normalized)]
    long_space_chars = sum(long_space_runs)
    noisy_lines = sum(1 for line in normalized.splitlines() if NOISY_LINE_SPACE_RE.search(line))
    whitespace_ratio = round(long_space_chars / char_count, 4) if char_count else 0.0
    is_noisy = (
        char_count >= MIN_QUALITY_PROBE_CHARS
        and (
            whitespace_ratio >= PYMUPDF_LAYOUT_NOISE_RATIO
            or noisy_lines >= PYMUPDF_LAYOUT_NOISE_LINES
        )
    )
    return {
        "char_count": char_count,
        "long_space_runs": len(long_space_runs),
        "max_long_space_run": max(long_space_runs) if long_space_runs else 0,
        "noisy_lines": noisy_lines,
        "whitespace_ratio": whitespace_ratio,
        "is_noisy": is_noisy,
    }


def load_style_decisions(project_root: Path) -> dict:
    """讀取 style-decisions.json。"""
    path = project_root / "style-decisions.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"⚠️  style-decisions.json 解析失敗，忽略文件抽取設定：{exc}")
        return {}


def load_document_extraction_settings(project_root: Path, pdf_stem: str) -> dict[str, str]:
    """讀取全域與每文件抽取設定。"""
    style_decisions = load_style_decisions(project_root)
    document_format = style_decisions.get("document_format", {})
    if not isinstance(document_format, dict):
        return {}

    settings: dict[str, str] = {}
    for key, normalizer in (
        ("page_text_engine", normalize_page_text_engine),
        ("layout_profile", normalize_layout_profile),
    ):
        normalized = normalizer(document_format.get(key))
        if normalized is not None:
            settings[key] = normalized

    documents = document_format.get("documents", {})
    if isinstance(documents, dict):
        doc_settings = documents.get(pdf_stem, {})
        if isinstance(doc_settings, dict):
            for key, normalizer in (
                ("page_text_engine", normalize_page_text_engine),
                ("layout_profile", normalize_layout_profile),
            ):
                normalized = normalizer(doc_settings.get(key))
                if normalized is not None:
                    settings[key] = normalized

    return settings


def classify_page_layout(words: list[tuple], page_width: float) -> dict[str, object]:
    """根據單頁文字分布判斷是否為雙欄頁。"""
    if page_width <= 0:
        return {"layout_profile": "unknown", "confidence": 0.0, "classified_lines": 0}

    lines: dict[tuple[int, int], list[tuple[float, float, str]]] = {}
    for word in words:
        if len(word) < 8:
            continue
        x0, _y0, x1, _y1, text, block_no, line_no, _word_no = word[:8]
        text = str(text).strip()
        if len(re.sub(r"\W+", "", text)) < 2:
            continue
        key = (int(block_no), int(line_no))
        lines.setdefault(key, []).append((float(x0), float(x1), text))

    line_boxes: list[tuple[float, float]] = []
    for line_words in lines.values():
        line_words.sort(key=lambda item: item[0])
        joined = " ".join(text for _x0, _x1, text in line_words).strip()
        if len(joined) < 24:
            continue
        line_boxes.append(
            (
                min(x0 for x0, _x1, _text in line_words),
                max(x1 for _x0, x1, _text in line_words),
            )
        )

    if len(line_boxes) < 8:
        return {"layout_profile": "unknown", "confidence": 0.0, "classified_lines": len(line_boxes)}

    left_boundary = page_width * 0.48
    right_boundary = page_width * 0.52
    left_lines = sum(1 for x0, x1 in line_boxes if x1 <= left_boundary)
    right_lines = sum(1 for x0, x1 in line_boxes if x0 >= right_boundary)
    spanning_lines = sum(1 for x0, x1 in line_boxes if x0 < left_boundary and x1 > right_boundary)
    classified_lines = left_lines + right_lines + spanning_lines
    if classified_lines < 8:
        return {
            "layout_profile": "unknown",
            "confidence": 0.0,
            "classified_lines": classified_lines,
        }

    left_ratio = left_lines / classified_lines
    right_ratio = right_lines / classified_lines
    spanning_ratio = spanning_lines / classified_lines

    if (
        left_lines >= 3
        and right_lines >= 3
        and left_ratio >= 0.2
        and right_ratio >= 0.2
        and spanning_ratio <= 0.2
    ):
        confidence = round(min(0.99, (left_ratio + right_ratio) * (1 - spanning_ratio)), 2)
        return {
            "layout_profile": "double-column",
            "confidence": confidence,
            "classified_lines": classified_lines,
        }

    if spanning_ratio >= 0.45:
        return {
            "layout_profile": "single-column",
            "confidence": round(min(0.99, spanning_ratio), 2),
            "classified_lines": classified_lines,
        }

    return {
        "layout_profile": "unknown",
        "confidence": round(max(left_ratio, right_ratio, spanning_ratio), 2),
        "classified_lines": classified_lines,
    }


def sample_page_indices(total_pages: int, max_samples: int = 12) -> list[int]:
    """均勻抽樣頁碼索引。"""
    if total_pages <= 0:
        return []
    if total_pages <= max_samples:
        return list(range(total_pages))
    return sorted({round(i * (total_pages - 1) / (max_samples - 1)) for i in range(max_samples)})


def probe_pymupdf_text_quality(pdf_path: Path, max_samples: int = 12) -> dict[str, object]:
    """抽樣檢查 pymupdf 的文字流是否受版面噪訊污染。"""
    if pymupdf is None:
        return {
            "prefer_markitdown": False,
            "source": "pymupdf-quality-probe",
            "sampled_pages": [],
            "informative_pages": 0,
            "noisy_pages": 0,
            "required_noisy_pages": 0,
        }

    doc = pymupdf.open(str(pdf_path))
    try:
        results: list[dict[str, object]] = []
        for page_index in sample_page_indices(len(doc), max_samples=max_samples):
            page = doc[page_index]
            text = extract_page_text_pymupdf(page)
            result = analyze_pymupdf_text_noise(text)
            result["page"] = page_index + 1
            results.append(result)

        informative = [result for result in results if result["char_count"] >= MIN_QUALITY_PROBE_CHARS]
        noisy = [result for result in informative if result["is_noisy"]]
        required_noisy_pages = max(2, (len(informative) + 2) // 3) if informative else 0
        prefer_markitdown = bool(informative) and len(noisy) >= required_noisy_pages

        return {
            "prefer_markitdown": prefer_markitdown,
            "source": "pymupdf-quality-probe",
            "sampled_pages": results,
            "informative_pages": len(informative),
            "noisy_pages": len(noisy),
            "required_noisy_pages": required_noisy_pages,
        }
    finally:
        doc.close()


def detect_layout_profile(pdf_path: Path, max_samples: int = 12) -> dict[str, object]:
    """抽樣頁面，自動判斷單欄或雙欄。"""
    if pymupdf is None:
        return {
            "layout_profile": "single-column",
            "confidence": 0.0,
            "source": "fallback",
            "sampled_pages": [],
        }

    doc = pymupdf.open(str(pdf_path))
    try:
        results: list[dict[str, object]] = []
        for page_index in sample_page_indices(len(doc), max_samples=max_samples):
            page = doc[page_index]
            try:
                words = page.get_text("words", sort=False)
            except TypeError:
                words = page.get_text("words")
            result = classify_page_layout(words or [], float(page.rect.width))
            result["page"] = page_index + 1
            results.append(result)

        known = [result for result in results if result["layout_profile"] != "unknown"]
        if not known:
            return {
                "layout_profile": "single-column",
                "confidence": 0.0,
                "source": "auto-detect",
                "sampled_pages": results,
            }

        double_votes = sum(1 for result in known if result["layout_profile"] == "double-column")
        single_votes = sum(1 for result in known if result["layout_profile"] == "single-column")
        if double_votes > single_votes:
            layout_profile = "double-column"
            confidence = round(double_votes / len(known), 2)
        else:
            layout_profile = "single-column"
            confidence = round(single_votes / len(known), 2)

        return {
            "layout_profile": layout_profile,
            "confidence": confidence,
            "source": "auto-detect",
            "sampled_pages": results,
        }
    finally:
        doc.close()


def resolve_page_text_strategy(
    pdf_path: Path,
    project_root: Path,
    requested_engine: str,
    requested_layout: str,
) -> dict[str, object]:
    """綜合 CLI、style-decisions 與自動偵測，決定分頁提取策略。"""
    pdf_stem = pdf_path.stem
    settings = load_document_extraction_settings(project_root, pdf_stem)

    page_text_engine = normalize_page_text_engine(requested_engine) or "auto"
    layout_profile = normalize_layout_profile(requested_layout) or "auto"
    engine_source = "cli" if page_text_engine != "auto" else None
    layout_source = "cli" if layout_profile != "auto" else None

    if page_text_engine == "auto":
        style_engine = settings.get("page_text_engine")
        if style_engine and style_engine != "auto":
            page_text_engine = style_engine
            engine_source = "style-decisions"

    if layout_profile == "auto":
        style_layout = settings.get("layout_profile")
        if style_layout and style_layout != "auto":
            layout_profile = style_layout
            layout_source = "style-decisions"

    detection: dict[str, object] | None = None
    quality_probe: dict[str, object] | None = None
    if layout_profile == "auto":
        detection = detect_layout_profile(pdf_path)
        layout_profile = str(detection.get("layout_profile", "single-column"))
        layout_source = str(detection.get("source", "auto-detect"))

    if (
        page_text_engine == "auto"
        and layout_profile == "single-column"
        and MarkItDown is not None
    ):
        quality_probe = probe_pymupdf_text_quality(pdf_path)
        if quality_probe.get("prefer_markitdown"):
            page_text_engine = "markitdown"
            engine_source = str(quality_probe.get("source", "quality-probe"))

    if page_text_engine == "auto":
        page_text_engine = "markitdown" if layout_profile == "double-column" else "pymupdf"
        engine_source = "layout-profile"

    if page_text_engine == "markitdown" and MarkItDown is None:
        print("⚠️  需要 markitdown 才能使用雙欄保守路徑，已回退到 pymupdf")
        page_text_engine = "pymupdf"
        engine_source = "fallback"

    return {
        "page_text_engine": page_text_engine,
        "page_text_engine_source": engine_source or "default",
        "layout_profile": layout_profile,
        "layout_profile_source": layout_source or "default",
        "document_settings": settings,
        "detection": detection,
        "quality_probe": quality_probe,
    }


def should_print_progress(page_num: int, total_pages: int, progress_every: int) -> bool:
    """控制分頁提取進度輸出頻率。"""
    return page_num == 1 or page_num == total_pages or page_num % progress_every == 0


def extract_with_pages(
    pdf_path: Path,
    output_dir: Path,
    page_text_engine: str = "pymupdf",
    progress_every: int = 25,
) -> Path | None:
    """提取含頁碼標記的內容，用於章節拆分。"""
    if pymupdf is None:
        print("⚠️  pymupdf 未安裝（需要用於分頁），跳過")
        return None
    if page_text_engine == "markitdown" and MarkItDown is None:
        print("⚠️  markitdown 未安裝，無法使用 markitdown 分頁模式")
        return None

    import tempfile

    doc = pymupdf.open(str(pdf_path))
    total_pages = len(doc)
    progress_every = max(1, progress_every)
    output_file = output_dir / f"{pdf_path.stem}_pages.md"
    try:
        with output_file.open("w", encoding="utf-8") as handle:
            if page_text_engine == "pymupdf":
                for page_num, page in enumerate(doc, 1):
                    page_text = extract_page_text_pymupdf(page)
                    handle.write(f"\n\n<!-- PAGE {page_num} -->\n\n{page_text}")
                    if should_print_progress(page_num, total_pages, progress_every):
                        print(f"↻ 分頁提取進度（pymupdf）: {page_num}/{total_pages}")
            else:
                md = MarkItDown()
                with tempfile.TemporaryDirectory() as tmp_dir:
                    for page_num in range(total_pages):
                        single = pymupdf.open()
                        single.insert_pdf(doc, from_page=page_num, to_page=page_num)
                        tmp_pdf = Path(tmp_dir) / f"page_{page_num + 1}.pdf"
                        single.save(str(tmp_pdf))
                        single.close()

                        result = md.convert(str(tmp_pdf))
                        handle.write(
                            f"\n\n<!-- PAGE {page_num + 1} -->\n\n{result.text_content.strip()}"
                        )
                        if should_print_progress(page_num + 1, total_pages, progress_every):
                            print(f"↻ 分頁提取進度（markitdown）: {page_num + 1}/{total_pages}")
    finally:
        doc.close()

    print(f"✓ 已提取（含頁碼，{page_text_engine}）: {output_file}")
    return output_file


def build_image_filename(page_num: int, image_index: int, placement_index: int, rect, ext: str) -> str:
    """建立包含位置與尺寸資訊的圖片檔名。"""
    if rect is None:
        return f"page{page_num:03d}_img{image_index:02d}_occ{placement_index:02d}.{ext}"

    x = round(rect.x0)
    y = round(rect.y0)
    width = round(rect.width)
    height = round(rect.height)
    return (
        f"page{page_num:03d}_img{image_index:02d}_occ{placement_index:02d}"
        f"_x{x}_y{y}_w{width}_h{height}.{ext}"
    )


def extract_images(pdf_path: Path, output_dir: Path) -> list[dict]:
    """提取 PDF 中的圖片，並記錄位置與尺寸資訊。"""
    if pymupdf is None:
        print("⚠️  pymupdf 未安裝，無法提取圖片")
        return []

    doc = pymupdf.open(str(pdf_path))
    images_dir = output_dir / "images" / pdf_path.stem
    images_dir.mkdir(parents=True, exist_ok=True)

    saved_images: list[dict] = []
    for page_num, page in enumerate(doc, 1):
        page_rect = getattr(page, "rect", None)
        page_width = round(float(page_rect.width), 2) if page_rect is not None else None
        page_height = round(float(page_rect.height), 2) if page_rect is not None else None

        try:
            page_images = page.get_images(full=True)
        except TypeError:
            page_images = page.get_images()

        for img_index, img in enumerate(page_images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            analysis = analyze_image_bytes(image_bytes)
            try:
                rects = page.get_image_rects(xref, transform=False)
            except TypeError:
                rects = page.get_image_rects(xref)
            except AttributeError:
                rects = []

            if not rects:
                rects = [None]

            for placement_index, rect in enumerate(rects):
                image_name = build_image_filename(
                    page_num,
                    img_index,
                    placement_index,
                    rect,
                    image_ext,
                )
                image_path = images_dir / image_name
                image_path.write_bytes(image_bytes)

                if rect is None:
                    x = None
                    y = None
                    width = base_image.get("width")
                    height = base_image.get("height")
                else:
                    x = round(rect.x0, 2)
                    y = round(rect.y0, 2)
                    width = round(rect.width, 2)
                    height = round(rect.height, 2)

                coverage_ratio = None
                if (
                    width
                    and height
                    and page_width
                    and page_height
                    and page_width > 0
                    and page_height > 0
                ):
                    coverage_ratio = round((width * height) / (page_width * page_height), 4)

                saved_images.append(
                    {
                        "page": page_num,
                        "image_index": img_index,
                        "placement_index": placement_index,
                        "xref": xref,
                        "filename": image_name,
                        "path": str(image_path.relative_to(output_dir).as_posix()),
                        "x": x,
                        "y": y,
                        "width": width,
                        "height": height,
                        "page_width": page_width,
                        "page_height": page_height,
                        "coverage_ratio": coverage_ratio,
                        "file_size": len(image_bytes),
                        "visual_hash": analysis.get("visual_hash"),
                        "dominant_color_ratio": analysis.get("dominant_color_ratio"),
                        "sampled_pixel_count": analysis.get("sampled_pixel_count"),
                    }
                )

    doc.close()

    manifest_path = images_dir / "manifest.json"
    manifest = {
        "pdf": pdf_path.name,
        "images_dir": str(images_dir.relative_to(output_dir).as_posix()),
        "images": saved_images,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"✓ 已提取 {len(saved_images)} 張圖片到 {images_dir}")
    print(f"✓ 已建立圖片 manifest: {manifest_path}")
    return saved_images


def main():
    args = parse_args()
    pdf_path = Path(args.pdf_file)

    if not pdf_path.exists():
        print(f"❌ 找不到檔案: {pdf_path}")
        sys.exit(1)

    # 設定輸出目錄
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "data" / "markdown"
    output_dir.mkdir(parents=True, exist_ok=True)
    strategy = resolve_page_text_strategy(
        pdf_path,
        project_root,
        requested_engine=args.page_text_engine,
        requested_layout=args.layout_profile,
    )

    print(f"\n📄 處理: {pdf_path.name}")
    print(
        f"🧭 分頁引擎: {strategy['page_text_engine']} "
        f"（來源: {strategy['page_text_engine_source']}）"
    )
    print(
        f"🧭 版面設定: {strategy['layout_profile']} "
        f"（來源: {strategy['layout_profile_source']}）"
    )
    if strategy["detection"] is not None:
        sampled_pages = [
            f"p.{result['page']}={result['layout_profile']}"
            for result in strategy["detection"].get("sampled_pages", [])
            if result.get("layout_profile") != "unknown"
        ]
        if sampled_pages:
            print(f"   自動偵測抽樣: {', '.join(sampled_pages[:8])}")
    quality_probe = strategy.get("quality_probe")
    if quality_probe and quality_probe.get("prefer_markitdown"):
        noisy_pages = [
            f"p.{result['page']}={result['whitespace_ratio']}"
            for result in quality_probe.get("sampled_pages", [])
            if result.get("is_noisy")
        ]
        if noisy_pages:
            print(f"   文字品質探測：PyMuPDF 版面噪訊偏高，改用 markitdown（{', '.join(noisy_pages[:8])}）")
    print("-" * 50)

    if args.skip_full_markitdown:
        print("↷ 已略過整本 markitdown 提取")
    else:
        extract_with_markitdown(pdf_path, output_dir)

    extract_with_pages(
        pdf_path,
        output_dir,
        page_text_engine=strategy["page_text_engine"],
    )

    include_images = args.include_images
    if include_images is None:
        include_images = prompt_include_images()

    if include_images:
        extract_images(pdf_path, output_dir)
    else:
        print("↷ 已略過圖片提取")

    print("-" * 50)
    print("✅ 完成！")
    print(f"\n下一步：使用 split_chapters.py 拆分章節")


if __name__ == "__main__":
    main()
