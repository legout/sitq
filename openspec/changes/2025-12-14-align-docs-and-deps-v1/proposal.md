# Change: Align Docs and Dependencies to v1 Scope

## Why

The repository documentation (README and MkDocs pages) still describes legacy features (multiple backends, multiple worker types, JSON serializer, retries, etc.) that are not implemented in the v1 code under `src/sitq/`. The default dependency set in `pyproject.toml` also includes packages for deferred backends and features, increasing install time and maintenance surface area.

This mismatch slows onboarding and creates confusion when users try to follow examples that cannot run.

## What Changes

- Update user-facing documentation to reflect the actual v1 public API and feature set.
- Ensure at least one end-to-end example is runnable and matches the documented API.
- Reduce default runtime dependencies to what v1 requires; move deferred backend dependencies to optional extras or development-only groups.

## Impact

- Affected specs:
  - `documentation-system`
  - `documentation-examples`
- Affected files (expected):
  - `README.md`
  - `docs/**`
  - `pyproject.toml`
- **BREAKING**:
  - Potentially for packaging: removing unused default dependencies may affect users relying on “future” backends via transitive installs. This is acceptable for v1 scope if clearly documented (and optional extras are provided where appropriate).

## Notes / Risks

- Documentation changes should follow the v1 PRD/SPEC (`plan/PRD_v1.md`, `plan/SPEC_v1.md`) and the OpenSpec v1 capability specs.
- If optional extras are introduced, docs must clearly show how to install them.

