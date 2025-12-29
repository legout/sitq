# Change: Update documentation validation tests for Ditaxis layout

## Why

The existing documentation validation tests assume a legacy docs structure and will drift as the documentation is reorganized. The test suite should enforce the new structure and catch stale references early.

## What Changes

- Update documentation validation tests to reflect the new Ditaxis file layout.
- Keep syntax checking for code blocks/snippets and basic cross-reference checks.
- Ensure the interactive notebook location is validated.

## Impact

- Affected specs:
  - `testing-system`
- Affected files:
  - `tests/validation/test_documentation.py` (and any helpers)
- **BREAKING**: None
