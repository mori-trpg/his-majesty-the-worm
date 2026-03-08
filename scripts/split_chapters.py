#!/usr/bin/env python3
"""
章節拆分工具
根據設定檔將 Markdown 內容拆分成多個章節檔案

使用方式：
    # 產生範例設定檔
    python scripts/split_chapters.py --init

    # 根據設定檔拆分章節
    python scripts/split_chapters.py

    # 指定設定檔
    python scripts/split_chapters.py --config my_chapters.json

設定檔格式 (chapters.json)：
{
    "source": "data/markdown/rulebook_pages.md",
    "output_dir": "docs/src/content/docs",
    "chapters": {
        "rules": {
            "title": "核心規則",
            "files": {
                "index": {
                    "title": "規則總覽",
                    "description": "遊戲規則概述",
                    "pages": [1, 10]
                },
                "combat": {
                    "title": "戰鬥系統",
                    "description": "戰鬥規則說明",
                    "pages": [11, 30]
                }
            }
        }
    }
}
"""

import json
import os
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path


def load_config(config_path: Path) -> dict:
    """載入設定檔"""
    return json.loads(config_path.read_text(encoding="utf-8"))


def save_config(config: dict, config_path: Path):
    """儲存設定檔"""
    config_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def create_example_config(config_path: Path):
    """建立範例設定檔"""
    example = {
        "source": "data/markdown/your_pdf_pages.md",
        "output_dir": "docs/src/content/docs",
        "clean_patterns": [
            r"\(Order #\d+\)",          # 移除訂單號
            r"Page \d+ of \d+",         # 移除頁碼標記
        ],
        "images": {
            "enabled": True,
            "assets_dir": "docs/src/assets/extracted",
            "repeat_file_size_threshold": 5,
        },
        "chapters": {
            "rules": {
                "title": "核心規則",
                "order": 1,
                "files": {
                    "index": {
                        "title": "規則總覽",
                        "description": "遊戲規則的基本概述",
                        "pages": [1, 10],
                        "order": 0
                    },
                    "basic-moves": {
                        "title": "基本動作",
                        "description": "角色可執行的基本動作",
                        "pages": [11, 20],
                        "order": 1
                    }
                }
            },
            "characters": {
                "title": "角色",
                "order": 2,
                "files": {
                    "index": {
                        "title": "角色創建",
                        "description": "如何創建角色",
                        "pages": [21, 40],
                        "order": 0
                    }
                }
            }
        }
    }
    save_config(example, config_path)
    print(f"✓ 已建立範例設定檔: {config_path}")
    print("\n請編輯設定檔，設定：")
    print("  - source: 來源 Markdown 檔案（使用 _pages.md 版本）")
    print("  - chapters: 章節結構與頁碼範圍")


def extract_pages(content: str) -> dict[int, str]:
    """從含頁碼標記的內容提取各頁"""
    pages = {}
    pattern = r"<!-- PAGE (\d+) -->\n\n(.*?)(?=<!-- PAGE \d+ -->|$)"

    for match in re.finditer(pattern, content, re.DOTALL):
        page_num = int(match.group(1))
        page_content = match.group(2).strip()
        pages[page_num] = page_content

    return pages


def get_page_range(pages: dict[int, str], start: int, end: int) -> str:
    """取得指定頁碼範圍的內容"""
    parts = []
    for page_num in range(start, end + 1):
        if page_num in pages:
            parts.append(pages[page_num])
    return "\n\n".join(parts)


def clean_content(text: str, patterns: list[str]) -> str:
    """清理內容"""
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    # 移除多餘空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def generate_frontmatter(title: str, description: str = "", order: int | None = None) -> str:
    """生成 Starlight frontmatter"""
    lines = [
        "---",
        f"title: {title}",
    ]
    if description:
        lines.append(f"description: {description}")
    if order is not None:
        lines.append("sidebar:")
        lines.append(f"  order: {order}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def infer_source_stem(source_path: Path) -> str:
    """從 _pages.md 來源檔推回 PDF stem。"""
    stem = source_path.stem
    if stem.endswith("_pages"):
        return stem[:-6]
    return stem


def load_image_manifest(config: dict, project_root: Path) -> tuple[list[dict], Path | None, int]:
    """載入圖片 manifest 與設定。"""
    image_config = config.get("images", {})
    if image_config.get("enabled", True) is False:
        return [], None, image_config.get("repeat_file_size_threshold", image_config.get("repeat_size_threshold", 5))

    source_path = Path(config["source"])
    default_manifest = (
        project_root
        / "data"
        / "markdown"
        / "images"
        / infer_source_stem(source_path)
        / "manifest.json"
    )
    manifest_path = project_root / image_config["manifest"] if "manifest" in image_config else default_manifest

    if not manifest_path.exists():
        return [], None, image_config.get("repeat_file_size_threshold", image_config.get("repeat_size_threshold", 5))

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return (
        payload.get("images", []),
        manifest_path,
        image_config.get("repeat_file_size_threshold", image_config.get("repeat_size_threshold", 5)),
    )


def image_file_size_key(image: dict) -> int | None:
    """為圖片建立檔案大小去重 key。"""
    file_size = image.get("file_size")
    if file_size is None:
        return None
    return int(file_size)


def group_images_by_page(images: list[dict], repeat_file_size_threshold: int) -> tuple[dict[int, list[dict]], int]:
    """依頁碼整理圖片，並略過高重複檔案大小圖片。"""
    size_counts = Counter(
        size_key
        for image in images
        if (size_key := image_file_size_key(image)) is not None
    )

    page_images: dict[int, list[dict]] = defaultdict(list)
    skipped = 0
    for image in images:
        size_key = image_file_size_key(image)
        if (
            repeat_file_size_threshold > 0
            and size_key is not None
            and size_counts[size_key] >= repeat_file_size_threshold
        ):
            skipped += 1
            continue

        page = int(image["page"])
        page_images[page].append(image)

    for images_on_page in page_images.values():
        images_on_page.sort(
            key=lambda image: (
                float(image["y"]) if image.get("y") is not None else float("inf"),
                float(image["x"]) if image.get("x") is not None else float("inf"),
                image["filename"],
            )
        )

    return dict(page_images), skipped


def resolve_assets_dir(config: dict, project_root: Path) -> Path:
    """決定輸出圖片資產目錄。"""
    output_dir = project_root / config["output_dir"]
    image_config = config.get("images", {})
    assets_dir = image_config.get("assets_dir")
    if assets_dir:
        return project_root / assets_dir
    return output_dir.parents[1] / "assets"


def copy_image_to_assets(
    image: dict,
    project_root: Path,
    assets_dir: Path,
    source_slug: str,
) -> Path:
    """將圖片複製到 docs assets。"""
    source_image_path = project_root / "data" / "markdown" / image["path"]
    target_path = assets_dir / source_slug / image["filename"]
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_image_path, target_path)
    return target_path


