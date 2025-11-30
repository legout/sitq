# Change: Define public API surface for sitq v1

## Why
`PRD_v1.md` and `SPEC_v1.md` describe a small, explicit public API surface (`TaskQueue`, `SyncTaskQueue`, `Worker`, and the `Result` model), but the project does not yet have a formal capability describing which symbols are exported from the top-level `sitq` package. Making this explicit helps keep the v1 API small and intentional.

## What Changes
- Introduce a `public-api-core` capability that defines which core types are exported from the `sitq` package namespace.
- Specify that internal modules (backends, serialization, etc.) remain implementation details and are not part of the stable top-level API for v1.

## Impact
- Affected specs: `public-api-core`
- Affected code: `src/sitq/__init__.py`, documentation in `README.md`

