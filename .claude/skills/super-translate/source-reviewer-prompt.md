# Source Reviewer Prompt Template

Use this template when dispatching the source-fidelity reviewer subagent.

**Purpose:** Verify source compliance before quality review.

```text
Task tool (general-purpose):
  description: "Review source fidelity for <TARGET_FILE>"
  prompt: |
    You are reviewing source fidelity for one translated draft.

    ## Inputs

    - Source file: <TARGET_FILE>
    - Draft file: <DRAFT_FILE>
    - glossary.json
    - style-decisions.json

    ## Core Rule

    Do not trust prior reports. Verify the draft directly against source.

    ## Review Scope

    1. Missing/truncated content
    2. Meaning drift in mechanics/rules
    3. Glossary violations and forbidden variants
    4. Translation mode compliance
    5. Structure/frontmatter regressions
    6. Simplified Chinese or incorrect punctuation style

    ## Output JSON Only

    {
      "pass": true/false,
      "critical": [{ "type": "...", "location": "...", "detail": "..." }],
      "important": [{ "type": "...", "location": "...", "detail": "..." }],
      "minor": [{ "type": "...", "location": "...", "detail": "..." }]
    }

    Pass condition: critical must be empty.
```
