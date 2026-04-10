# Optimized Translation Workflow Pattern

## Overview

The optimized translation pattern implements a linear chain with appropriate model routing to eliminate multi-loop review inefficiencies while maintaining translation quality.

## Pattern Mapping

| Phase | Model | Reasoning |
|-------|-------|-----------|
| **Translation** | sonnet | Requires deep language comprehension and cultural context |
| **Content Review** | sonnet | Needs semantic understanding and quality judgment |
| **Format Review** | haiku | Structure validation, markdown formatting, reference conversion |

## Linear Chain Benefits

### vs. Multi-Loop Review

**Traditional (Inefficient):**
```
Translate → Review → Revise → Review → Revise → Review → Format
```
Problems: Review fatigue, diminishing returns, context pollution

**Optimized (Linear):**
```
Translate (sonnet) → Content Review (sonnet) → Format Review (haiku) → Merge
```
Benefits: Clear separation of concerns, cost optimization, predictable workflow

## Fork Context Strategy

### Why Fork Each Phase

1. **Prevent Context Pollution:** Large translation content doesn't contaminate main conversation
2. **Model Specialization:** Each agent gets targeted instructions for their model capability
3. **Parallel Potential:** Future optimization could run phases concurrently
4. **Error Isolation:** Issues in one phase don't affect others

### Agent Instructions Template

**Translation Agent (sonnet):**
```
Focus: Semantic accuracy only
Input: Cleaned source + terminology
Output: Raw translation
Constraints: No formatting, no review
```

**Content Review Agent (sonnet):**
```
Focus: Quality and accuracy validation  
Input: Translation + source comparison
Output: Content corrections
Constraints: No formatting changes
```

**Format Review Agent (haiku):**
```
Focus: Structure and presentation
Input: Reviewed content + style guidelines
Output: Final formatted result
Constraints: No content changes
```

## Cost Analysis

**Traditional Approach:**
- Multiple sonnet calls for revision cycles
- Context accumulation across reviews
- Average: 3-5 review iterations

**Optimized Approach:**
- 2x sonnet (translation + content review)
- 1x haiku (format review)  
- Fixed iteration count

**Cost Reduction:** ~40% token savings on large documents

## Quality Assurance

### Built-in Quality Gates

1. **Terminology Validation** (Pre-translation)
2. **Semantic Review** (Post-translation)
3. **Format Validation** (Final phase)
4. **Progress Tracking** (Throughout)

### Failure Modes Prevented

- **Review Fatigue:** Fixed iteration count prevents diminishing returns
- **Context Loss:** Fork isolation maintains focus per phase
- **Cost Overrun:** Haiku handles structural tasks efficiently
- **Late Format Issues:** Immediate formatting prevents downstream problems