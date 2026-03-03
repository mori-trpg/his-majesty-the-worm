# Reviewer Prompt Template

Use this template when dispatching the reviewer subagent.

**Purpose:** Verify source fidelity and translation quality in a single pass.

```text
Task tool (general-purpose):
  description: "Review translation for <TARGET_FILE>"
  prompt: |
    You are reviewing a translated markdown draft.

    ## Inputs

    - Source file: <TARGET_FILE>
    - Draft file: <DRAFT_FILE>
    - glossary.json
    - style-decisions.json

    ## Core Rule

    Verify the draft directly against source. Do not trust prior reports.

    ## Review Scope

    Source fidelity:
    1. Missing or truncated content
    2. Meaning drift in mechanics/rules
    3. Glossary violations and forbidden variants

    Quality:
    4. zh-TW readability and tone
    5. Full-width punctuation correctness
    6. Heading/frontmatter/table/dice format integrity

    ## Output JSON Only

    {
      "pass": true/false,
      "critical": [{ "type": "...", "location": "...", "detail": "..." }],
      "important": [{ "type": "...", "location": "...", "detail": "..." }]
    }

    Pass condition: critical must be empty.
    Only flag issues that genuinely affect accuracy or readability.
    Do not nitpick minor stylistic preferences.
```
