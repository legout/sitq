# Change: Test Suite Organization (Unit/Integration vs Benchmarks)

## Why

The repository currently mixes a large number of test and benchmark scripts at the project root, and some long-running benchmark-like tests execute under the default pytest run. This makes CI/local validation slower and less reliable, and it obscures which checks are intended to be run as part of the fast feedback loop.

This change scopes to developer ergonomics and reliability: reorganize tests into a conventional layout and ensure benchmarks are opt-in.

## What Changes

- Move tests into a standard `tests/` layout (e.g. `tests/unit/`, `tests/integration/`, `tests/performance/`).
- Ensure benchmark/performance tests are excluded from the default pytest run (e.g. via markers or naming conventions) while remaining runnable explicitly.
- Add minimal pytest configuration to document and enforce the above behavior.

## Impact

- Affected specs:
  - `testing-system` (new capability)
- Affected files (expected):
  - test files currently at repo root
  - pytest configuration (e.g. `pyproject.toml` tool config or `pytest.ini`)
- **BREAKING**: None (developer workflow change only).