def build_image_markdown(image: dict, target_path: Path, markdown_path: Path) -> str:
    """生成 Markdown 圖片引入。"""
    relative_path = Path(os.path.relpath(target_path, markdown_path.parent)).as_posix()
    alt_text = f"第 {image['page']} 頁插圖"
    return f"![{alt_text}]({relative_path})"


def build_section_content(
    pages: dict[int, str],
    start: int,
    end: int,
    clean_patterns: list[str],
    page_images: dict[int, list[dict]],
    output_path: Path,
    project_root: Path,
    assets_dir: Path,
    source_slug: str,
) -> tuple[str, int]:
    """組合章節內容與對應圖片。"""
    parts = []
    copied_count = 0

    for page_num in range(start, end + 1):
        if page_num not in pages:
            continue

        page_content = clean_content(pages[page_num], clean_patterns)
        images = page_images.get(page_num, [])
        image_lines = []
        for image in images:
            target_path = copy_image_to_assets(image, project_root, assets_dir, source_slug)
            image_lines.append(build_image_markdown(image, target_path, output_path))
            copied_count += 1

        block_parts = [part for part in [page_content, "\n\n".join(image_lines)] if part]
        if block_parts:
            parts.append("\n\n".join(block_parts))

    return "\n\n".join(parts).strip(), copied_count


def split_chapters(config: dict, project_root: Path):
    """根據設定拆分章節"""
    source_path = project_root / config["source"]
    output_dir = project_root / config["output_dir"]
    clean_patterns = config.get("clean_patterns", [])
    manifest_images, manifest_path, repeat_file_size_threshold = load_image_manifest(config, project_root)
    page_images, skipped_images = group_images_by_page(manifest_images, repeat_file_size_threshold)
    assets_dir = resolve_assets_dir(config, project_root)
    source_slug = infer_source_stem(Path(config["source"]))

    if not source_path.exists():
        print(f"❌ 找不到來源檔案: {source_path}")
        print("   請先執行 extract_pdf.py 提取 PDF")
        sys.exit(1)

    print(f"📖 來源檔案: {source_path}")
    content = source_path.read_text(encoding="utf-8")
    pages = extract_pages(content)
    print(f"   共 {len(pages)} 頁")
    if manifest_path is not None:
        print(f"🖼️  圖片 manifest: {manifest_path}")
        print(f"   可用圖片 {len(manifest_images)} 張，略過高重複檔案大小 {skipped_images} 張")
    print("-" * 50)

    total_files = 0
    total_images = 0
    for section_name, section_config in config["chapters"].items():
        section_dir = output_dir / section_name
        section_dir.mkdir(parents=True, exist_ok=True)

        section_title = section_config.get("title", section_name)
        print(f"\n📁 {section_title} ({section_name}/)")

        for filename, file_config in section_config["files"].items():
            title = file_config["title"]
            description = file_config.get("description", "")
            page_range = file_config["pages"]
            order = file_config.get("order")

            start_page, end_page = page_range
            output_path = section_dir / f"{filename}.md"
            section_content, image_count = build_section_content(
                pages,
                start_page,
                end_page,
                clean_patterns,
                page_images,
                output_path,
                project_root,
                assets_dir,
                source_slug,
            )

            frontmatter = generate_frontmatter(title, description, order)
            full_content = frontmatter + "\n" + section_content
            output_path.write_text(full_content, encoding="utf-8")

            char_count = len(section_content)
            image_note = f", {image_count} 張圖" if image_count else ""
            print(
                f"   ✓ {filename}.md - {title} "
                f"(p.{start_page}-{end_page}, {char_count:,} 字{image_note})"
            )
            total_files += 1
            total_images += image_count

    print("-" * 50)
    print(f"✅ 完成！共產生 {total_files} 個檔案，插入 {total_images} 張圖片")


def main():
    project_root = Path(__file__).parent.parent
    default_config = project_root / "chapters.json"

    # 處理命令列參數
    if "--init" in sys.argv:
        create_example_config(default_config)
        return

    config_path = default_config
    if "--config" in sys.argv:
        idx = sys.argv.index("--config")
        if idx + 1 < len(sys.argv):
            config_path = Path(sys.argv[idx + 1])

    if not config_path.exists():
        print(f"❌ 找不到設定檔: {config_path}")
        print("   請先執行: python scripts/split_chapters.py --init")
        sys.exit(1)

    config = load_config(config_path)
    split_chapters(config, project_root)


if __name__ == "__main__":
    main()
