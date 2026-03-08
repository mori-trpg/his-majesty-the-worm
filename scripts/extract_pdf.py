#!/usr/bin/env python3
"""
PDF 提取工具
將 PDF 轉換為 Markdown，支援文字與圖片提取

使用方式：
    python scripts/extract_pdf.py <pdf_file>
    python scripts/extract_pdf.py <pdf_file> --include-images
    python scripts/extract_pdf.py <pdf_file> --no-include-images

輸出：
    data/markdown/<檔名>.md                 - markitdown 提取版本
    data/markdown/<檔名>_pages.md           - 含頁碼標記版本（用於章節拆分）
    data/markdown/images/<檔名>/            - 提取的圖片
    data/markdown/images/<檔名>/manifest.json - 圖片位置與尺寸資訊
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from markitdown import MarkItDown
except ImportError:
    MarkItDown = None

try:
    import pymupdf
except ImportError:
    pymupdf = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="將 PDF 提取成可切分的 Markdown")
    parser.add_argument("pdf_file", help="來源 PDF 檔案")

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


def extract_with_pages(pdf_path: Path, output_dir: Path) -> Path | None:
    """使用 markitdown 逐頁提取 PDF 內容（含頁碼標記，用於章節拆分）"""
    if MarkItDown is None:
        print("⚠️  markitdown 未安裝，跳過")
        return None
    if pymupdf is None:
        print("⚠️  pymupdf 未安裝（需要用於分頁），跳過")
        return None

    import tempfile

    md = MarkItDown()
    doc = pymupdf.open(str(pdf_path))

    content_parts = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        for page_num in range(len(doc)):
            single = pymupdf.open()
            single.insert_pdf(doc, from_page=page_num, to_page=page_num)
            tmp_pdf = Path(tmp_dir) / f"page_{page_num + 1}.pdf"
            single.save(str(tmp_pdf))
            single.close()

            result = md.convert(str(tmp_pdf))
            content_parts.append(
                f"\n\n<!-- PAGE {page_num + 1} -->\n\n{result.text_content.strip()}"
            )

    doc.close()

    output_file = output_dir / f"{pdf_path.stem}_pages.md"
    output_file.write_text("".join(content_parts), encoding="utf-8")

    print(f"✓ 已提取（含頁碼）: {output_file}")
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
        try:
            page_images = page.get_images(full=True)
        except TypeError:
            page_images = page.get_images()

        for img_index, img in enumerate(page_images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
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
                        "file_size": len(image_bytes),
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

    print(f"\n📄 處理: {pdf_path.name}")
    print("-" * 50)

    # 使用 markitdown 提取
    extract_with_markitdown(pdf_path, output_dir)

    # 使用 pymupdf 提取（含頁碼）
    extract_with_pages(pdf_path, output_dir)

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
