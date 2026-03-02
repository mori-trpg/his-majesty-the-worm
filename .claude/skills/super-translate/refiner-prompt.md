# Refiner Prompt Template

Use this template when dispatching the refiner subagent.

**Purpose:** Apply reviewer findings to the draft while preserving correct content.

```text
Task tool (general-purpose):
  description: "Refine draft for <TARGET_FILE>"
  prompt: |
    You are refining a translated markdown draft using reviewer findings.

    ## Inputs

    - Source file: <TARGET_FILE>
    - Draft file: <DRAFT_FILE>
    - Reviewer findings JSON: <REVIEW_JSON>
    - glossary.json
    - style-decisions.json

    ## Rules

    - Fix all critical findings first.
    - Preserve already-correct content.
    - Keep markdown structure intact.
    - Do not introduce new term variants unless approved.
    - If required term is missing in glossary, flag it in unresolved issues.

    ## Output JSON Only

    {
      "draft_path": "<DRAFT_FILE>",
      "changes": [{ "location": "...", "summary": "..." }],
      "unresolved": [{ "type": "...", "detail": "..." }]
    }
```
