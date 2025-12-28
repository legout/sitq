# Change: Stabilize v1 Core (Importability + API Semantics)

## Why

The current v1 code under `src/sitq/` contains structural issues that can prevent importing the public API from source (e.g. mis-indented methods and misplaced initialization code). Additionally, a few behaviors diverge from the v1 specs (notably `get_result` timeout semantics and exception consistency), which makes the library hard to use and difficult to validate with tests and examples.

This change focuses on restoring **spec compliance** and **importability** without adding new capabilities.

## What Changes

- Restore importability of the v1 public API (`sitq.TaskQueue`, `sitq.Worker`, `sitq.SyncTaskQueue`) when importing from source.
- Clarify and enforce v1 semantics:
  - `TaskQueue.get_result(..., timeout=...)` returns `None` on timeout (and does not surface a domain timeout exception to callers).
  - `SyncTaskQueue` delegates to async `TaskQueue` while raising domain-specific sitq exceptions (not generic `RuntimeError`) for operational failures.
- Remove repository hygiene hazards that mask broken source code (tracked `__pycache__` / `.pyc` artifacts).
- Fix validation implementation mismatches that currently cause runtime failures (e.g. missing validation builder methods used by v1 components, and missing `.validate()` calls).

## Impact

- Affected specs:
  - `task-queue-core`
  - `sync-task-queue`
  - `serialization-core`
  - `improve-error-handling`
- Affected code (expected):
  - `src/sitq/queue.py`
  - `src/sitq/sync.py`
  - `src/sitq/serialization.py`
  - `src/sitq/exceptions.py`
  - `.gitignore` and removal of tracked bytecode under `src/sitq/**/__pycache__/`
- **BREAKING**: No intended user-facing API break; changes are bugfixes/clarifications to align behavior with existing v1 specs.

## Notes / Risks

- Some existing tests and docs assume legacy APIs; this change only targets v1 behavior as described in the current OpenSpec specs and `plan/PRD_v1.md`.
- If callers were relying on a raised timeout exception from `get_result`, behavior will change to the documented `None` return; this is treated as restoring intended behavior.
