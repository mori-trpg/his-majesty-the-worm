---
name: translate
description: Start translation - translate a specified section or file
arguments:
  - name: target
    description: Translation target (file path / section name / all)
    required: false
---

# Translate Document

Use `pdf-translation` and `terminology-management` skills.

## Prerequisites

- `glossary.json` exists with key terms
- Files exist in `docs/src/content/docs/`
- Run `/init-doc` first if not done

## Process

### 0. Select Translation Mode

Read `style-decisions.json` and check `translation_mode.mode`:

**If mode is null (not set):**
- Use AskUserQuestion tool to ask user:
  - **Full Translation**: Translate all content completely, preserving the original structure and details
  - **Summary Translation**: Provide a concise translation that extracts key rules and omits examples and lengthy explanations
- Update `style-decisions.json` with user's choice:
  - Set `translation_mode.mode` to `"full"` or `"summary"`
  - Set `translation_mode.reason` to user's reason (if provided)

**If mode is already set:**
- Show current mode setting
- Ask if user wants to change (optional)

### 1. Select Target

If no `$ARGUMENTS`:
- List available files in `docs/src/content/docs/`
- Ask user which to translate

Scope options:
- Single file: `docs/src/content/docs/rules/basic.md`
- Section: `rules` (all files in section)
- All: `all`

### 2. Load Resources

Read:
- `glossary.json` - term mappings
- `style-decisions.json` - style choices

### 3. Translate Content

For each target file:

1. **Read source** - Load current content
2. **Identify segments** - Paragraphs, lists, tables
3. **Apply glossary** - Use consistent terminology
4. **Translate** - Convert to natural English
5. **Preserve structure** - Keep frontmatter, markdown syntax

### Translation Rules

| Element | Handling |
|---------|----------|
| Frontmatter | Translate `title`, `description`; keep `sidebar` structure |
| Headings | Translate, maintain hierarchy |
| Lists | Preserve formatting, translate content |
| Tables | Keep structure, translate cells |
| Code blocks | Keep unchanged |
| Bold/Italic | Preserve markers |
| Links | Translate text, keep URLs |
| Game terms | Apply glossary strictly |

### Mode-Specific Rules

**Full Translation Mode (`full`):**
- Translate all paragraphs, including examples and explanations
- Preserve the original structure without omission
- Suitable for rulebooks requiring complete reference

**Summary Translation Mode (`summary`):**
- Extract core rules and mechanisms
- Omit lengthy examples and replace with concise explanations
- Merge repeated concepts
- Use bullet points to organize key information
- Suitable for quick-reference rule summaries

### 4. New Terms

When encountering unknown terms:

1. Pause and report to user
2. Ask for translation
3. Add to `glossary.json`
4. Continue with new term

### 5. Write Output

Replace source file with translated version.

### 6. Progress Tracking

After each file:
- Report: `✓ translated: <path>`
- Show next file or completion

## Example Usage

```
/translate
/translate docs/src/content/docs/rules/basic.md
/translate rules
/translate all
```

## Output

Translated files in place, ready for `/check-consistency`.
