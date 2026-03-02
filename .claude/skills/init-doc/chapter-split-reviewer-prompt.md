# Chapter Split Reviewer Prompt Template

Use this template when dispatching the chapter split reviewer subagent.

**Purpose:** Decide whether chapter splitting is needed and return a deterministic `chapters.json` payload.

```text
Task tool (general-purpose):
  description: "Plan chapter split for <SOURCE_PAGES_FILE>"
  prompt: |
    You are reviewing one extracted markdown source and deciding chapter split strategy.

    ## Inputs

    - Source pages file: <SOURCE_PAGES_FILE>
    - Expected config output path: <OUTPUT_CONFIG_PATH>
    - style-decisions.json (document_format, proper_nouns)

    ## Core Rules

    - Do not ask the user whether to split.
    - Decide split strategy from source structure and readability only.
    - Preserve full page coverage with no overlap and no gaps.
    - Keep chapter/file slugs in lowercase kebab-case ASCII.
    - Build config compatible with scripts/split_chapters.py.
    - If split is not needed, return one section with one `index` file covering full page range.

    ## Split Heuristics

    1. Prefer splitting when there are clear chapter/part boundaries.
    2. Keep related mechanics in the same file when splitting would break comprehension.
    3. Avoid tiny files with weak standalone value.
    4. Preserve source ordering exactly.

    ## Output JSON Only

    {
      "should_split": true/false,
      "reason": "...",
      "chapters_config": {
        "source": "<SOURCE_PAGES_FILE>",
        "output_dir": "docs/src/content/docs",
        "chapters": {
          "section-slug": {
            "title": "...",
            "order": 1,
            "files": {
              "index": {
                "title": "...",
                "description": "...",
                "pages": [1, 10],
                "order": 0
              }
            }
          }
        }
      },
      "warnings": ["..."]
    }

    Pass condition:
    - `chapters_config` is directly writable to `chapters.json`.
    - All pages in source are covered exactly once.
```
