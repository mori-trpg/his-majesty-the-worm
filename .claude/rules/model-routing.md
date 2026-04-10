---
paths:
  - ".claude/skills/**/*.md"
---

# Model Selection Principles

## Language Comprehension Tasks

- MUST use sonnet model for translation work
- MUST use sonnet model for content quality assessment
- MUST use sonnet model for terminology and glossary analysis
- MUST use sonnet model for cultural adaptation decisions

## Structure and Format Tasks

- MUST use haiku model for markdown syntax validation
- MUST use haiku model for file organization and navigation
- MUST use haiku model for frontmatter format checking
- MUST use haiku model for link and path verification

## Cost Optimization

- NEVER use sonnet for simple structural validation
- NEVER use haiku for language comprehension or translation
- MUST choose model based on cognitive complexity required
- MUST prioritize cost efficiency for repetitive validation tasks

## Model Assignment

- MUST specify explicit model choice in subagent frontmatter
- NEVER rely on default model inheritance
- MUST match model capability to task requirements