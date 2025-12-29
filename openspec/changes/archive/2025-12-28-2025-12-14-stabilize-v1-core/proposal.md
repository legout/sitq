# Change: Stabilize v1 Core (Importability + API Semantics)

## Why

The current v1 code under `src/sitq/` contains structural issues that can prevent importing of public API from source (e.g. mis-indented methods and misplaced initialization code). Additionally, a few behaviors diverge from v1 specs (notably `get_result` timeout semantics and exception consistency), which makes the library hard to use and difficult to validate with tests and examples.

This change focuses on restoring **spec compliance** and **importability** without adding new capabilities.

## What Changes

- Restore importability of v1 public API (`sitq.TaskQueue`, `sitq.Worker`, `sitq.SyncTaskQueue`) when importing from source.
- Clarify and enforce v1 semantics:
   - `TaskQueue.get_result(..., timeout=...)` returns `None` on timeout (and does not surface a domain timeout exception to callers).
   - `SyncTaskQueue` delegates to async `TaskQueue` while raising domain-specific sitq exceptions (not generic `RuntimeError`) for operational failures.
- Remove repository hygiene hazards that mask broken source code (tracked `__pycache__` / `.pyc` artifacts).
- Fix validation implementation mismatches that currently cause runtime failures (e.g. missing validation builder methods used by v1 components, and missing `.validate()` calls).
- **NEW**: Fix SQLite backend schema compliance (add missing `error` column).
- **NEW**: Add automatic schema migration for SQLite backend.
- **NEW**: Replace debug `print()` statements with loguru logger throughout codebase.
- **NEW**: Fix `SyncTaskQueue` event loop detection to properly reject async contexts.

## Impact

- Affected specs:
   - `task-queue-core`
   - `sync-task-queue`
   - `backend-sqlite`
   - `serialization-core`
   - `improve-error-handling`
- Affected code:
   - `src/sitq/queue.py` (timeout semantics)
   - `src/sitq/sync.py` (event loop detection)
   - `src/sitq/backends/sqlite.py` (schema, migration, logging)
   - `src/sitq/validation.py` (retry logging)
   - `.gitignore` (already correct)
   - `src/sitq/serialization.py` (for completeness)
   - `src/sitq/exceptions.py` (for completeness)
- **BREAKING**: None intended; all changes are bugfixes/clarifications to align behavior with existing v1 specs.

## Notes / Risks

- Some existing tests and docs assume legacy APIs; this change only targets v1 behavior as described in current OpenSpec specs and `plan/PRD_v1.md`.
- If callers were relying on a raised timeout exception from `get_result`, behavior will change to documented `None` return; this is treated as restoring intended behavior.
- **NEW**: SQLite schema migration is automatic and idempotent; handles both new and existing databases.
- **NEW**: `timeout=0` now returns immediately instead of waiting forever; callers may need adjustment.
- **NEW**: `SyncTaskQueue` now properly rejects async contexts with `RuntimeError`; previously allowed incorrect usage.
