# Change: Refactor docs to Ditaxis IA and fix MkDocs navigation

## Why

The current documentation structure mixes tutorials, recipes, reference, and architecture content, and the MkDocs navigation can drift out of sync with the docs tree. This reduces trust and makes it harder for users to find the right type of documentation.

## What Changes

- Restructure the documentation under `docs/` to follow the Ditaxis model:
  - `docs/tutorials/`
  - `docs/how-to/`
  - `docs/reference/` (including `docs/reference/api/`)
  - `docs/explanation/`
- Update `docs/mkdocs.yml` to:
  - Ensure `nav:` matches the on-disk docs tree (no missing files)
  - Set the repo metadata to `https://github.com/legout/sitq`
  - Remove the `git-committers` plugin (per project decision)

## Impact

- Affected specs:
  - `documentation-system`
- Affected files:
  - `docs/mkdocs.yml`
  - `docs/**` (directory layout and navigation targets)
- **BREAKING**: None (documentation-only)
