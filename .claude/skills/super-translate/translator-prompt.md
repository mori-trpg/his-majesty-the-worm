# Translator Prompt Template

Use this template when dispatching the translator subagent for one target file.

**Purpose:** Produce a draft translation without overwriting the source file.

**Note:** All context is inlined by the orchestrator. Do not read any files yourself.

```text
Task tool (general-purpose):
  description: "Translate draft for <TARGET_FILE>"
  prompt: |
    You are translating one markdown file from English to Traditional Chinese (zh-TW).

    ## Source File

    Path: <TARGET_FILE>

    ```markdown
    <SOURCE_CONTENT>
    ```

    ## Glossary

    ```json
    <GLOSSARY_CONTENT>
    ```

    ## Style Decisions

    ```json
    <STYLE_CONTENT>
    ```

    ## Hard Constraints

    - Traditional Chinese only (Taiwan usage), no Simplified Chinese.
    - Preserve markdown structure exactly (frontmatter, headings, lists, tables, links, code blocks).
    - Treat `frontmatter.title` as the page title. Do not restate it anywhere in the body as a heading of any level (`#`, `##`, etc.).
    - If the page opens with an overview/introduction block that has no heading in the source, translate it as plain body content. Do not invent a `#` heading or `## 概覽`.
    - Preserve image links exactly. If an image link is part of a paragraph's source flow, keep the exact markdown link but reposition it near the middle of the translated paragraph; do not split that paragraph into separate blocks before and after the image.
    - Preserve mechanics meaning; no rule drift.
    - Use glossary mappings exactly.
    - Manual translation only (no script-generated prose).
    - Write output to <DRAFT_FILE> only. Do not modify <TARGET_FILE>.

    ## Unknown Terms

    If a term is missing from the glossary, do not guess. Record it in "uncertain_terms".

    ## Required Output (JSON)

    {
      "draft_path": "<DRAFT_FILE>",
      "uncertain_terms": [
        { "term": "...", "context": "..." }
      ],
      "risk_notes": ["..."]
    }
```
