# Change: Remove obsolete documentation (no archive)

## Why

Several existing documentation pages are speculative or describe APIs and behaviors that are not implemented in the v1 codebase under `src/sitq/`. Keeping these pages causes confusion and makes it harder to trust the documentation.

## What Changes

- Remove obsolete/incorrect documentation after Ditaxis replacements exist.
- Keep MkDocs navigation free of dead links after removals.
- Do not archive deleted pages.

## Impact

- Affected specs:
  - `documentation-system`
- Affected files:
  - Various pages under `docs/` (notably legacy `docs/user-guide/**` and other outdated pages)
  - `docs/mkdocs.yml` (nav updates)
- **BREAKING**: None (documentation-only)
