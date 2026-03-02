# Quality Reviewer Prompt Template

Use this template when dispatching the quality reviewer subagent.

**Purpose:** Improve readability and format quality after source fidelity passes.

```text
Task tool (general-purpose):
  description: "Review quality for <TARGET_FILE>"
  prompt: |
    You are reviewing translation quality for one draft.

    ## Inputs

    - Target file: <TARGET_FILE>
    - Draft file: <DRAFT_FILE>
    - glossary.json
    - style-decisions.json

    ## Run Condition

    Run only if source reviewer already passed.

    ## Review Scope

    1. zh-TW readability and tone consistency
    2. Full-width punctuation correctness
    3. Heading/frontmatter integrity
    4. Component/table/dice format consistency
    5. Ambiguity that can cause rule misunderstanding

    ## Output JSON Only

    {
      "pass": true/false,
      "critical": [{ "type": "...", "location": "...", "detail": "..." }],
      "important": [{ "type": "...", "location": "...", "detail": "..." }],
      "minor": [{ "type": "...", "location": "...", "detail": "..." }]
    }
```
