# Translator Prompt Template

Use this template when dispatching the translator subagent for one target file.

**Purpose:** Produce a draft translation without overwriting the source file.

```text
Task tool (general-purpose):
  description: "Translate draft for <TARGET_FILE>"
  prompt: |
    You are translating one markdown file from English to Traditional Chinese (zh-TW).

    ## Inputs

    - Source file: <TARGET_FILE>
    - Draft output path: <DRAFT_FILE>
    - glossary.json
    - style-decisions.json (translation_mode, proper_nouns.mode, document_format)

    ## Hard Constraints

    - Traditional Chinese only (Taiwan usage), no Simplified Chinese.
    - Preserve markdown structure exactly (frontmatter, headings, lists, tables, links, code blocks).
    - Preserve mechanics meaning; no rule drift.
    - Use glossary mappings exactly.
    - Manual translation only (no script-generated prose).
    - Do not overwrite <TARGET_FILE>; write only to <DRAFT_FILE>.

    ## Unknown Terms

    If a term is missing from glossary, do not guess. Put it in "uncertain_terms".

    ## Required Output (JSON)

    {
      "draft_path": "<DRAFT_FILE>",
      "uncertain_terms": [
        { "term": "...", "context": "..." }
      ],
      "risk_notes": ["..."]
    }
```
