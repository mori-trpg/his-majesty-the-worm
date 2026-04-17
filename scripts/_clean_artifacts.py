"""Remove PDF extraction artifacts from translated docs."""
import re, os

TARGET_DIRS = [
    'docs/src/content/docs/front-matter',
    'docs/src/content/docs/basics',
    'docs/src/content/docs/adventurer',
    'docs/src/content/docs/guild',
    'docs/src/content/docs/kith-and-kin',
    'docs/src/content/docs/four-paths',
    'docs/src/content/docs/crawl-phase',
    'docs/src/content/docs/challenge-phase',
    'docs/src/content/docs/camp-phase',
]

# Lines to delete (exact match after strip)
def is_artifact(stripped):
    # Bare page numbers: 1-4 digits possibly doubled (3434, 5252, etc.)
    if re.fullmatch(r'\d{1,4}', stripped):
        return True
    # Doubled page numbers like 3434, 5252, 1010
    m = re.fullmatch(r'(\d{2,3})\1', stripped)
    if m:
        return True
    # English chapter/appendix headers
    if re.fullmatch(r'CHAPTER \d+\s*\|.*', stripped):
        return True
    if re.fullmatch(r'APPENDIX [A-Z]\s*\|.*', stripped):
        return True
    # Chinese chapter headers
    if re.fullmatch(r'第[一二三四五六七八九十\d]+章\s*[│|].+', stripped):
        return True
    # Bare "CHAPTER N" alone
    if re.fullmatch(r'CHAPTER \d+', stripped):
        return True
    # Bare "APPENDIX X" alone
    if re.fullmatch(r'APPENDIX [A-Z]', stripped):
        return True
    return False


def clean_file(fpath):
    with open(fpath, encoding='utf-8') as f:
        lines = f.readlines()

    fm_count = 0
    new_lines = []
    removed = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip('\n').strip()

        # Track frontmatter
        if stripped == '---':
            fm_count += 1
        if fm_count < 2:
            new_lines.append(line)
            i += 1
            continue

        if is_artifact(stripped):
            removed += 1
            # Also swallow surrounding blank lines to avoid double-blanks
            # Skip this line; the surrounding blank-line collapsing happens below
        else:
            new_lines.append(line)
        i += 1

    # Collapse multiple consecutive blank lines into one
    collapsed = []
    prev_blank = False
    for line in new_lines:
        is_blank = line.strip() == ''
        if is_blank and prev_blank:
            continue
        collapsed.append(line)
        prev_blank = is_blank

    if removed:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.writelines(collapsed)

    return removed


def main():
    total = 0
    for d in TARGET_DIRS:
        for root, _, files in os.walk(d):
            for fname in sorted(files):
                if not (fname.endswith('.md') or fname.endswith('.mdx')):
                    continue
                fpath = os.path.join(root, fname)
                n = clean_file(fpath)
                if n:
                    rel = os.path.relpath(fpath, 'docs/src/content/docs')
                    print(f'  {rel}: removed {n} artifact lines')
                    total += n
    print(f'\n總計移除 {total} 行 PDF 殘留物')


if __name__ == '__main__':
    main()
