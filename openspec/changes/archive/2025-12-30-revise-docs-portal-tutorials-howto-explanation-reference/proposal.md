# Change: Revise docs portal, tutorials, how-to, explanation, and reference

## Why

The docs landing page and several existing doc pages reference outdated or unimplemented APIs and concepts. This undermines onboarding and makes it difficult to learn sitq from documentation.

## What Changes

- Rewrite `docs/index.md` as a Ditaxis portal page that links to:
  - Tutorials (learning-oriented)
  - How-to guides (goal-oriented)
  - Reference (mkdocstrings API reference)
  - Explanation (architecture and rationale)
  - Runnable scripts under `examples/basic/`
- Ensure `docs/installation.md` matches `pyproject.toml` requirements (Python `>=3.13`) and supported install modes.
- Create/replace:
  - Tutorials, including a rewritten interactive notebook under `docs/tutorials/interactive-tutorial.ipynb`
  - How-to guides for common operational tasks
  - Explanation pages for architecture, serialization, and limitations
  - Mkdocstrings stubs under `docs/reference/api/` for the public API surface

## Impact

- Affected specs:
  - `documentation-system`
- Affected files:
  - `docs/index.md`, `docs/installation.md`
  - `docs/tutorials/**`, `docs/how-to/**`, `docs/explanation/**`, `docs/reference/**`
- **BREAKING**: None (documentation-only)
