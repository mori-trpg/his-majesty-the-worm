---
paths:
  - "docs/src/content/docs/**/*.{md,mdx}"
---

# Documentation Conventions

## Traditional Chinese Requirements

- MUST use Traditional Chinese (繁體中文) exclusively, never Simplified Chinese
- MUST use full-width punctuation：，。、；：「」『』（）
- MUST use half-width for numbers, English, and code
- MUST use `……` for ellipsis, never `...`

## Frontmatter Structure

- MUST include Traditional Chinese `title` and `description`
- MUST include `sidebar: order:` for navigation positioning
- NEVER skip frontmatter structure

## Markdown Formatting

- MUST reserve H1 for title (from frontmatter)
- MUST use H2 for main sections, H3 for subsections
- NEVER skip heading levels (H2 → H4)
- MUST use absolute paths from docs root for internal links: `/rules/combat/`
- MUST store images in `docs/src/assets/` with relative paths: `../../assets/image-name.jpg`
- MUST provide descriptive alt text for all images

## Starlight Components

- MUST use `:::note[標題]`, `:::tip`, `:::caution`, `:::danger` for asides
- MUST import cards from `@astrojs/starlight/components`

## Translation Style

- MUST check `glossary.json` first for proper nouns
- MUST use Arabic numerals for dice (2d6), stats, page refs
- MUST use Chinese numerals in prose: 一個、兩次、三種
- MUST maintain consistency for mechanics terms across documents
- MUST preserve original notation: +1, -2, 1d6+3

## Dice Tables

- MUST use Markdown tables with clear roll ranges (1-2, 3-4, 5-6)
- MUST use standard notation: `1d6`, `1d20`, `2d6`
- NEVER create gaps or overlaps in roll ranges