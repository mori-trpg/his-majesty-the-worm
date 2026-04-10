---
paths:
  - "scripts/**/*.py"
---

# Python Conventions

## Import Organization

- MUST include `from __future__ import annotations` as first import
- MUST group imports: standard library, third-party, local imports
- MUST use absolute imports for project modules
- MUST use `from pathlib import Path` instead of `os.path`

## Project Structure

- MUST use `PROJECT_ROOT = Path(__file__).resolve().parents[1]` pattern
- MUST define path constants using `PROJECT_ROOT` base
- NEVER hardcode file paths

## Error Handling

- MUST use specific exception types, never bare `except:`
- MUST provide descriptive error messages for user-facing failures
- MUST exit with appropriate codes: 0 success, 1 user error, 2 system error

## Documentation

- MUST include module docstring describing purpose
- MUST include type hints for function parameters and return values
- MUST use descriptive CLI argument help text

## Testing Standards

- MUST name test files `test_*.py` in `scripts/tests/`
- MUST use pytest fixtures defined in `conftest.py`
- MUST test both success and error cases
- NEVER skip testing for scripts that modify files

## Code Quality

- MUST use explicit variable names, avoid single letters except for loops
- MUST validate input arguments before processing
- MUST handle file operations with proper exception handling