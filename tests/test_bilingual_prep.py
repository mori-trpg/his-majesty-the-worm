import sys
sys.path.insert(0, "scripts")
from bilingual_prep import merge_soft_linebreaks, build_bilingual_draft

def test_merge_soft_linebreaks_english():
    # English line break gets a space
    text = "line one\nline two"
    assert merge_soft_linebreaks(text) == "line one line two"

def test_merge_soft_linebreaks_chinese():
    # Chinese line break gets no space
    text = "第一行\n第二行"
    assert merge_soft_linebreaks(text) == "第一行第二行"

def test_merge_soft_linebreaks_preserves_paragraph():
    text = "para one\n\npara two"
    assert merge_soft_linebreaks(text) == "para one\n\npara two"

def test_build_bilingual_draft_plain_paragraph():
    source = "When a character attacks, they roll dice."
    result = build_bilingual_draft(source)
    assert "<!-- TODO: 翻譯 -->" in result
    assert "> When a character attacks, they roll dice." in result

def test_build_bilingual_draft_heading_no_placeholder():
    source = "## Combat\n\nSome rules here."
    result = build_bilingual_draft(source)
    # Heading should have no placeholder
    lines = result.splitlines()
    heading_idx = next(i for i, l in enumerate(lines) if l.startswith("## Combat"))
    assert lines[heading_idx - 1] != "<!-- TODO: 翻譯 -->" if heading_idx > 0 else True

def test_build_bilingual_draft_code_block_no_placeholder():
    source = "Text before.\n\n```\ncode here\n```\n\nText after."
    result = build_bilingual_draft(source)
    # Code block should not have placeholder prepended
    assert result.count("<!-- TODO: 翻譯 -->") == 2  # only text_before and text_after

def test_build_bilingual_draft_table_no_placeholder():
    source = "| A | B |\n|---|---|\n| 1 | 2 |"
    result = build_bilingual_draft(source)
    assert "<!-- TODO: 翻譯 -->" not in result
